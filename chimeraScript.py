from chimera import runCommand as rc
from chimera import replyobj
import argparse
import os
import sys
import subprocess
from datetime import datetime

"""
Parse the path of the target directory which is given as an argument to the script
"""
raytrace = False
flat = False
highRes = False
path = ""
output = ""

def parsePath():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory containing the micrographs')
    parser.add_argument(
        'output', nargs=1, help='the path of the directory for the output')
    parser.add_argument(
        '-r', dest='r', action='store_true', help='Render images using Chimera raytracing')
    parser.add_argument(
        '-f', dest='f', action='store_true', help='Render the images as flat, without shadows or highlights')
    parser.add_argument(
        '-hr', dest='hr', action='store_true', help='Render higher resolution images. Will make the process slower.')
    args = parser.parse_args()
    global output
    path = args.path[0]
    output = args.output[0] + "/chimeraImages"
    try:
        os.mkdir(output)
    except:
        print('')
    if(args.r):
        global raytrace
        raytrace = True
    if(args.f):
        global flat
        flat = True
    if(args.hr):
        global highRes
        highRes = True
    return path


"""
Sorting method to sort by mrc iteration number
"""


def sortMrcs(model=" "):
    s = model.split("it")
    it = int(s[1][0:3])
    if s[0].startswith("run_ct"):
        it += 1
    return it


"""
Sorting method to sort by mrc class number
"""


def sortClasses(model=" "):
    s = model.split("class")
    classNum = int(s[1][0:3])
    return classNum


"""
Goes to the directory given in path, then reads in all the .mrc files
Iterates over the read MRCs, organizing them by iteration number and class number.
Returns a dictionary where the keys are the iterations in order, and the item is a list
with the classes for that iteration in order
"""


def readMRCs(path):
    os.chdir(path)
    mrcs = [fn for fn in os.listdir(".") if fn.endswith(".mrc")]
    mrcs.sort(key=sortMrcs)
    iterations = {}
    for fn in mrcs:
        s = fn.split("it")
        it = int(s[1][0:3])
        if s[0].startswith("run_ct"):
            it += 1
        if(it in iterations):
            iterations[it] = iterations[it] + [fn]
        else:
            iterations[it] = [fn]
    for k in iterations.keys():
        iterations[k].sort(key=sortClasses)
    # for k in iterations.keys():
    #     print(iterations[k])
    return iterations


"""
This function contains all the interactions with chimera
Loads the mrcs and prints out the image files
"""


def chimeraRender(iterations):
    global path
    finalIt = 0
    for it in iterations.keys():
        modelNum = 0
        rc("cd " + path)
        for c in iterations[it]:
            rc("open " + c)
            rc("volume #" + str(modelNum) + " sdlevel 7")
            rc("volume #" + str(modelNum) + " step 1")
            modelNum += 1
        rc("tile")
        rc("preset apply publication 1")
        num = str(it)
        while len(num) < 4:
            num = "0" + num
        png_name = "frame" + num + ".png"
        subprocess.call("echo \"Rendering iteration " + str(it) + " at " + datetime.now().strftime('%H:%M:%S') + "\"", shell=True)
        rc("cd " + output)
        saveImage(png_name, raytrace, flat, highRes)
        finalIt = it

    #Spin with the final iteration
    modelNum = 0
    subprocess.call("echo \"Rendering final spin at " + datetime.now().strftime('%H:%M:%S') + "\"", shell=True)
    rc("cd " + path)
    for c in iterations[finalIt]:
            rc("open " + c)
            rc("volume #" + str(modelNum) + " sdlevel 7")
            rc("volume #" + str(modelNum) + " step 1")
            modelNum += 1
    rc("tile")
    rc("preset apply publication 1")
    rc("window")
    for x in range(90):
        rc("turn y 4 model #0-" + str(modelNum))
        num = str(finalIt + 1 + x) 
        while len(num) < 4:
                num = "0" + num
        png_name = "frame" + num + ".png"
        rc("cd " + output)
        saveImage(png_name, raytrace, flat, highRes, False, False)
    rc("stop now")

def saveImage(png_name, raytrace, flat, highRes, closeModelsAfterSaving=True, autoFitWindow=True):
    rc("lighting contrast .7")
    rc("lighting sharpness 100")
    rc("lighting reflectivity .8")
    rc("lighting brightness 1.1")
    if autoFitWindow:
        rc("window")
    if raytrace:
        rc("lighting reflectivity .8")
        rc("lighting brightness 0.85")
        if(highRes):
            rc("copy file " + png_name + " supersample 4 raytrace rtwait rtclean width 16  height 16 dpi 128 units inches")
        else:
            rc("copy file " + png_name + " supersample 4 raytrace rtwait rtclean width 8 height 8 dpi 128 units inches")
    else:
        if(flat):
            rc("lighting mode ambient")
            rc("set silhouetteWidth 8")
        else:
            rc("lighting mode two-point")
            rc("set silhouetteWidth 4")
        if(highRes):
            rc("copy file " + png_name + " supersample 4 width 16 height 16 dpi 128 units inches")
        else:
            rc("copy file " + png_name + " supersample 4 width 8 height 8 dpi 128 units inches")
    if closeModelsAfterSaving:
        rc("close all")


def main():
    global path
    path = parsePath()
    iterations = readMRCs(path)
    chimeraRender(iterations)

main()
