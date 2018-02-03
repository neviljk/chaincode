# For rotation through the array and for the duplicate number function.
from collections import Counter

import arcpy

# For moving average...
import numpy as np

# Required to output it into a pretty textfile.
import datetime
import prettytable

# Helper Functions
def returnTestName (dictionaryName, array, resolution):
    # If the count is 2, return the second one, if there is already one there.
    for k in dictionaryName.keys():
        if dictionaryName[k]['code'][resolution] == array:
            return k

# Returns a result based if there is a possibility of a duplicate.
def returnTestNameNumber (dictionaryName, array, resolution,number):
    resultArray=[];
    for k in dictionaryName.keys():
        if dictionaryName[k]['code'][resolution] == array:
            resultArray.append(k)
    return  resultArray[number]

def arrayOfTestAtResolution(dictionaryName, resolution):
    array = []
    for key in dictionaryName:
        internalArrayName = (dictionaryName[key]['code'][resolution])
        internalArraySplit = list(internalArrayName)
        integerArray = [int(x) for x in internalArraySplit]
        array.append(integerArray)
    return array

def outputReference(dictionaryName,resolution, fileName=False):
    if fileName == True:
        return  dictionaryName['filename']
    string= (dictionaryName['code'][resolution])
    stringToArray = list(string)
    arrayToInt = [int(x) for x in stringToArray]
    return arrayToInt

def arrayToString (array):
    toString = [str(x) for x in array]
    stringArray = "".join(toString)

    return stringArray

# Duplicate Numbers function from http://stackoverflow.com/questions/4775004/count-duplicates-between-2-lists

def duplicateNumbers(a, b):
    if len(a)>len(b):
        a,b = b,a
    a_count = Counter(a)
    b_count = Counter(b)
    return sum(min(b_count[ak], av) for ak,av in a_count.items())

# Used to output the chaincode as a series of cells.
cellCreationDictionary = {0: {'x': 1, 'y':0}, 1: {'x': 1, 'y':1}, 2: {'x': 0, 'y':1}, 3: {'x': -1, 'y':1}, 4: {'x': -1, 'y':0}, 5: {'x': -1, 'y':-1}, 6: {'x': 0, 'y':-1}, 7: {'x': 1, 'y':-1}}

def outPutCells(pattern):
    allOutPutCells = []
    x = 0
    y = 0
    newCell = str([x,y])
    allOutPutCells.append(newCell)
    for number in pattern:
        number = int(number)
        x = x + cellCreationDictionary[number]['x']
        y = y + cellCreationDictionary[number]['y']
        newCell = str([x,y])
        allOutPutCells.append(newCell)
    return allOutPutCells
# Output the comparison value between two patterns. Comparison Algorithm. 
def outputScore (patternOne, patternTwo):
    maxLengthPOnePTwo = max(len(patternOne), len(patternTwo))
    patternOneCells = outPutCells(patternOne)
    patternTwoCells = outPutCells(patternTwo)
    numberCommonCells = duplicateNumbers(patternOneCells, patternTwoCells)
    comparisonValue = numberCommonCells / float(maxLengthPOnePTwo)
    return comparisonValue


def allOutputFunction(allArrays, referenceArray, filehandle, resolution):
    f = filehandle

    allOutputArray = list()
    # To print the output
    table = prettytable.PrettyTable(["Test Name", " Similarity Score*", "Length of Array"])
    # If string is duplicate push it there. Return not the first but the nth result.
    stringArrayArray = list()
    for array in allArrays:
        stringArray = arrayToString(array)
        duplicateStringNumber= stringArrayArray.count(stringArray)
        stringArrayArray.append(stringArray)
        chainCodeName = returnTestNameNumber(testPatternDictionary, stringArray, resolution,duplicateStringNumber)
        thisOutputScore = outputScore(array, referenceArray)
        stringOutputScore = str(round(thisOutputScore,5))
        table.add_row([chainCodeName, stringOutputScore, str(len(array))])
        allOutputArray.append(thisOutputScore)
    sortedTable= table.get_string(sortby="Test Name")
    f.write(sortedTable)
    f.write('\n')
    return allOutputArray

def printResults(allTestArray, realArray,resolution, filehandle):
    f = filehandle
    f.write("Resolution " + str(resolution) + "m" +'\n \n')
    allOutputArray= allOutputFunction(allTestArray, realArray, filehandle, resolution)
    if allOutputArray == []:
        f.write("At Resolution " + resolution + " Program stopped \n \n")
        return
    largestNumberIndex = allOutputArray.index(max(allOutputArray))
    arrayWithLargestValue= allTestArray[largestNumberIndex]
    nameOfArrayWithLargestValue = returnTestName(testPatternDictionary, arrayToString(arrayWithLargestValue), resolution)
    f.write("The most similar array at {} resolution is {} with a similarity score of {} \n \n ".format(resolution,nameOfArrayWithLargestValue,round(max(allOutputArray),4 )))
    resultsDictionary[resolution] = {'name': nameOfArrayWithLargestValue, 'value': max(allOutputArray)}
def createResult(resolution, testPatternDictionary, referenceDictionary , filehandle):
    allPatterns = arrayOfTestAtResolution(testPatternDictionary,resolution)
    realPattern = outputReference(referenceDictionary,resolution)
    printResults(allPatterns, realPattern, resolution, filehandle)

## Execute Program.

def performComparison(filename, testDict, refDict ):
    global testPatternDictionary
    global referenceDictionary
    global resultsDictionary
    resultsDictionary = dict()
    testPatternDictionary = testDict
    referenceDictionary = refDict

    f = open(filename,"w")
    f.write("OVERVIEW \n \n")
    now = datetime.datetime.now()
    f.write("Created on " + now.strftime("%d/%m/%Y")+ " at " + now.strftime("%H:%M") + "\n \n")
    # Create result with only the resolutions in the reference file.
    for x in sorted(referenceDictionary['code']):
        createResult(x, testPatternDictionary, referenceDictionary, f)

    ## Printing Results Table
    fullResultstable = prettytable.PrettyTable(["Resolution", "Best Fit", "Value"])
    for res in resultsDictionary:
        name = (resultsDictionary[res]['name'])
        value = (resultsDictionary[res]['value'])
        fullResultstable.add_row([res, str(name), str(round(value, 5))])
    sortedTable = fullResultstable.get_string(sortby="Resolution")
    f.write("SUMMARY OF RESULTS \n \n")
    f.write(sortedTable)


    f.write("\n \n * number of numbers common to both reference and test  / max(len(reference), len(test)) . \n \n")
    f.close()
    arcpy.AddMessage("Program completed. Output can be found in the file: " + filename)

