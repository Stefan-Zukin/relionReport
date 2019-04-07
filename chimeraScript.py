from chimera import runCommand as rc
from chimera import replyobj
import argparse
import os

"""
Parse the path of the target directory which is given as an argument to the script
"""


def parsePath():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    args = parser.parse_args()
    path = args.path[0]
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
        if(iterations.__contains__(it)):
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
        rc("copy file " + png_name + " supersample 3")
        rc("close all")
    #rc("stop now")


def main():
    path = parsePath()
    iterations = readMRCs(path)
    chimeraRender(iterations)

main()
