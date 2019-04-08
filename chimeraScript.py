from chimera import runCommand as rc
from chimera import replyobj
import argparse
import os
import sys

"""
Parse the path of the target directory which is given as an argument to the script
"""
raytrace = False
flat = False
highRes = False

def parsePath():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    parser.add_argument(
        '-r', dest='r', action='store_true', help='Render images using Chimera raytracing')
    parser.add_argument(
        '-f', dest='f', action='store_true', help='Render the images as flat, without shadows or highlights')
    parser.add_argument(
        '-hr', dest='hr', action='store_true', help='Render higher resolution images. Will make the process slower.')
    args = parser.parse_args()
    path = args.path[0]
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
    for it in iterations.keys():
        modelNum = 0
        for c in iterations[it]:
            replyobj.status("Processing " + c)
            rc("open " + c)
            rc("volume #" + str(modelNum) + " sdlevel 7")
            rc("volume #" + str(modelNum) + " step 1")
            modelNum += 1
        rc("tile")
        rc("preset apply publication 1")
        num = str(it)
        while len(num) < 4:
            num = "0" + num
        png_name = "it" + num + ".png"
        os.system("echo Rendering iteration " + str(it))
        rc("lighting contrast .7")
        rc("lighting sharpness 100")
        rc("lighting reflectivity .8")
        rc("lighting brightness 1.1")
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
        rc("close all")
    rc("stop now")


def main():
    path = parsePath()
    iterations = readMRCs(path)
    chimeraRender(iterations)

main()
