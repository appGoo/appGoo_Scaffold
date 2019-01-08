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

    #i = 1
    #while i > 0:
    #  i = processIncludes(sourceFile, destFile)
    # the function returns how many includes it processed

    # hex for '<%%include ' (space follows)
    includeRegex = r"(\x3C\x25\x25include\x20)"
    closeRegex = r"(\x20\x25\x3E)"

    loopAgain = True
    loopCount = 0
    while loopAgain:
        startPos = re.search(includeRegex, txt)
        if startPos:
            tmpTxt = txt[startPos.end():]
            endPos = re.search(closeRegex, tmpTxt)
            if endPos:
                #incFile = tmpTxt[:endPos.start()].strip()
                rStr = tmpTxt[:endPos.start()]
                incFile = rStr.strip()
                rStr = '<%%include ' + rStr + ' %>'
                incf = open(incFile, "r")
                incTxt = incf.read()
                incf.close()
                incTxt = incTxt.rstrip('\n')
                print('will replace ' + rStr + ' with ' + incTxt)
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
    print(txt)
    
    # all includes resolved, now do other processing

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

    
