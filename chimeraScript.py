#from chimera import runCommand as rc
#from chimera import replyobj
import argparse
import os


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
        print(iterations[k])
        iterations[k].sort(key=sortClasses)
    print()
    for k in iterations.keys():
        print(iterations[k])
    print()
    return iterations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    args = parser.parse_args()
    path = args.path[0]


    readMRCs("/Users/stefanzukin/Desktop/Programming/Python/classReport/test")

    # os.chdir(path)
    os.chdir("/Users/stefanzukin/Desktop/Programming/Python/classReport/test")

    # for fn in mrcs:

    #replyobj.status("Processing " + fn)
    #rc("open " + fn)
    # rc("tile")
    #rc("close all")

    #rc("copy file testy.jpg jpeg")

    # Close chimera
    #rc("stop now")
main()
