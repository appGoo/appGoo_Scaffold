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
    includeRegex = r"(\x3C\x25\x25include\x20)"
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
    # remove comments that start with '#'
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
    lineArray = txt.split('\n')
    lineContext = 'start'
    for txtLine in lineArray:
        if lineContext == 'start':
            txtLine = txtLine.replace('  ', ' ')
            funcDef = txtLine.split(' ')
            agTxt = 'CREATE OR REPLACE FUNCTION ' + funcDef[0] + ' (\n'
            lineContext = 'declare'
        elif lineContext == 'declare':
            if txtLine.strip().lower() == 'declare':
                agTxt = agTxt + 'DECLARE \n'
                lineContext = 'params'
            else:
                lineContext = 'appgoo'
        elif lineContext == 'params':
            if txtLine.strip().lower() == 'appgoo':
                lineContext = 'appgoo'
            else:
                # insert parameter
                pass
        elif lineContext == 'appgoo':
                if txtLine.strip().lower() == 'appgoo':
                    # we now must do the RETURNS
                    lineContext = 'code'
                else:
                    #raise an error
                    pass
        elif lineContext == 'code':
            agTxt = agTxt + txtLine + '\n' 
        else:
            #raise an error
            pass


    print(agTxt)

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

    
