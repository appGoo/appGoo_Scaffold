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



################################################################################
#
# getConfigFile
# Returns a nominated JSON file, if no file specified returns the build config
# To-do:
#       - Allow a different file to specified from a runtime parameter
#       - Proper Error Reporting for JSON errors or file non-existant
#
################################################################################

def getConfigFile(configFile = 'agBuildConfig.json'):
    try:
        with open(configFile) as cfg:
          return json.load(cfg)

    except FileNotFoundError as err:
    # print(dir(err))
        print(err.strerror + ' - ', err.filename)


################################################################################
#
# writeOutputFile
# Appends a supplied text string to the nominated file. If nothing is provided
# it will just append a hash '#'
# To-do:
#       - Proper Error Reporting for file non-existant or unavailable to write
#
################################################################################

def writeOutputFile(fileName, appendText = '#'):

    with open(fileName, 'a') as f:
        f.write(appendText + '\n')



################################################################################
#
# getSQLFiles
# Processes all files in a nominated directory and checks to see if they qualify
# as a SQL file and then requests them to be processed. In addition, if it is
# an 'include' file it then requests that the include file is processed
#
# To-do:
#       - Proper Error Reporting for typical problems (not known at this stage)
#
################################################################################

def getSQLFiles(fileName, searchPath, sqlQualifier, includeQualifier):

# consider using a decorator to have the listdir overlay the processing aspect    
    currDir = os.getcwd() + '/'
    filesToRead = os.listdir(searchPath)
    filesToRead.sort()
    for file in filesToRead:
        if file.endswith(includeQualifier):
            processIncludeFile(fileName, currDir, searchPath + '/' + file)
        elif file.endswith(sqlQualifier):
            processSQLFile(fileName, currDir, searchPath + '/' + file)



################################################################################
#
# processIncludeFile
# It reads each line of a supplied file and passes it to be processed as a
# SQL file
#
# To-do:
#       - Enhance to only process SQL files that meet the SQL qualifier
#       - Trap errors for file not existing
#       - Cater for empty lines
#
################################################################################

def processIncludeFile(fileName, currDir, filePath):
    fullFilePath = currDir + filePath
    print('Found include file: ' + fullFilePath)
    writeOutputFile(fileName, '-- Processing Include File: ' + fullFilePath)
    with open(fullFilePath, 'r') as f:
        for LineInFile in f:
            if LineInFile.strip()[:2] != '--':
                processSQLFile(fileName, currDir, LineInFile.rstrip('\n')) 



################################################################################
#
# processSQLFile
# Appends the contents of the supplied file to the output file. It does not
# validate the contents of the file.
#
# To-do:
#       - Error reporting for the file not existing or being unavailable
#
################################################################################

def processSQLFile(fileName, currDir, filePath):
    print('Appending from ' + currDir + filePath)
    fullFilePath = currDir + filePath
    fullFilePath = fullFilePath.replace('//','/')
    writeOutputFile(fileName, '-- Appending SQL File: ' + fullFilePath)
    sqlFile = open(fullFilePath, "r")
    sqlText = sqlFile.read()
    writeOutputFile(fileName, sqlText)
    sqlFile.close()
    


################################################################################
#
# deleteFiles
# delete files that meet a criteria
#
# To-do:
#       - Error reporting for the file not existing or being unavailable
#
################################################################################


def deleteFiles(searchPath, fileQualifier, keepFiles):

    currDir = os.getcwd() + '/'
    filesToRead = os.listdir(currDir + searchPath)
    filesToRead.sort()
    for file in filesToRead:
        if file.endswith(fileQualifier):
            if file != any(keepFiles):
                print('found file to delete: ' + file)
            


################################################################################
#
# runSQL
# performs a shell command and returns the output - whether it is successful
# or fails
#
# To-do:
#       - Error Reporting
#
################################################################################

def runSQL(sqlText):
    return subprocess.run([sqlText], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, check=True)
    



################################################################################
#
# main
# This is where the program begins.
#
# To-do:
#       - Intelligent error reporting to understand where problems are occurring
#
################################################################################
        
def main():

    # get timestamp into a variable
    _buildts = datetime.datetime.now()

    # Enhance this with 'click' to make this the runtime parameter
    buildConfigData = getConfigFile()
    installConfigData = "x"
    upgradeConfigData = "x"

    # start a log file if requested (we need the name regardless for cleanup
    logFile = _buildts.strftime("%y%m%d-%H%M%S") + '-build.log'
    if buildConfigData["agOptions"]["fileLog"][:1].lower() == "y":
        writeLog = True
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
        getSQLFiles(sqlFile, bldStruct, buildConfigData["agBuild"]["sqlFileQualifier"], buildConfigData["agBuild"]["includeFileQualifier"])

    #finalise output file

    #do data installation if necessary
    #include the creation of a dbLog

    #do data update if necessary
    #do dbLog if requested

    #execute sql

    #cleanup older files
    keepSQLFiles = (sqlFile)
    print('dont delete: ' + sqlFile)
    deleteFiles("", "-temp.agsql", keepSQLFiles)
    keepLogFiles = (logFile)
    print('dont delete: ' + logFile)
    deleteFiles("", "-build.log", keepLogFiles)
    
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



################################################################################
#
# This is required for when the program is executed from the command line
#
################################################################################

if __name__ == "__main__":
    main()
