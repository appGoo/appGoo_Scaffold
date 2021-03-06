################################################################################
#
# Scaffold Builder
#
# Builds SQL from external files and executes them in the database.
# Part of the appGoo system to serve content direct from the database.
# https://github.com/appGoo
#
# MAJOR TO-DO:
#  - Re-do include functionality to allow up to 100 nested includes
#  - Allow includes to replace text in a line rather than start and end
#    with a line break
#  - Install SQL. Make sql statement configurable
#  - Upgrade SQL. Design method for performing an upgrade of appGoo and
#    a developer's application
#  - Error trapping
#  - Logging - improve the appearance of the captured log 
#  - Command Line
#  - Implement incremental updates only. Keep a .agbuild.history file that stores
#    the date that a build was last done and only build files if install is
#    not required and the SQL file (including upgrade) is created or modified
#    after the date. Note that we track a date per config file.
#  - All the specification of how to show a timestamp with a RunOption in the
#    build file with a default of "%Y-%m-%d %H:%M:%S" (iso format)
#
################################################################################

# imports
import os
import sys
import subprocess
import datetime
import json
import re

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

def buildAndProcess(jsonQualifier, configData, sqlFile="", sqlLogFile=""):

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

##    try:
##        runMode = "File" if configData[jsonQualifier]["runMode"][:1].lower() == "f" else "Batch"
##    except:
##        runMode = "Batch"
##
##    if writeLog:
##        writeOutputFile(logFile, "runMode for " + jsonQualifier + " = " + runMode)
    
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
                getSQLFiles(sqlFile, item, configData[jsonQualifier][refs[3]], configData[jsonQualifier][refs[4]], sqlLogFile)

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

def deleteFiles(searchPath, fileQualifier, keepFiles):

    #currDir = os.getcwd() + '/'
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

def execSQL(jsonQualifier, jsonBuildFile, jsonInstallFile, sqlFile, sqlLogFile, minimiseStdOut=True): 

    if jsonQualifier[:6].lower() == 'appgoo':
        runSQL = jsonInstallFile["runOptions"]["sqlCmd"]
        runSQL = runSQL.replace("&UNAME", jsonInstallFile["runOptions"]["dbUser"])
    else:
        runSQL = jsonBuildFile["runOptions"]["sqlCmd"]
        runSQL = runSQL.replace("&UNAME", jsonBuildFile["runOptions"]["dbUser"])
        
    runSQL = runSQL.replace("&DB", jsonInstallFile["runOptions"]["dbName"])
    if processSQL == "f":
        runSQL = runSQL.replace("&CMDS", r"--set ON_ERROR_STOP=on --set AUTOCOMMIT=on -f " + sqlFile)
    else:
        runSQL = runSQL.replace("&CMDS", r"--set ON_ERROR_STOP=on --set AUTOCOMMIT=off -f " + sqlFile)

    runSQL = runSQL + " --echo-errors --output=.sql-output-" + jsonQualifier + "-agbuild.log" if minimiseStdOut else runSQL
    #dont know why - but the psql always fail when I don't pipe the output
    runSQL = runSQL + " &> .tmp-agbuild.log"

    completedCmd = runShellCmd(runSQL)
    cmdResult = str(completedCmd.stdout)
    writeOutputFile(sqlLogFile, cmdResult)

    #check for sql error
    foundError = cmdResult.find('psql:' + sqlFile)
    #check for psql error 
    if foundError < 1:
        foundError = cmdResult.find('psql: FATAL:') if foundError < 1 else foundError
        #check for shell error
        foundError = 1 if cmdResult[:3] == "b'/" else foundError

    #process according to result found
    if foundError > 0:
        cmdSuccessOut = ("False", cmdResult.lstrip(" "))
    else:
        cmdSuccessOut = ("True", cmdResult[1:500])

    #to-do: alter this for "per-file" processing    
    if writeLog:
        writeOutputFile(logFile, 'SQL Execution for: ' + jsonQualifier + '\n---------------------->')
        if cmdSuccessOut[0] == 'False':
            writeOutputFile(logFile, '**** BUILD ERROR REPORTED ***\n' + cmdSuccessOut[1] + '\n<----------------------')
        else:
            writeOutputFile(logFile, 'All SQL was successfully executed')
        
        writeOutputFile(logFile, 'Refer to file ' + sqlLogFile + ' for output captured')
    
    
    return cmdSuccessOut




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

def getSQLFiles(fileName, searchPath, sqlQualifier, includeQualifier, sqlLogFile=""):

