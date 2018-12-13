################################################################################
#
# Scaffold Builder
#
# Builds SQL from external files and executes them in the database.
# Part of the appGoo system to serve content direct from the database.
# https://github.com/appGoo
#
# MAJOR TO-DO:
#  - Install SQL. Make sql statement configurable
#  - Upgrade SQL. Design method for performing an upgrade of appGoo and
#    a developer's application
#  - Error trapping
#  - Logging - suggest an idea to print out the logfile at the end
#  - Command Line
#  - Pre/Post processing. Rather than have commands in the JSON file,
#    instead have a shell file that can be called to execute
#  - Implement incremental updates only. Keep a .build-log file that stores
#    the date that a build was last done and only build files if install is
#    not required and the SQL file (including upgrade) is created or modified
#    after the date. Note that we track a date per config file.
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
    if os.path.exists(currDir):
        filesToRead = os.listdir(searchPath)
        filesToRead.sort()
        for file in filesToRead:
            if file.endswith(includeQualifier):
                processIncludeFile(fileName, currDir, searchPath + '/' + file)
            elif file.endswith(sqlQualifier):
#to-do: check if it has been modified since last run date
#if os.path.getmtime(file) > minTimeStamp:
                processSQLFile(fileName, currDir, searchPath + '/' + file)
    else:
        # trap an error
        pass


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
#to-do: check if it has been modified since last run date
#if os.path.getmtime(file) > minTimeStamp:
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

def deleteFiles(searchPath, fileQualifier, keepFiles, writeLog, logFile):

    currDir = os.getcwd() + '/'
    if os.path.exists(currDir):
        filesToRead = os.listdir(currDir + searchPath)
        filesToRead.sort()
        for file in filesToRead:
            if file.endswith(fileQualifier):
                if file not in(keepFiles):
                    os.remove(file)
                    if writeLog:
                        writeOutputFile(logFile, 'Deleted file: ' + currDir + file)  
    else:
        if writeLog:
                        writeOutputFile(logFile, '*** WARNING: currDir is invalid: ' + currDir + '/n*** FILES NOT DELETED')  



################################################################################
#
# buildAndProcess
# builds a list of items to process. Used for pre- and post-processing as
# well as all SQL parsing
#
# Pre- and Post-Processing:
# run shell scripts in the operating system. The scripts must exist in the
# same directory as this build executable
#
# To-do:
#       - Ensure failure causes this program to stop
#
################################################################################

def processScripts(jsonQualifier, buildConfigData, writeLog, logFile, sqlFile=""):

    if jsonQualifier == "preprocessing":
        refs = ["Pre-Processing","script-", "./", "", ""]
    elif jsonQualifier == "postprocessing":
        refs = ["Post-Processing","script-", "./", "", ""]
    elif jsonQualifier == "agBuild":
        refs = ["Application Build","build-", "", "sqlFileQualifier", "includeFileQualifier"]
    elif jsonQualifier == "agInstallation":
        refs = ["Application Installation","installation-", "", "sqlFileQualifier", "includeFileQualifier"]
    elif jsonQualifier == "agUpgrade":
        refs = ["Application Upgrade","upgrade-", "", "sqlFileQualifier", "includeFileQualifier"]
    else:
        #we have a problem
        pass
    
    i = 0
    foundJSON = True
    processRef = ''
    Instructions = []
    while foundJSON:
        i += 1
        processRef = refs[1] + '0' + str(i) if i < 10 else refs[1] + str(i)
        try:
            Instructions.append(refs[2] + buildConfigData[jsonQualifier][processRef])
        except KeyError as err:
            foundJSON = False
        except:
            raise

    if writeLog:
        writeOutputFile(logFile, refs[0] + ' Script Output--->')

    for item in Instructions:
        try:
            if jsonQualifier in ("preprocessing", "postprocessing"):
                processResult = str(runShellCmd(item))
                if writeLog:
                    writeOutputFile(logFile, 'Script: ' + item + '\n' + str(processResult))
            else:
                writeOutputFile(sqlFile, '-- # DEBUG: item=' + item)
                getSQLFiles(sqlFile, item, buildConfigData[jsonQualifier][refs[3]], buildConfigData[jsonQualifier][refs[4]])

        except PermissionError as err:
            if writeLog:
                writeOutputFile(logFile, '*** FATAL ***/nShell script ' + script + ' has permission denied/nMost likely this means that the script is not executable. Use chmod a+x')
        except:
            raise

    if writeLog:
        writeOutputFile(logFile, '\n')





################################################################################
#
# runShellCmd
# performs a shell command and returns the output - whether it is successful
# or fails
#
# To-do:
#       - Error Reporting
#
################################################################################

