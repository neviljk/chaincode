# Create Freeman chaincodes from input feature classes
# Ver 0.3

# Imports
import arcpy
from math import ceil, floor, atan, sin, cos, radians, pi
import numpy as np
import time
import copy

start_time = time.time()

# Class that simulates a fishnet grid over the feature
class Fishnet:
    def __init__(self, extent, resolution):
        self.extent = extent
        self.xres = resolution
        self.yres = resolution
        self.cols = int(ceil((extent.XMax - extent.XMin) / self.xres))
        self.rows = int(ceil((extent.YMax - extent.YMin) / self.yres))

    # Converts projected coordinate (meters) to row, col in the fishnet
    def getRowCol(self, x, y):
        sr = self.rows - floor((y - self.extent.YMin) / self.yres) - 1
        sc = floor((x - self.extent.XMin) / self.xres)
        return int(sr),int(sc)

    # Returns the Freeman chaincode representation of polyline
    def getChainCode(self,polyline):
        code2 = {(0, 1): 0, (-1, 1): 1, (-1, 0): 2, (-1, -1): 3, (0, -1): 4, (1, 0): 6, (1, -1): 5, (1, 1): 7}
        # code2 is dictionary that maps a tuple (dr,dc) to one of the eight chaincode values
        # dr is the difference between current and previous row
        # dc is the difference between current and previous column

        res = self.xres
        chaincode = ''
        length = polyline.length

        firstPoint = True
        for dist in np.arange(0, length, res/2.):
            pg = polyline.positionAlongLine(dist)
            sr, sc = self.getRowCol(pg.firstPoint.X, pg.firstPoint.Y)

            if (firstPoint):
                prev_r,prev_c = sr,sc
                firstPoint = False
            else:
                if (prev_r == sr and prev_c == sc):
                    pass # No change in row, col. Ignore
                else:
                    # Compute the chain code by comparing the current row, col with the last
                    dr, dc = sr - prev_r, sc - prev_c
                    chaincode += str(code2[dr,dc])
                    prev_r, prev_c = sr, sc
        return chaincode

def completePath(workspace, subdir, nameList):
  for ix in range(len(nameList)):
    nameList[ix] = workspace + '/' + subdir + '/' + nameList[ix]
  return nameList

def controlExtension(inName, ext):
  if (inName.find(".") > 0):
    inName = inName.split(".",1)[0] + ext
  else:
    inName = inName + ext
  return inName

# Compute the angle between the sPnt and cPnt
def getOrient(sPnt, cPnt):
  pnt0 = sPnt
  pnt1 = cPnt

  if abs(pnt1[0]-pnt0[0]) < 0.00001:
    rad = pi/2
  else:
    rad = atan( ( pnt1[1]-pnt0[1] )  / ( pnt1[0]-pnt0[0] ) )
  return rad * 180./pi

def RotateXY(x, y, xc=0, yc=0, angle=0):
    """Rotate an xy co-oordinate about a specified origin
    x,y      xy coordinates
    xc,yc   center of rotation
    angle   angle in degrees
    """
    x = x - xc
    y = y - yc
    angle = angle * -1
    angle = radians(angle)
    xr = (x * cos(angle)) - (y * sin(angle)) + xc
    yr = (x * sin(angle)) + (y * cos(angle)) + yc
    return xr, yr

def rotatePolyLines(inFC):
    """Rotates each polylines in the input feature class by
    the respective angle between their start and endpoints."""
    fieldList = ["SHAPE@"]
    with arcpy.da.UpdateCursor(inFC, fieldList) as cur:
        for row in cur:
            startPoint = (row[0].firstPoint.X, row[0].firstPoint.Y)
            endPoint = (row[0].lastPoint.X, row[0].lastPoint.Y)
            angle = getOrient(startPoint, endPoint)
            verts = []
            for part in row[0]:
                for pnt in part:
                    x, y = RotateXY(pnt.X, pnt.Y, row[0].firstPoint.X, row[0].firstPoint.Y, angle)
                    pnt.X = x
                    pnt.Y = y
                    verts.append(pnt)
            row[0]=arcpy.Polyline(arcpy.Array(verts))
            cur.updateRow(row)
    del cur

# Iterates over each feature in the input shapefile, and generates chaincodes at different resolutions
def getAllChainCodes(inFC, resolutions):
    fieldList = ["SHAPE@", "OID@"]

    test = {}
    with arcpy.da.SearchCursor(inFC, fieldList) as cur:
        for row in cur:
            arcpy.AddMessage("Creating Chaincodes for FID: " + str(row[1]))
            extent = row[0].extent
            fid = row[1]
            code = {}
            for res in resolutions:
                f = Fishnet(extent, res)
                chaincode = f.getChainCode(row[0])
                code[res] = chaincode

            test[fid] = { "code":  copy.deepcopy(code) }
    del cur
    return test

def checkExistence(path):
    if arcpy.Exists(path):
      return True
    else:
        return False

arcpy.env.overwriteOutput = True

# Get the workspace
workspace = arcpy.GetParameterAsText(0)

# Get the Reference FC
refFCName = arcpy.GetParameterAsText(1)
refFC = completePath(workspace, "shape", [refFCName])[0]
refFC = controlExtension(refFC,".shp")

# Get the Test FC
testFCName = arcpy.GetParameterAsText(2)
testFC = completePath(workspace, "shape", [testFCName])[0]
testFC = controlExtension(testFC,".shp")

# Temp FC
tmpFCName = "inp_copy.shp"
tmpFC = completePath(workspace, "temp", [tmpFCName])[0]

# Result File
resultName = arcpy.GetParameterAsText(3)
resultFile = completePath(workspace, "result", [resultName])[0]
resultFile = controlExtension(resultFile,".txt")

 # Make a copy of the ref FC
arcpy.CopyFeatures_management(refFC, tmpFC)

# Rotate all the polylines in the ref FC copy
rotatePolyLines(tmpFC)

# Generate Chaincodes
arcpy.AddMessage("Creating chaincodes of the reference shapefile")

# The required resolutions of the chaincode
resolutions = [50,100,200,500, 1000]
refCodes = getAllChainCodes(tmpFC, resolutions)

# Make a copy of the test FC
arcpy.CopyFeatures_management(testFC, tmpFC)

# Rotate all the polylines in the test FC copy
rotatePolyLines(tmpFC)

# Generate Chaincodes
arcpy.AddMessage("Creating chaincodes of the test shapefile")
testCodes = getAllChainCodes(tmpFC, resolutions)

arcpy.AddMessage( "Total execution time %.3fs" % (time.time() - start_time))
