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
#from pprint import pprint



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

def buildAndProcess(jsonQualifier, configData, writeLog, logFile, sqlFile=""):

    if jsonQualifier == "preprocess":
        refs = ["Pre-Processing","script-", "./", "", ""]
    elif jsonQualifier == "postprocess":
        refs = ["Post-Processing","script-", "./", "", ""]
    elif jsonQualifier == "appBuild":
        refs = ["Application Build","build-", "", "sqlFileQualifier", "includeFileQualifier"]
    elif jsonQualifier == "appInstallation":
        refs = ["Application Installation","installation-", "", "sqlFileQualifier", "includeFileQualifier"]
    elif jsonQualifier == "appUpgrade":
        refs = ["Application Upgrade","upgrade-", "", "sqlFileQualifier", "includeFileQualifier"]
    elif jsonQualifier == "agInstallation":
        refs = ["appGoo Installation","installation-", "", "sqlFileQualifier", "includeFileQualifier"]
    elif jsonQualifier == "agUpgrade":
        refs = ["appGoo Upgrade","upgrade-", "", "sqlFileQualifier", "includeFileQualifier"]
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
            Instructions.append(refs[2] + configData[jsonQualifier][processRef])

        except KeyError as err:
            foundJSON = False
        except:
            raise

    if writeLog:
        writeOutputFile(logFile, refs[0] + ' Script Output--->')

    for item in Instructions:
        try:
            if jsonQualifier in ("preprocess", "postprocess"):
                processResult = str(runShellCmd(item))
                if writeLog:
                    writeOutputFile(logFile, 'Script: ' + item + '\n' + str(processResult))
            else:
                writeOutputFile(sqlFile, '-- # DEBUG: item=' + item)
                getSQLFiles(sqlFile, item, configData[jsonQualifier][refs[3]], configData[jsonQualifier][refs[4]], writeLog, logFile)

        except PermissionError as err:
            if writeLog:
                writeOutputFile(logFile, '*** FATAL ***/nShell script ' + script + ' has permission denied/nMost likely this means that the script is not executable. Use chmod a+x')
        except:
            raise

    if writeLog:
        writeOutputFile(logFile, '\n')





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
# execSQL
# Submits SQL into the database and returns a result of the command ouput property
# To-do:
#       - Error Management
#
################################################################################

def execSQL(jsonQualifier, jsonBuildFile, jsonInstallFile, sqlFile, sqlLogFile, writeLog, logFile): 

    #sqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + jsonQualifier + '-exec.agsql'
    if jsonQualifier[:6].lower() == 'appgoo':
        buildSQL = jsonInstallFile["runOptions"]["sqlCmd"]
        buildSQL = buildSQL.replace("&UNAME", jsonInstallFile["runOptions"]["dbUser"])
    else:
        buildSQL = jsonBuildFile["runOptions"]["sqlCmd"]
        buildSQL.replace("&UNAME", jsonBuildFile["runOptions"]["dbUser"])
        
    buildSQL = buildSQL + " &> " + sqlLogFile
    buildSQL = buildSQL.replace("&DB", jsonInstallFile["runOptions"]["dbName"])
    buildSQL = buildSQL.replace("&CMDS", '--set ON_ERROR_STOP=on --set AUTOCOMMIT=off -f ' + sqlFile)

    buildResult = str(runShellCmd(buildSQL))
    foundError = str(buildResult).find('psql:' + sqlFile)
    
    if foundError > 0:
        buildSuccessOut = ("False", str(buildResult)[foundError + len(sqlLogFile)+5:].lstrip(" "))
    else:
        buildSuccessOut = ("True", str(buildResult)[:500])

    if writeLog:
        writeOutputFile(logFile, 'SQL Execution for: ' + jsonQualifier + '\n---------------------->')
        if buildSuccessOut[0] == 'False':
            writeOutputFile(logFile, '**** BUILD ERROR REPORTED ***\n' + buildSuccessOut[1] + '\n<----------------------')
        else:
            writeOutputFile(logFile, 'SQL was successfully run')
        
        writeOutputFile(logFile, 'Refer to file ' + sqlLogFile + ' for output on SQL run')
    
    return buildSuccessOut




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
# getSQLFiles
# Processes all files in a nominated directory and checks to see if they qualify
# as a SQL file and then requests them to be processed. In addition, if it is
# an 'include' file it then requests that the include file is processed
#
# To-do:
#       - Proper Error Reporting for typical problems (not known at this stage)
#
################################################################################

def getSQLFiles(fileName, searchPath, sqlQualifier, includeQualifier, writeLog, logFile):

# consider using a decorator to have the listdir overlay the processing aspect    
    currDir = os.getcwd() + '/'
    if os.path.exists(currDir):
        filesToRead = os.listdir(searchPath)
        filesToRead.sort()
        for file in filesToRead:
            if file.endswith(includeQualifier):
                if writeLog:
                    writeOutputFile(logFile, 'Found include file: ' + searchPath + '/' + file)
                processIncludeFile(fileName, currDir, searchPath + '/' + file, writeLog, logFile)
            elif file.endswith(sqlQualifier):
