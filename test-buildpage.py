import os
import re

def getCodePositions(txt):

    escapeRegex = r"(\x3C\x25\x20)|(\x3C\x25\n)"
    echoRegex = r"(\x3C\x25\x3D\x20)"
    closeRegex = r"(\x20\x25\x3E)|(\n\x25\x3E)"
    optionsRegex = r"(\x3C\x25options\x20)|(\x3C\x25options\n)"
    
    _escPos = re.search(escapeRegex, txt)
    if _escPos:
        escPos = _escPos.start()
    else:
        escPos = 0
    _echoPos = re.search(echoRegex, txt)
    if _echoPos:
        echoPos = _echoPos.start()
    else:
        echoPos = 0
    _closePos = re.search(closeRegex, txt)
    if _closePos:
        closePos = _closePos.start()
    else:
        closePos = 0
    _optionsPos = re.search(optionsRegex, txt)
    if _optionsPos:
        optionsPos = _optionsPos.start()
    else:
        optionsPos = 0

    return {
        "escPos": escPos,
        "echoPos": echoPos,
        "closePos": closePos,
        "optionsPos": optionsPos}
        

def main():

    currDir = os.getcwd() + '/'
    sourceFile = currDir + 'test-pagefile.txt'
    # destFile = os.getcwd() + '/newfile.txt'
    sf = open(sourceFile, "r")
    txt = sf.read()
    sf.close()

    #Now text is in a variable
    # 1. Recursively include up to 100 files
    # 2. Build Procedure Header, Declaration & Begin
    # 3. Build Procedure Footer
    # 4. Build Procedure Body
    # 5. Replace '<%/' to '<%' and '/%>' to '%>'

    # do includes
    # hex for '<%include ' (space follows) & ' %>
    escapeRegex = r"(\x3C\x25\x20)|(\x3C\x25\n)"
    includeRegex = r"(\x3C\x25include\x20)"
    optionsRegex = r"(\x3C\x25options\x20)|(\x3C\x25options\n)"
    echoRegex = r"(\x3C\x25\x3D\x20)"
    closeRegex = r"(\x20\x25\x3E)|(\n\x25\x3E)"

    loopAgain = True
    hasChanged = False
    loopCount = 0
    while loopAgain:
        startPos = re.search(includeRegex, txt)
        if startPos:
            tmpTxt = txt[startPos.end():]
            endPos = re.search(closeRegex, tmpTxt)
            if endPos:
                hasChanged = True
                rawStr = tmpTxt[:endPos.end()]
                incFile = tmpTxt[:endPos.start()].strip()
                rStr = '<%include ' + rawStr
                incf = open(incFile, "r")
                incTxt = incf.read()
                incf.close()
                incTxt = incTxt.rstrip('\n')
                #print('will replace ' + rStr + ' with ' + incTxt)
                txt = txt.replace(rStr, incTxt)
            else:
                #we must report an error
                loopAgain = False
        else:
            loopAgain = False

        loopCount = loopCount + 1
        if loopAgain and loopCount > 100:
            loopAgain = False
            
        
    print('loopcount = ' + str(loopCount))
    
    # all includes resolved, now do other processing
    # remove comments that start with '#' and blank lines
    lineArray = txt.split('\n')
    txt = ''
    for txtLine in lineArray:
        if txtLine[:1] == '#':
            #ignore
            pass
        elif len(txtLine.strip()) == 0:
            #ignore
            pass
        else:
            txt = txt + txtLine + '\n'

    #print(txt)


    # do procedure heading
    agTxt = ''
    decTxtBlk = '  AS $___agBody___$ \n\nDECLARE\n  __agStrArray_ text[];\n  __i_ integer := 0;\n  __agRtn_ text;\n'
    begTxtBlk = 'BEGIN \n'
    arrBegBlk = '__agStrArray_[__i_] = $___agArray___$'
    arrEndBlk = '$___agArray___$; __i_ := __i_ + 1;\n'
    echoBegBlk = '$___agArray___$ || ( '
    echoEndBlk = ' ) || $___agArray___$'
    lineArray = txt.split('\n')
    lineContext = 'start'
    paramCount = 0

    escapeOpen = False
    echoOpen = False
    strOpen = False
    codeLines = 0
    codeTxt = ''
    returnTxt = "\n\n  __agRtn_ := array_to_string(__agStrArray_, '', '');\n  RETURN __agRtn_;\n"
    optionsTxt = "\nEND;\n$___agBody___$\nLANGUAGE 'plpgsql'\n&VOLATILITY \n&SECURITY \n&PARALLEL \n&COST"
    rawOptTxt = ''
    
    for txtLine in lineArray:
        if lineContext == 'start':
            txtLine = txtLine.strip()
            txtLine = txtLine.replace('  ', ' ')
            funcDef = txtLine.split(' ')
            agTxt = 'CREATE OR REPLACE FUNCTION ' + funcDef[0] + ' (\n'
            lineContext = 'params'
        elif lineContext == 'params':
            if txtLine.strip().lower() in ('declare', '<%appgoo %>', '<%code %>', '<%begin %>'):
                if len(funcDef) == 1:
                    agTxt = agTxt + ') RETURNS TEXT \n' + decTxtBlk
                else:
                    del funcDef[0]
                    agTxt = agTxt + ') ' + ' '.join(funcDef) + '\n' + decTxtBlk
                if txtLine.strip().lower() == 'declare':
                    lineContext = 'vars'
                else:
                    agTxt = agTxt + '\n' + begTxtBlk
                    lineContext = 'code'
            else:
                paramCount = paramCount + 1
                txtLine = txtLine.strip()
                if txtLine[:2] == '__':
                    # illegal parameter name, so don't allow it
                    pass
                else:
                    if paramCount > 1:
                        agTxt = agTxt + ', '
                    else:
                        agTxt = agTxt + '  '
                    txtLine = txtLine.replace('  ', ' ')
                    txtLine = txtLine.rstrip(',')
                    paramDef = txtLine.split(' ')                
                    if len(paramDef) == 1:
                        agTxt = agTxt + txtLine.strip() + ' text \n'
                    else:
                        agTxt = agTxt + txtLine.strip() + ' \n'
        elif lineContext == 'vars':
            if txtLine.strip().lower() in ('<%appgoo %>', '<%code %>', '<%begin %>'):
                agTxt = agTxt + '\n' + begTxtBlk
                lineContext = 'code'
            else:
                txtLine = txtLine.strip()
                if txtLine[:2] == '__':
                    # illegal variable name, so don't allow it
                    pass
                else:
                    txtLine = txtLine.replace('  ', ' ')
                    txtLine = txtLine.rstrip(',')
                    txtLine = txtLine.rstrip(';')
                    varDef = txtLine.split(' ')
                    if len(varDef) == 1:
                        agTxt = agTxt + '  ' + txtLine.strip() + ' text; \n'
                    else:
                        agTxt = agTxt + '  ' + txtLine.strip() + '; \n' 
        elif lineContext == 'code':
            #escapeOpen = False
            #echoOpen = False
            #strOpen = False
            #arrBegBlk = '__agStrArray_[__i_] = $___agArray___$'
            #arrEndBlk = '$___agArray___$; __i_ = __i_ + 1;\n'
            #echoBegBlk = '$___agArray___$ || ( '
            #echoEndBlk = ' ) || $___agArray___$'