def runShellCmd(cmd):
    return subprocess.run([cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, check=True)
    



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
#change this -- get a timestamp from .agBuildHistory.log
    _buildflt = _buildts.timestamp()

    # Enhance this with 'click' to make this the runtime parameter
    buildConfigData = getConfigFile()
    #upgradeConfigData = "x"

    # start a log file if requested (we need the name regardless for cleanup
    logFile = _buildts.strftime("%y%m%d-%H%M%S") + '-build.log'
    if buildConfigData["agOptions"]["fileLog"][:1].lower() == "y":
        writeLog = True
        writeOutputFile(logFile, '# appGoo Build ' + str(_buildts.strftime("%Y-%m-%d %H:%M:%S")))
    else:
        writeLog = False

    
    #do a connection to the DB to make sure it is OK
    checkSQL = buildConfigData["agDatabase"]["installCheckSQL"]
    checkSQL = r"-c '\x' -c '" + checkSQL + r";'"
    testSQL = buildConfigData["agDatabase"]["sqlCmd"]
    testSQL = testSQL.replace("&CMDS", checkSQL)
    testSQL = testSQL.replace("&DB", buildConfigData["agDatabase"]["dbName"])
    testSQL = testSQL.replace("&UNAME", buildConfigData["agDatabase"]["user"])

    #####################################################################
    #
    # Test if appGoo installation has been performed in the database
    # --------------------------------------------------------------
    # Not only does this result inform us that the db is available and the
    # credentials are correct, but it also informs us whether appGoo has
    # not been installed by checking for the existence of an appGoo object
    # in the result. If there is no result the string contains '(0 rows)'
    # which means that it is not installed. Any rows returned mean that
    # appGoo is installed. Note that the SQL Statement is configurable by
    # the user in case they customise appGoo objects.
    #
    #####################################################################

    testConnect = str(runShellCmd(testSQL))
    doInstall = False if testConnect.find("(0 rows)") == -1 else True
    if writeLog:
        writeOutputFile(logFile, 'Test Connection Output\n----------------------\n' + str(testConnect) +'\n----------------------\ndoInstall=' + str(doInstall))  


    #####################################################################
    #
    # Database logging
    # --------------------------------------------------------------
    # 1) User can set whether this is done in the config file
    # 2) We only insert records, we do not purge old records, dev must maintain
    # 3) We can only do DB logging once installation is complete
    # 4) Until installation is complete we will append the SQL to a
    #    temporary SQL file that we execute after installation
    # 5) Anything written to the log file should have an equivalent record
    #    in the database log
    # 6) Errors in the database log will be added to the log file but not
    #    cause a stop in processing
    #
    #####################################################################

    doDbLog = True if buildConfigData["agOptions"]["dbLog"][:1].lower() == "y" else False
    if writeLog:
        writeOutputFile(logFile, 'doDbLog = ' + str(doDbLog))

    if doDbLog:
        pass 

    #perform pre-processing
    # we only check for the first letter
    # n = no,never; a,y =always, yes; o,i = only if installed, instal
    doPreProcess = (buildConfigData["preprocess"]["do-preprocess"][:1].lower() in("a", "y"))
    if not doPreProcess and doInstall and (buildConfigData["preprocess"]["do-preprocess"][:1] in("o", "i")):
        doPreProcess = True

    if writeLog:
        writeOutputFile(logFile, 'doPreProcess: ' + str(doPreProcess))

    if doPreProcess:
        processScripts('preprocessing', buildConfigData, writeLog, logFile)

        
    #do appGoo installation
    if doInstall:
        pass
    #to-do: add install logic

    #do appGoo upgrade
    #to do an appGoo upgrade we check for all SQL files (raw & includes)
    #that have a modified time > than last build run
    #the .build-history.log file maintains the latest run time (and by which
    #config file it was done by) in Line 1
    #the remaining records are the last time for their config file and they
    #replace the line in the file - but only if they completed with no errors
    pass



    #start an output file (it is a hidden file)
    sqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-temp.agsql'
    writeOutputFile(sqlFile, '/* appGoo SQL to be executed ' + str(_buildts) + ' */')
    if writeLog:
        writeOutputFile(logFile, 'Created SQL File ' + sqlFile) 

    #build SQL
    processScripts("agBuild", buildConfigData, writeLog, logFile, sqlFile)



    #finalise output file

    #do data installation if necessary
    #include the creation of a dbLog

    #do data update if necessary
    #do dbLog if requested

    #execute sql

    #cleanup older files
    keepSQLFiles = (sqlFile)
    deleteFiles("", "-temp.agsql", keepSQLFiles, writeLog, logFile)
    keepLogFiles = (logFile)
    deleteFiles("", "-build.log", keepLogFiles, writeLog, logFile)
    
    
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