#to-do: check if it has been modified since last run date
#       note- appGoo Installation ignores last modified date
#if os.path.getmtime(file) > minTimeStamp:
                if writeLog:
                    writeOutputFile(logFile, 'Found SQL file:     ' + searchPath + '/' + file)
                processSQLFile(fileName, currDir, searchPath + '/' + file, writeLog, logFile)
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

def processIncludeFile(fileName, currDir, filePath, writeLog, logFile):

    fullFilePath = currDir + filePath
    with open(fullFilePath, 'r') as f:
        for LineInFile in f:
            if LineInFile.strip()[:2] != '--':
#to-do: check if it has been modified since last run date
#       note- appGoo installation ignores modified date
#if os.path.getmtime(file) > minTimeStamp:
                if writeLog:
                    writeOutputFile(logFile, 'Parsing SQL file:   ' + LineInFile.rstrip('\n'))
                processSQLFile(fileName, currDir, LineInFile.rstrip('\n'), writeLog, logFile) 



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

def processSQLFile(fileName, currDir, filePath, writeLog, logFile):

    fullFilePath = currDir + filePath
    fullFilePath = fullFilePath.replace('//','/')
    writeOutputFile(fileName, '-- Appending SQL File: ' + fullFilePath)
    sqlFile = open(fullFilePath, "r")
    sqlText = sqlFile.read()
    writeOutputFile(fileName, sqlText)
    sqlFile.close()
    if writeLog:
        writeOutputFile(logFile, 'Appended SQL file: ' + filePath)
    



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
################################################################################
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
#change this -- get a timestamp from .appBuildHistory.log
    _buildflt = _buildts.timestamp()

    # Enhance this with 'click' to make this the runtime parameter
    buildConfigData = getConfigFile()
    installConfigData = getConfigFile('agInstallConfig.json')

    currDir = os.getcwd() + '/'

    # start a log file if requested (we need the name regardless for cleanup
    logFile = _buildts.strftime("%y%m%d-%H%M%S") + '-agbuild.log'
    if buildConfigData["runOptions"]["fileLog"][:1].lower() == "y":
        writeLog = True
        writeOutputFile(logFile, '# appGoo Build ' + str(_buildts.strftime("%Y-%m-%d %H:%M:%S")) + '\nCurrent Working directory: ' + currDir)
    else:
        writeLog = False

    
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
    
    testSqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-test-exec.agsql'
    testSqlLogFile = _buildts.strftime("%y%m%d-%H%M%S") + '-sql-output-test-agbuild.log'
    checkSQL = '/* Testing connection to database ' + str(_buildts) + ' */\n' + installConfigData["runOptions"]["installCheckSQL"] + ';'
    checkSQL = checkSQL.replace(';;',';')

    writeOutputFile(testSqlFile, checkSQL)
    if writeLog:
        writeOutputFile(logFile, 'Started Test SQL File ' + testSqlFile + '\nStarted Test SQL Output File ' + testSqlLogFile) 

    #build & run SQL
    buildResult = execSQL("appGooTest", buildConfigData, installConfigData, testSqlFile, testSqlLogFile, writeLog, logFile) 

        
##    checkSQL = installConfigData["runOptions"]["installCheckSQL"]
##    checkSQL = r"-c '\x' -c '" + checkSQL + r";'"
##    testSQL = installConfigData["runOptions"]["sqlCmd"]
##    testSQL = testSQL.replace("&CMDS", checkSQL)
##    testSQL = testSQL.replace("&DB", installConfigData["runOptions"]["dbName"])
##    testSQL = testSQL.replace("&UNAME", installConfigData["runOptions"]["dbUser"])
##    testConnect = str(runShellCmd(testSQL))

    doInstall = False if buildResult[1].find("(0 rows)") == -1 else True
    if writeLog:
        writeOutputFile(logFile, 'appGoo installation required: ' + str(doInstall))



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

    doDbLog = True if buildConfigData["runOptions"]["dbLog"][:1].lower() == "y" else False
    if writeLog:
        writeOutputFile(logFile, 'doDbLog:       ' + str(doDbLog))

    if doDbLog:
        pass 

    #perform pre-processing
    # we only check for the first letter
    # n = no y = yes  i = only If Installed
    doPreProcess = (buildConfigData["preprocess"]["do-preprocess"][:1].lower() == "y")
    if not doPreProcess and doInstall and (buildConfigData["preprocess"]["do-preprocess"][:1] == "i"):
        doPreProcess = True

    if writeLog:
        writeOutputFile(logFile, 'doPreProcess:  ' + str(doPreProcess))

    if doPreProcess:
        buildAndProcess('preprocess', buildConfigData, writeLog, logFile)

        

    #####################################################################
    #
    # appGoo Installation
    # --------------------------------------------------------------
    #
    # This is the installation of appGoo into a fresh database
    # It will be treated in the same vein as the build except that
    # it uses the appGoo installation json config file as its source
    # of content. The SQL file is built seperately to other SQL files
    # and is not subject to purging so that it is kept and can be
    # reviewed in the future if need be.
    #
    #####################################################################

    if doInstall:
        sqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-appGoo-install-agbuild.agsql'
        writeOutputFile(sqlFile, "-- appGoo Installation SQL Execution File created on " + _buildts.strftime("%y-%m-%d %H:%M:%S"))
        if writeLog:
            writeOutputFile(logFile, 'Starting appGoo installation into file ' + sqlFile)

        buildAndProcess("agInstallation", installConfigData, writeLog, logFile, sqlFile)
