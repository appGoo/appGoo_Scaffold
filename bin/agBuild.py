################################################################################
#
# Scaffold Builder
#
# Builds SQL from external files and executes them in the database.
# Part of the appGoo system to serve content direct from the database.
# https://github.com/appGoo
#
################################################################################

# imports
import datetime
import json
import subprocess
import os
#remove this later
from pprint import pprint



# get config file into a json variable
# to-do: allow a different file to be specified
def getConfigFile(configFile = 'agBuildConfig.json'):
    try:
        with open(configFile) as cfg:
          return json.load(cfg)

    except FileNotFoundError as err:
    # print(dir(err))
        print(err.strerror + ' - ', err.filename)



def writeOutputFile(fileName, appendText = '#'):

    #f = open(fileName, 'a') -- this is an older alternative
    with open(fileName, 'a') as f:
        f.write(appendText + '\n')
    #f.close() -- use only if using the older way of doing this



def getFiles(fileName, searchPath, sqlQualifier, includeQualifier):
    
    currDir = os.getcwd() + '/'
    filesToRead = os.listdir(searchPath)
    filesToRead.sort()
    for file in filesToRead:
        if file.endswith(includeQualifier):
            processIncludedFile(fileName, currDir, searchPath + '/' + file)
        elif file.endswith(sqlQualifier):
            processSQLFile(fileName, currDir, searchPath + '/' + file)

def processIncludedFile(fileName, currDir, filePath):
    fullFilePath = currDir + filePath
    print('Found include file: ' + fullFilePath)
    writeOutputFile(fileName, '-- Processing Include File: ' + fullFilePath)
    with open(fullFilePath, 'r') as f:
        for LineInFile in f:
            if LineInFile.strip()[:2] != '--':
                processSQLFile(fileName, currDir, LineInFile.rstrip('\n')) 


def processSQLFile(fileName, currDir, filePath):
    print('Appending from ' + currDir + filePath)
    fullFilePath = currDir + filePath
    fullFilePath = fullFilePath.replace('//','/')
    writeOutputFile(fileName, '-- Appending SQL File: ' + fullFilePath)
    sqlFile = open(fullFilePath, "r")
    sqlText = sqlFile.read()
    writeOutputFile(fileName, sqlText)
    sqlFile.close()
    


def runSQL(sqlText):
    return subprocess.run([sqlText], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, check=True)
    
        
def main():
    """
    Put some explanation here
    """
    # get timestamp into a variable
    _buildts = datetime.datetime.now()

    # Enhance this with 'click' to make this the runtime parameter
    buildConfigData = getConfigFile()
    installConfigData = "x"
    upgradeConfigData = "x"

    # start a log file if requested
    if buildConfigData["agOptions"]["fileLog"][:1].lower() == "y":
        writeLog = True
        logFile = _buildts.strftime("%y%m%d-%H%M%S") + '-build.log'
        writeOutputFile(logFile, '# appGoo Build ' + str(_buildts))
    else:
        writeLog = False

    
    #do a connection to the DB to make sure it is OK
    checkSQL = r"-c '\x' -c 'select $$_appGoo_is_installed_$$ AS isInstalled from pg_catalog.pg_roles where rolname = $$__ag_null__$$;'"
    testSQL = buildConfigData["agDatabase"]["sqlCmd"]
    #testSQL = testSQL.replace("&CMDS", r"-c '\x' -c 'select '__appGoo-installed=true' AS isInstalled from pg_catalog.pg_roles where rolname = 'postgres' or rolname = '__ag_null__';'")
    testSQL = testSQL.replace("&CMDS", checkSQL)
    testSQL = testSQL.replace("&DB", buildConfigData["agDatabase"]["dbName"])
    testSQL = testSQL.replace("&UNAME", buildConfigData["agDatabase"]["user"])

    testConnect = str(runSQL(testSQL))

    #not only does this result inform us that the db is available and the
    # credentials are correct, but it also informs us whether appGoo has
    # been installed by the existence of a string "__appGoo-installed=true"
    # in the result
    doInstall = False if testConnect.find("(0 rows)") == -1 else True
    #doInstall = True if testConnect.find("returncode=0") != -1 else False
    print('doInstall=' + str(doInstall))
    #print(testConnect)
                         
    #start a dbLog if requested (only do if install in db done)

    #a dbLog should be the fully qualified filenames executed 

    #start an output file (it is a hidden file)
    sqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-temp.agsql'
    writeOutputFile(sqlFile, '/* appGoo SQL to be executed ' + str(_buildts) + ' */')
    if writeLog:
        writeOutputFile(logFile, 'Created SQL File ' + sqlFile)  

    #start appending to the output file
    #first, we 
    #we loop through all structures
    i = 0
    foundJSON = True
    buildRef = ''
    buildStructures = []
    while foundJSON:
        i += 1
        buildRef = 'build-0' + str(i) if i < 10 else 'build-' + str(i)
        try:
            buildStructures.append(buildConfigData["agBuild"][buildRef])
            #print('bs['+ str(i) + '] ' + buildStructures[i])
        except KeyError as err:
            foundJSON = False
        except:
            raise

    for bldStruct in buildStructures:
        #print(bldStruct)
        writeOutputFile(sqlFile, '-- # DEBUG: bldStruct=' + bldStruct)
        getFiles(sqlFile, bldStruct, buildConfigData["agBuild"]["sqlFileQualifier"], buildConfigData["agBuild"]["includeFileQualifier"])

    #finalise output file

    #do data installation if necessary
    #include the creation of a dbLog

    #do data update if necessary
    #do dbLog if requested

    #execute sql

    #cleanup older files
        #get a directory list
        #if filename != current log file:
            #if ends with '-build.log' then delete
        #if filename != current agsql file:
            #if ends with '-temp.agsql' then delete
        #note that all file deletes should be posted in the log file

    #finalise log file and finish dbLog

    print('At ' + str(_buildts))
    pprint(buildConfigData)
    print(buildConfigData["agDatabase"]["targetType"])



if __name__ == "__main__":
    main()