##            _escPos = re.search(escapeRegex, txtLine)
##            if _escPos:
##                escPos = _escPos.start()
##            else:
##                escPos = 0
##            _echoPos = re.search(echoRegex, txtLine)
##            if _echoPos:
##                echoPos = _echoPos.start()
##            else:
##                echoPos = 0
##            _closePos = re.search(closeRegex, txtLine)
##            if _closePos:
##                closePos = _closePos.start()
##            else:
##                closePos = 0
##            _optionsPos = re.search(optionsRegex, txtLine)
##            if _optionsPos:
##                optionsPos = _optionsPos.start()
##            else:
##                optionsPos = 0
            #codePos = getCodePositions(txtLine)
##            if startPos:
##                tmpTxt = txt[startPos.end():]
##                endPos = re.search(closeRegex, tmpTxt)
##                if endPos:
##                    hasChanged = True
##                    rawStr = tmpTxt[:endPos.end()]
##                    incFile = tmpTxt[:endPos.start()].strip()
##                    rStr = '<%include ' + rawStr
##                    incf = open(incFile, "r")
##                    incTxt = incf.read()
##                    incf.close()
##                    incTxt = incTxt.rstrip('\n')
##                    #print('will replace ' + rStr + ' with ' + incTxt)
##                    txt = txt.replace(rStr, incTxt)
           
            if codeLines == 0 and 1 == 2:
                # always start assuming with a string capture - do not append a line break
                agTxt = agTxt + arrBegBlk
                strOpen = True
                codeLines = 1

            while len(txtLine.strip()) > 0 and 1 == 2:
                codePos = getCodePositions(txtLine)
                #posList = [codePos["closePos"], codePos["escPos"], codePos["echoPos"]]
                if strOpen:
                    if codePos["closePos"] + codePos["escPos"] + codePos["echoPos"] == 0:
                        # just grab everything left on the line and append
                        agTxt = agTxt + txtLine
                        txtLine = ''
                        print('A:' + str(codeLines) + ' newText=' + txtLine)
                    elif codePos["closePos"] > 0 and (codePos["closePos"] < codePos["escPos"] or codePos["closePos"] < codePos["echoPos"]):
                        # bad format --> fail
                        # example: '<string is open>%>'
                        print('#=> Codelines ' + str(codeLines) + ' illegal esc-close')
                        txtLine = ''
                    elif codePos["escPos"] > 0 and (codePos["escPos"] < codePos["echoPos"] or codePos["echoPos"] == 0):
                        # end string at code
                        agTxt = agTxt + txtLine[:codePos["escPos"]].rstrip() + arrEndBlk
                        txtLine = txtLine[codePos["escPos"]+3:]
                        escapeOpen = True
                        echoOpen = False
                        strOpen = False
                        codePos = getCodePositions(txtLine)
                        print('B:' + str(codeLines) + ' newText=' + txtLine)
                    elif codePos["echoPos"] > 0 and (codePos["echoPos"] < codePos["escPos"] or codePos["escPos"] == 0):
                        # concatenate variable output
                        agTxt = agTxt + txtLine[:codePos["echoPos"]].rstrip() + echoBegBlk
                        txtLine = txtLine[codePos["echoPos"]+4:]
                        echoOpen = True
                        escapeOpen = False
                        strOpen = False
                        codePos = getCodePositions(txtLine)
                        print('C:' + str(codeLines) + ' newText=' + txtLine)
                    else:
                        # unknown when this would be used
                        print('\n================================> UNKNOWN LOGIC. Line= ' + str(codeLines)) 
                elif escapeOpen:
                    if codePos["closePos"] + codePos["escPos"] + codePos["echoPos"] == 0:
                        # just grab everything left on the line and append
                        agTxt = agTxt + txtLine
                        txtLine = ''
                        print('D:' + str(codeLines) + ' newText=' + txtLine)
                    elif (codePos["escPos"] < codePos["closePos"] and codePos["escPos"] > 0) or (codePos["echoPos"] < codePos["closePos"] and codePos["echoPos"] > 0):
                        # bad format --> fail
                        # example: '<% escape is open <%='
                        print('#=> Codelines ' + str(codeLines) + ' illegal esc/echo-open')
                        txtLine = ''
                    elif codePos["closePos"] > 0:
                        # end escape at close
                        agTxt = agTxt + txtLine[:codePos["closePos"]]
                        txtLine = txtLine[codePos["closePos"]+3:]
                        escapeOpen = False
                        echoOpen = False
                        strOpen = False
                        codePos = getCodePositions(txtLine)
                        if codePos["escPos"] == 1:
                            # start new code
                            agTxt = agTxt + '\n'
                            txtLine = txtLine[4:]
                            escapeOpen = True
                        elif codePos["echoPos"] == 1:
                            # start new string
                            # this is a new line where the result needs to look like:
                            #  array[i] = recordset.columname || $_$string_and_text...
                            # I dont know how to do this yet
                            #agTxt = agTxt + '\n' + arrBegBlk
                            #txtLine = txtLine[5:]
                            echoOpen = True
                            # remove this
                            agTxt = agTxt + txtLine
                            txtLine = ''
                        elif codePos["escPos"] > 1 or codePos["echoPos"] > 1:
                            # start new string
                            # remove this
                            agTxt = agTxt + txtLine
                            txtLine = ''
                        else:
                            # everything is a string
                            if len(txtLine.strip()) > 0:
                                # start a string
                                # remove this
                                agTxt = agTxt + txtLine
                                txtLine = ''
                            else:
                                txtLine = ''
                                # but we still do not have a mode for the next line ....
                                # need a determineMode function that takes the text and
                                # returns str, esc, echo, options as the new-mode to enter
                            
                        print('E:' + str(codeLines) + ' newText=' + txtLine)
                elif echoOpen:
                    # remove this
                    agTxt = agTxt + txtLine
                    txtLine = ''
                else:
                    print('\n================================> LOGIC ERROR AAA. Line= ' + str(codeLines)) 
                    
                    
            #agTxt = agTxt + txtLine + '\n'
            if txtLine.lower().strip() == '<%options':
                lineContext = 'options'
            else:
                codeTxt = codeTxt + txtLine + '\n'
        elif lineContext == 'options':
            rawOptTxt = rawOptTxt + txtLine.strip() + '\n'
        else:
            #raise an error
            pass

    # process code
    codeTxt = '\n' + arrBegBlk + codeTxt
    codeTxt = codeTxt.replace('<% ', arrEndBlk)
    codeTxt = codeTxt.replace('<%\n', arrEndBlk)
    echoPos = 1
    while echoPos > 0:
        codePos = getCodePositions(codeTxt)
        echoPos = codePos["echoPos"]
        if echoPos > 0:
            print('found echoPos for position ' + str(echoPos))
            codePos = getCodePositions(codeTxt[echoPos:])
            if codePos["closePos"] > 0:
                codeTxt = codeTxt[:echoPos] + codeTxt[echoPos:].replace(' %>', echoEndBlk, 1)
            else:
                # fail. cannot have an echo with no end
                print('bad file')
                
            codeTxt = codeTxt.replace('<%= ', echoBegBlk, 1)
            codePos = getCodePositions(codeTxt)
            echoPos = codePos["echoPos"]
    codeTxt = codeTxt.replace(' %>', '\n' + arrBegBlk)
    codeTxt = codeTxt.replace('\n%>', '\n' + arrBegBlk)
    codeTxt = codeTxt.replace('<%/','<%')
    codeTxt = codeTxt.replace('/%>','%>')
    codeTxt = codeTxt.rstrip()
    lastArrEnd = codeTxt.rfind(arrEndBlk)
    lastArrBeg = codeTxt.rfind(arrBegBlk)
    if lastArrBeg > lastArrEnd:
        codeTxt = codeTxt + arrEndBlk
    codeTxt = codeTxt.replace(arrBegBlk + arrEndBlk, '')
    
    
    #process options
    rawOptTxt = rawOptTxt.lower()
    if rawOptTxt.find('immutable') > -1:
        optionsTxt = optionsTxt.replace('&VOLATILITY', 'IMMUTABLE')
    if rawOptTxt.find('stable') > -1:
        optionsTxt = optionsTxt.replace('&VOLATILITY', 'STABLE')
    if rawOptTxt.find('volatile') > -1:
        optionsTxt = optionsTxt.replace('&VOLATILITY', 'VOLATILE')
    if rawOptTxt.find('invoker') > -1:
        optionsTxt = optionsTxt.replace('&SECURITY', 'SECURITY INVOKER')
    if rawOptTxt.find('definer') > -1:
        optionsTxt = optionsTxt.replace('&SECURITY', 'SECURITY DEFINER')
    if rawOptTxt.find('unsafe') > -1:
        optionsTxt = optionsTxt.replace('&PARALLEL', 'PARALLEL UNSAFE')
    if rawOptTxt.find(' safe') > -1:
        optionsTxt = optionsTxt.replace('&PARALLEL', 'PARALLEL SAFE')

    costNum = ''.join((n if n in '0123456789' else '') for n in rawOptTxt).strip()
    if costNum == '':
        optionsTxt = optionsTxt.replace('&COST', 'COST 100')
    else:
        costNum = 'COST ' + str(costNum)
        optionsTxt = optionsTxt.replace('&COST', costNum)

    # insert option defaults
    optionsTxt = optionsTxt.replace('&VOLATILITY', 'VOLATILE')
    optionsTxt = optionsTxt.replace('&SECURITY', 'SECURITY INVOKER')
    optionsTxt = optionsTxt.replace('&PARALLEL', 'PARALLEL SAFE')
    #if rawOptTxt.find('cost') > 0:
    #    optionsTxt = optionsTxt.replace('&PARALLEL', 'PARALLEL UNSAFE')
    
    print(agTxt + codeTxt + returnTxt + optionsTxt)
    #print('\n' + rawOptTxt)

    

def junk():

    test_str = "This <% is <% laughing //%> l <% laugh %>thank you."

    regex = r"(laugh)"

    matches = re.search(regex, test_str)

    if matches:
        print ("Match was found at {start}-{end}: {match}".format(start = matches.start(), end = matches.end(), match = matches.group()))
    
        for groupNum in range(0, len(matches.groups())):
            groupNum = groupNum + 1
        
            print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = matches.start(groupNum), end = matches.end(groupNum), group = matches.group(groupNum)))
    
if __name__ == "__main__":
    main()

    