# consider using a decorator to have the listdir overlay the processing aspect    
    #currDir = os.getcwd() + '/'
    if os.path.exists(currDir):
        filesToRead = os.listdir(searchPath)
        filesToRead.sort()
        for file in filesToRead:
            if file.endswith(includeQualifier):
                if writeLog:
                    writeOutputFile(logFile, 'Found include file: ' + searchPath + '/' + file)
                processIncludeFile(fileName, searchPath + '/' + file, sqlLogFile)
            elif file.endswith(sqlQualifier):
                processSQLFile(False, fileName, searchPath + '/' + file, sqlLogFile)
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

def processIncludeFile(fileName, filePath, sqlLogFile=""):

    fullFilePath = currDir + filePath
    with open(fullFilePath, 'r') as f:
        for LineInFile in f:
            if LineInFile.strip()[:2] != '--':
#to-do: check if it has been modified since last run date
#       note- appGoo installation ignores modified date
#if os.path.getmtime(file) > minTimeStamp:
                #if writeLog:
                #    writeOutputFile(logFile, 'Parsing SQL file:   ' + LineInFile.rstrip('\n'))
                if LineInFile.strip().lower() in("@commit", "@commit;", "commit;", "commit"):
                    if processSQL == "b" and appendedCommit == False:
                            writeOutputFile(fileName, "\ncommit;\n")
                            appendedCommit == True
                            if writeLog:
                                writeOutputFile(logFile, "issued a commit;")
                        
                else:
                    appendedCommit = False
                    processSQLFile(True, fileName, LineInFile.rstrip('\n'), sqlLogFile) 



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

def processSQLFile(isFromInclude, fileName, filePath, sqlLogFile):

    global continueWork
    
    fullFilePath = currDir + filePath
    fullFilePath = fullFilePath.replace('//','/')

