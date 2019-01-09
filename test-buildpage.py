import os
import re


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
    # hex for '<%%include ' (space follows) & ' %>
    escapeRegex = r"(\x3C\x25\x20)|(\x3C\x25\n)"
    includeRegex = r"(\x3C\x25\x25include\x20)"
    optionsRegex = r"(\x3C\x25\x25options\x20)|(\x3C\x25\x25options\n)"
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
                rStr = '<%%include ' + rawStr
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
    decTxtBlk = '  AS $___agBody___$ \n\nDECLARE\n  __agStrArray_ text[];\n  __i_ integer := 0;\n'
    begTxtBlk = 'BEGIN \n'
    arrBegBlk = '__agStrArray_[__i_] = $___agArray___$'
    arrEndBlk = '$___agArray___$; __i_ = __i_ + 1;\n'
    lineArray = txt.split('\n')
    lineContext = 'start'
    paramCount = 0

    escapeOpen = False
    echoOpen = False
    strOpen = False
    codeLines = 0
    
    for txtLine in lineArray:
        if lineContext == 'start':
            txtLine = txtLine.strip()
            txtLine = txtLine.replace('  ', ' ')
            funcDef = txtLine.split(' ')
            agTxt = 'CREATE OR REPLACE FUNCTION ' + funcDef[0] + ' (\n'
            lineContext = 'params'
        elif lineContext == 'params':
            if txtLine.strip().lower() in ('declare', 'appgoo', 'code', 'begin'):
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
            if txtLine.strip().lower() in ('appgoo', 'code', 'begin'):
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
            escPos = re.search(escapeRegex, txtLine)
            echoPos = re.search(echoRegex, txtLine)
            closePos = re.search(closeRegex, txtLine)
            optionsPos = re.search(optionsRegex, txtLine)
##            if startPos:
##                tmpTxt = txt[startPos.end():]
##                endPos = re.search(closeRegex, tmpTxt)
##                if endPos:
##                    hasChanged = True
##                    rawStr = tmpTxt[:endPos.end()]
##                    incFile = tmpTxt[:endPos.start()].strip()
##                    rStr = '<%%include ' + rawStr
##                    incf = open(incFile, "r")
##                    incTxt = incf.read()
##                    incf.close()
##                    incTxt = incTxt.rstrip('\n')
##                    #print('will replace ' + rStr + ' with ' + incTxt)
##                    txt = txt.replace(rStr, incTxt)
           
            if codeLines == 0:
                # always start assuming with a string capture
                agTxt = agTxt + arrBegBlk
                strOpen = True
                codeLines = 1

            if strOpen:
                if escPos or echoPos or closePos:
                    #do something
                    pass
                else:
                    #capture the whole string
                    agTxt = agTxt + txtLine + '\n'
            else:
                #escapeOpen or echoOpen must be true
                if not escapeOpen and not echoOpen:
                    # bad logic by me --> fix
                    print('\n================================> LOGIC ERROR AAA. Line= ' + str(codeLines)) 
                else:
                    #process for being in escape or echo mode
                    pass
                    
            #agTxt = agTxt + txtLine + '\n' 
        else:
            #raise an error
            pass

    print(agTxt)

    

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

    