# to-do: execute


    #do appGoo upgrade
    #to do an appGoo upgrade we check for all SQL files (raw & includes)
    #that have a modified time > than last build run
    #the .build-history.log file maintains the latest run time (and by which
    #config file it was done by) in Line 1
    #the remaining records are the last time for their config file and they
    #replace the line in the file - but only if they completed with no errors
    pass



    #start an output file (it is a hidden file)
    sqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-appBuild-exec.agsql'
    sqlLogFile = _buildts.strftime("%y%m%d-%H%M%S") + '-sql-output-appBuild-agbuild.log'

    writeOutputFile(sqlFile, '/* appGoo SQL to be executed ' + str(_buildts) + ' */')
    if writeLog:
        writeOutputFile(logFile, 'Started SQL Output File ' + sqlFile + '\nStarted SQL Output File ' + sqlLogFile) 

    #build & run SQL
    buildAndProcess("appBuild", buildConfigData, writeLog, logFile, sqlFile)
    buildResult = execSQL("appBuild", buildConfigData, installConfigData, sqlFile, sqlLogFile, writeLog, logFile) 

##    buildSQL = buildConfigData["runOptions"]["sqlCmd"]
##    buildSQL = buildSQL + " &> " + sqlLogFile
##    buildSQL = buildSQL.replace("&CMDS", '--set ON_ERROR_STOP=on --set AUTOCOMMIT=off -f ' + '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-temp.agsql')
##    buildSQL = buildSQL.replace("&DB", installConfigData["agInstallation"]["dbName"])
##    buildSQL = buildSQL.replace("&UNAME", buildConfigData["runOptions"]["dbUser"])
##
##    buildResult = str(runShellCmd(buildSQL))
##    foundError = str(buildResult).find('psql:' + sqlFile)
##    
##    if foundError > 0:
##        buildSuccess = False
##        buildErrorOut = str(buildResult)[foundError + len(sqlLogFile):]
##    else:
##        buildSuccess = True
##        buildErrorOut = ""
##
##    if writeLog:
##        writeOutputFile(logFile, 'Application Build SQL\n---------------------->')
##        if buildSuccess == False:
##            writeOutputFile(logFile, '**** BUILD ERROR REPORTED ***\n' + buildErrorOut + '\n<----------------------')
##        else:
##            writeOutputFile(logFile, 'Build was successful')
##        
##        writeOutputFile(logFile, 'Refer to file ' + sqlLogFile + ' for output on SQL run')
        
  
        
        
    

    #do data installation if necessary
    #include the creation of a dbLog

    #do data update if necessary
    #do dbLog if requested

    #execute sql

    #perform post-processing
    # we only check for the first letter
    # n = no; y = yes
    doPostProcess = (buildConfigData["postprocess"]["do-postprocess"][:1].lower() == "y")
    
    if writeLog:
        writeOutputFile(logFile, 'doPostProcess: ' + str(doPostProcess))

    if doPostProcess:
        buildAndProcess('postprocess', buildConfigData, writeLog, logFile)

    #cleanup older files
    keepSQLFiles = (testSqlLogFile)
    #to-do: Keep all SQL files executed in this session, delete all others...
    deleteFiles("", "-exec.agsql", keepSQLFiles, writeLog, logFile)
    keepLogFiles = (logFile, testSqlLogFile)
    deleteFiles("", "-agbuild.log", keepLogFiles, writeLog, logFile)
    
    
    #finalise log file and finish dbLog
    if writeLog:
        writeOutputFile(logFile, 'Build complete at : ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        writeOutputFile(logFile, 'This log file ' + logFile + ' will be deleted next time any build process is run\n' + r"Any file ending in '*-agbuild.log' will be deleted, so rename to keep it before next build")
        printFile = open(logFile, "r")
        printText = printFile.read()
        print(printText)
        printFile.close()
    else:
        print('appGoo Build complete.\nParameters:\n\tInstall App:        ' + str(doInstall) + '\n\tDo Pre-Processing:  ' + str(doPreProcess) + '\n\tDo Post-Processing: ' + str(doPostProcess))
        print('You can review SQL output results in ' + sqlLogFile)
        print('Note that the SQL output and any log files you request are deleted by the next successful build run unless you rename them')
        print('Start Time:      ' + str(_buildts.strftime("%Y-%m-%d %H:%M:%S")) + '\nCompletion Time: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if buildSuccess == False:
            print('*** BUILD ERROR ***')
            print(buildErrorOut)

################################################################################
#
# This is required for when the program is executed from the command line
#
################################################################################

if __name__ == "__main__":
    main()