#to-do: check if it has been modified since last run date
#       note- appGoo Installation ignores last modified date
#if os.path.getmtime(file) > minTimeStamp:
    #1. Get the last run date
    #2. Check to see if the file has been modified since that time
    #3. If it has been modified or all files are to be processed, then check runmode,
    #   file causes an execSQL, batch causes an append.

    appendFile = True

    if processModifiedOnly:
        fileModTime = os.path.getmtime(fullFilePath)
        appendFile = True if fileModTime >= lastRun else False

    if appendFile and continueWork:
        if processSQL == "f":
            sqlFileResult = execSQL("appBuild", buildConfigData, installConfigData, fullFilePath, sqlLogFile, True) 
            if sqlFileResult[0] == "False":
                continueWork = False
                stopReason = "The build process has stopped because of errors encountered building the application in the database"
                if writeLog:
                    writeOutputFile(logFile, "***Build process stopped due to an error with a SQL file")
        else:            
            writeOutputFile(fileName, '-- Appending SQL File: ' + fullFilePath)
            sqlFile = open(fullFilePath, "r")
            sqlText = sqlFile.read()
                    
            writeOutputFile(fileName, sqlText)
            sqlFile.close()


        if writeLog and continueWork:
            if processSQL == "f":
                filePath = 'File ' + fullFilePath + ' executed'
            else:
                filePath = '   - Appended file: ' + filePath if isFromInclude else 'Appended file:      ' + filePath

            writeOutputFile(logFile, filePath)
    else:
        if writeLog:
            #to-do: improve this log entry with formatted times and could also because of continueWork=false
            if appendFile == False:
                writeOutputFile(logFile, 'File ignored because of last modified date: ' + filePath)
            elif continueWork:
                #remove this
                writeOutputFile(logFile, '--> File skipped because continueWork = False')




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
    return subprocess.run([cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, check=False)

    


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
#       - Refer to to-do at top of file
#
################################################################################
        
def main():

    #global variables
    global _buildts, continueWork, stopReason, buildConfigData, installConfigData, currDir, logFile, writeLog, historyFile
    global lastRun, currentBuildPhase, processModifiedOnly, processSQL, appendedCommit

    #global tracker of whether to continue processing
    continueWork = True
    stopReason = ""
    processModifiedOnly = False
    processSQL = "b"
    currDir = os.getcwd() + '/'
    appendedCommit = False


    # Enhance this with 'click' to make this the runtime parameter
    buildConfigData = getConfigFile()
    installConfigData = getConfigFile('agInstallConfig.json')
    historyFile = getConfigFile('.agBuild.history')
    lastRun = datetime.datetime.strptime(historyFile["lastRun"]["timeStamp"], "%Y-%m-%d %H:%M:%S").timestamp()
    

    #logfile
    _buildts = datetime.datetime.now()
    _buildflt = _buildts.timestamp()
    logFile = _buildts.strftime("%y%m%d-%H%M%S") + '-agbuild.log'
    writeLog = True if buildConfigData["runOptions"]["fileLog"][:1].lower() == "y" else False
    doDbLog = True if buildConfigData["runOptions"]["dbLog"][:1].lower() == "y" else False
    doPreProcessVal = buildConfigData["preprocess"]["do-preprocess"]
    doPostProcessVal = buildConfigData["postprocess"]["do-postprocess"]
    processModVal = buildConfigData["appBuild"]["modifiedOnly"]
    processSqlVal = buildConfigData["appBuild"]["processSQL"]

    if writeLog:
        writeOutputFile(logFile, '# appGoo Build ' + str(_buildts.strftime("%Y-%m-%d %H:%M:%S")) \
            + '\nCurrent Working directory: ' + currDir)
        writeOutputFile(logFile, 'Parameters and Variables:' \
            + '\n  - Config File:        ' + 'agBuildConfig.json' \
            + '\n  - Log in database:    ' + str(doDbLog) \
            + '\n  - Do Pre-Processing:  ' + doPreProcessVal \
            + '\n  - Do Post-Processing: ' + doPostProcessVal \
            + '\n  - Build modified SQL files only: ' + processModVal \
            + '\n  - Build SQL files individually or in batch: ' + processSqlVal \
            + '\n################################################################################' \
            + '\n#\n# Commencing Build\n#' \
            + '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


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
    # to-do:
    #
    #####################################################################

    if writeLog:
        writeOutputFile(logFile, '\n################################################################################' \
            + '\n# Starting database connectivity test. \nThis also determines whether appGoo is installed' \
            + '\n--------------------------------------------------------------------------------')

    currentBuildPhase = "appGooTest"
    testSqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-testConnection-exec.agsql'
    testSqlLogFile = _buildts.strftime("%y%m%d-%H%M%S") + '-testConnection-agbuild.log'
    checkSQL = '/* Testing connection to database ' + str(_buildts) + ' */\n' + installConfigData["runOptions"]["installCheckSQL"] + ';'
    checkSQL = checkSQL.replace(';;',';')

    writeOutputFile(testSqlFile, checkSQL)

    #build & run SQL
    testResult = execSQL("appGooTest", buildConfigData, installConfigData, testSqlFile, testSqlLogFile, False) 
    if testResult[0] == "False":
        continueWork = False
        stopReason = "The build process has stopped because of errors encountered testing the connection to the database"
        doInstall = False
    else:
        doInstall = False if testResult[1].find("(0 rows)") == -1 else True

    if writeLog and continueWork:
        writeOutputFile(logFile, 'appGoo installation required: ' + str(doInstall) \
            + '\nTest connecting to the database was successful' \
            + '\n================================================================================')
    else:
        #insert output for failure
        pass


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

    if doDbLog:
        pass


    #perform pre-processing
    # we only check for the first letter
    # n = no y = yes  i = only If Installed
    if continueWork:
        currentBuildPhase = "preprocess"
        if doPreProcessVal[:1].lower() == "y":
            doPreProcess = True
        elif doPreProcessVal[:1].lower() == "i" and doInstall == False:
            doPreProcess = True
        else:
            doPreProcess = False

        if writeLog and doPreProcessVal[:1].lower() in("y", "i"):
            writeOutputFile(logFile, '\n\n################################################################################' \
                + '\n# Starting Pre-Processing' \
                + '\n--------------------------------------------------------------------------------')

            if continueWork and doPreProcessVal[:1].lower() == "i":
                if doInstall:
                    writeOutputFile(logFile, 'Pre-Processing will not be performed because appGoo Installation is required')
                else:
                    writeOutputFile(logFile, 'Pre-Processing will be performed because appGoo is installed')

        if doPreProcess and continueWork:
            buildAndProcess('preprocess', buildConfigData)

        if writeLog and doPreProcess:
            writeOutputFile(logFile, 'Pre-Processing completed' \
                + '\n================================================================================')



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

    if continueWork and doInstall:
        writeOutputFile(logFile, '\n\n################################################################################' \
            + '\n# Starting appGoo Installation' \
            + '\n--------------------------------------------------------------------------------')

        currentBuildPhase = "agInstallation"
        instalSqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-appGoo-agInstall-exec.agsql'
        instalSqlLogFile = _buildts.strftime("%y%m%d-%H%M%S") + '-appGoo-agInstall-agbuild.log'    
        writeOutputFile(instalSqlFile, "-- appGoo Installation SQL Execution File created on " + _buildts.strftime("%y-%m-%d %H:%M:%S"))

        buildAndProcess("agInstallation", installConfigData, instalSqlFile)
        agInstalResult = execSQL("agInstallation", buildConfigData, installConfigData, instalSqlFile, instalSqlLogFile, True)

        if agInstalResult[0] == "False":
            continueWork = False
            stopReason = "The build process has stopped because of errors encountered during installation of appGoo"

        if writeLog:
            writeOutputFile(logFile, 'appGoo Installation completed.' + stopReason \
                + '\n#######################################################################################\n')

####### SALLEYN: Stopped Log Cleanup here.

    #do appGoo upgrade
    #to do an appGoo upgrade we check for all SQL files (raw & includes)
    #that have a modified time > than last build run
    #the .build-history.log file maintains the latest run time (and by which
    #config file it was done by) in Line 1
    #the remaining records are the last time for their config file and they
    #replace the line in the file - but only if they completed with no errors
    currentBuildPhase = "agUpgrade"
    pass



    currentBuildPhase = "appBuild"
    processModifiedOnly = True if processModVal[:1].lower() == "y" else False
    # f = file, b = batch
    processSQL = "f" if processSqlVal[:1].lower() in("f", "p") else "b"
    #start an output file (it is a hidden file)
    buildSqlFile = '.' + _buildts.strftime("%y%m%d-%H%M%S") + '-appBuild-exec.agsql'
    buildSqlLogFile = _buildts.strftime("%y%m%d-%H%M%S") + '-sql-output-appBuild-agbuild.log'

    writeOutputFile(buildSqlFile, '/* appGoo SQL to be executed ' + str(_buildts) + ' */')
    if writeLog:
        writeOutputFile(logFile, 'Started SQL file ' + buildSqlFile + '\nCapturing SQL output in file ' + buildSqlLogFile) 

    #build & run SQL
    if continueWork:
        buildAndProcess("appBuild", buildConfigData, buildSqlFile, buildSqlLogFile)
        if processSQL == "b":
            appBuildResult = execSQL("appBuild", buildConfigData, installConfigData, buildSqlFile, buildSqlLogFile, True) 
            if appBuildResult[0] == "False":
                continueWork = False
                stopReason = "The build process has stopped because of errors encountered building the application in the database"

    processModifiedOnly = False
  
        
        
    

    #do dataUpgrade installation if necessary
    #include the creation of a dbLog

    #do data update if necessary
    #do dbLog if requested

    #execute sql

    #perform post-processing
    # we only check for the first letter
    # n = no; y = yes
    currentBuildPhase = "postprocess"
    doPostProcess = (doPostProcessVal[:1].lower() == "y")
    
    if writeLog:
        writeOutputFile(logFile, 'doPostProcess: ' + str(doPostProcess))

    if doPostProcess and continueWork:
        buildAndProcess('postprocess', buildConfigData)

    currentBuildPhase = "done"
    #cleanup older files
    keepSQLFiles = (buildSqlFile)
    #to-do: Keep all SQL files executed in this session, delete all others...
    deleteFiles("", "-exec.agsql", keepSQLFiles)
    keepLogFiles = (logFile, testSqlLogFile, instalSqlLogFile, buildSqlLogFile)
    deleteFiles("", "-agbuild.log", keepLogFiles)
    

    #update history
    if continueWork:
        #Write to history File
        historyFile["lastRun"]["timeStamp"] = str(_buildts.strftime("%Y-%m-%d %H:%M:%S"))
        #change this when it is parameterised
        historyFile["lastRun"]["configFile"] = "agBuildConfig.json"
        historyFile["history"]["agBuildConfig"] = str(_buildts.strftime("%Y-%m-%d %H:%M:%S"))
        
        with open(".agBuild.history", "w") as agHistory:
            json.dump(historyFile, agHistory, indent=4)

    
    #finalise log file and finish dbLog
    if writeLog:
        if continueWork == False:
            writeOutputFile(logFile, '\n' + stopReason + '\n')
            
        writeOutputFile(logFile, 'Build complete at : ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        writeOutputFile(logFile, 'This log file ' + logFile + ' will be deleted next time any build process is run\n' + r"Any file ending in '*-agbuild.log' will be deleted, so rename to keep it before next build")
        printFile = open(logFile, "r")
        printText = printFile.read()
        print(printText)
        printFile.close()
    else:
        if continueWork == False:
            print('***************** Process did not end properly due to an error encountered *****************\n')
            print(stopReason + '\n')
            print('********************************************************************************************\n')
        else:
            print('Build process completed properly without major errors\n')

        print('appGoo Build complete.\nParameters:\n\tInstall App:        ' + str(doInstall) + '\n\tDo Pre-Processing:  ' + str(doPreProcess) + '\n\tDo Post-Processing: ' + str(doPostProcess))
        print('You can review the following files that will be deleted by the next build:')
        print('\t' + buildSqlFile)
        for file in keepLogFiles:
              print('\t' + file)
        print('Note that the SQL output and any log files you request are deleted by the next successful build run unless you rename them')
        print('Start Time:      ' + str(_buildts.strftime("%Y-%m-%d %H:%M:%S")) + '\nCompletion Time: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))





################################################################################
#
# This is required for when the program is executed from the command line
#
################################################################################

if __name__ == "__main__":
    main()


