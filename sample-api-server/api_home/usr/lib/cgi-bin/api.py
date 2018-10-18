#!/usr/bin/python3
import os
import sys
import cgi
import cgitb
import json
import datetime
from datetime import datetime
cgitb.enable(display=0, logdir="/var/log/apache2", format="text")

## demoMode auto-rotates through the api states with each GET from API Gateway
demoMode = True
## set testFailure to True to simulate a scaling failure (only works with demoMode)
testFailure = False 
## set debugOn to True to enable a full request payload dump to debugLogFile
debugOn = False 

## logs api calls and state changes
logFileName = "/var/log/apache2/api-"+datetime.now().strftime("%Y%m%d")
debugLogFile = "/var/log/apache2/debug"+datetime.now().strftime("%Y%m%d-%H%M%S.%f")
global dimensionId

## defines directory for state files
global stateDir
stateDir = "/var/www/state/"

## Finds the dimensionId by looking for the first string in following */v1/scalableTargetDimensions/*
## Auto-creates a state file if none exists for the dimensionId
def manage_state_file():
    global stateDir
    global dimensionId
    lastIteration = False
    uriPath = os.environ["QUERY_STRING"].split("/")
    for pathPart in uriPath:
        if lastIteration:
            dimensionId = pathPart
            break
        if pathPart == "scalableTargetDimensions":
            lastIteration = True
    if not os.path.isfile(stateDir+dimensionId):
        stateBody = '''{"scalingStatus": "Successful", "version": "MyVersion", 
        "resourceName": "MyService", "dimensionName": "MyDimension", 
        "actualCapacity": 1.0, "desiredCapacity": 1.0, "scalableTargetDimensionId": "100"}'''
        stateDict = json.loads(stateBody) 
        stateDict["scalableTargetDimensionId"] = dimensionId 
        stateFile = open(stateDir+dimensionId , "w")
        stateFile.write(json.dumps(stateDict))
        stateFile.close()

def read_state():
    global dimensionId
    global stateDir
    stateFile = open(stateDir+dimensionId , "r")
    currentState = json.loads(stateFile.read())
    stateFile.close()
    return(currentState)

def write_state(currentState):
    global dimensionId
    global stateDir
    stateFile = open(stateDir+dimensionId , "w")
    stateFile.write(json.dumps(currentState))
    stateFile.close()
    return()

def auto_increment_state(currentState,bodyData):
    if bodyData and currentState["desiredCapacity"] != bodyData["desiredCapacity"]:
        # Response to initial scaling request
        currentState["desiredCapacity"] = bodyData["desiredCapacity"]
        currentState["scalingStatus"] = "Pending"
    else:
        if currentState["scalingStatus"] == "Pending":
            currentState["scalingStatus"] = "InProgress"
        elif testFailure and (currentState["scalingStatus"] == "InProgress" or currentState["scalingStatus"] == "Failed"):
            currentState["scalingStatus"] = "Failed"
        else:
            currentState["actualCapacity"] = currentState["desiredCapacity"]
            currentState["scalingStatus"] = "Successful"
    return(currentState)

def patch_state(currentState,bodyData):
    if "actualCapacity" in bodyData:
        currentState["actualCapacity"] = bodyData["actualCapacity"]
    if "desiredCapacity" in bodyData:
        currentState["desiredCapacity"] = bodyData["desiredCapacity"]
    if "scalingStatus" in bodyData:
        currentState["scalingStatus"] = bodyData["scalingStatus"]
    return(currentState)

def end_routine(currentState):
    global previousState
    write_state(currentState)
    print("Content-type: application/json\n\n")
    print(json.dumps(currentState))
    logResponse = ""
    if previousState["desiredCapacity"] != currentState["desiredCapacity"]:
        logResponse += "desiredCapacity: " + str(previousState["desiredCapacity"]) + " -> " + str(currentState["desiredCapacity"]) + "  "
    if previousState["actualCapacity"] != currentState["actualCapacity"]:
        logResponse += "actualCapacity: " + str(previousState["actualCapacity"]) + " -> " + str(currentState["actualCapacity"]) + "  "
    if previousState["scalingStatus"] != currentState["scalingStatus"]:
        logResponse += "scalingStatus: " + previousState["scalingStatus"] + " -> " + currentState["scalingStatus"] 
    if not logResponse:
        logResponse += "actualCapacity: " + str(currentState["actualCapacity"]) + " = desiredCapacity: " + str(currentState["desiredCapacity"]) + "  "
    if bodyData:
        bodyOut = json.dumps(bodyData)
    else:
        bodyOut = ""
    logData = datetime.now().strftime("%Y%m%d-%H%M%S") + " Request: " + os.environ["REQUEST_METHOD"] + " dimensionId: " + dimensionId +" "  + bodyOut + "\n"
    logData += datetime.now().strftime("%Y%m%d-%H%M%S") + " Response: dimensionId: " + dimensionId + "  " + logResponse  + "\n"
    logFile = open(logFileName , "a")
    logFile.write(logData)
    logFile.close()
    if debugOn:
        debugLog = open(debugLogFile, "a")
        for param in os.environ.keys():
            debugLog.write(str(param) + " " + str(os.environ[param]) + "\n")
        debugLog.write(json.dumps(bodyData)+"\n")
        debugLog.close()
    exit() 

### Main script logic
bodyData = None
manage_state_file()
currentState = read_state()
global previousState
previousState = dict(currentState)
## Grab body from PATCH
if "CONTENT_LENGTH" in os.environ:
    contentLength = int(os.environ["CONTENT_LENGTH"])
    bodyData = json.loads(sys.stdin.read(contentLength))
if bodyData and os.environ["REQUEST_METHOD"] == 'PATCH':
    if demoMode:
        ## For desiredCapacity change, auto-set status to pending.
        if (bodyData["desiredCapacity"]) != (currentState["desiredCapacity"]):
            currentState = auto_increment_state(currentState, bodyData)
            end_routine(currentState)
        else:
            end_routine(currentState)
    else:
        ## For desiredCapacity change, auto-set status to pending.
        if "desiredCapacity" in bodyData and (bodyData["desiredCapacity"] != currentState["desiredCapacity"]):
            bodyData["scalingStatus"] = "Pending"
        currentState = patch_state(currentState, bodyData)
        end_routine(currentState)
elif os.environ["REQUEST_METHOD"] == 'GET':
    if demoMode:
        ## GET in demoMode causes the script to auto-increment stats forward
        if (currentState["scalingStatus"] == "Successful"):
            end_routine(currentState)
        else:
            currentState = auto_increment_state(currentState, bodyData)
            end_routine(currentState)
    else:
        end_routine(currentState)
else:
    print("Status: 405 Method Not Allowed\n")

