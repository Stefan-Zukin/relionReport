#!/usr/bin/python3
# coding: utf-8

import glob
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import subprocess
import sys


"""
Invariants:
    -The path variable should always hold the absolute path to the target directory.
    -The curr variable should always hold the absolute path to the directory from which the script was run.


"""

def parseStar(starFile, tableName, keep_index=False, augment=False):
    """ParseStar function taken from PyEM, slightly modified to work with model.star files containing multiple tables
    Returns a Pandas dataframe with the data from the .star file
    """
    headers = []
    foundTable = False
    foundheader = False
    ln = 0
    lb = 0
    i = 0
    with open(starFile, "r") as f:
        for l in f:
            if(l.startswith(tableName)):
                foundTable = True
            else:
                ln += 1
                if foundheader and not lastheader:
                    # Don't add to skipped line value if I'm reading the data
                    ln -= 1
            if(foundTable):
                if l.startswith("_"):
                    foundheader = True
                    lastheader = True
                    if keep_index:
                        head = l.rstrip()
                    else:
                        head = l.split('#')[0].rstrip().lstrip('_')
                    headers.append(head)
                else:
                    lastheader = False
                if foundheader and not lastheader:
                    # Read through the data to see how long it is, record length in lb
                    # Use this value in the pd.read_csv line
                    if l.startswith(" "):
                        break
                    lb += 1
    df = pd.read_csv(starFile, skiprows=ln,
                     delimiter='\s+', nrows=lb, header=None)
    df.columns = headers
    return df  # A PANDAS data frame object is returned


def sortModelStars(model=" "):
    """Sorting method which sorts model.star files by iteration number
    Important to do this double split, to get only the filename of the .star
    Otherwise had a bug if enclosing folders had 'it" in the name, like /titan/"""
    s = model.split("run_")[1]
    s = s.split("it")
    it = int(s[1][0:3])
    if s[0].startswith("run_ct"):
        it += 1
    return it


def plotDF(df, legend, xlabel, ylabel, title, absMax, absMin, yMaxBuffer=0.1, yMinBuffer=0.1):
    """Generalized function for plotting a PANDAS dataframe"""
    maxDist = df.max(axis=0).max()
    minDist = df.min(axis=0).min()
    ymax = maxDist + yMaxBuffer
    ymin = minDist - yMinBuffer
    if(absMax != None):
        if ymax > absMax:
            ymax = absMax
    if(absMin != None):
        if ymin < absMin:
            ymin = absMin
    df.plot(use_index=True, linewidth=2)
    plt.legend(legend, ncol=2, loc='upper left', title="Classes")
    plt.ylim(ymin, ymax)
    plt.grid(linestyle='-', linewidth=.2)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)


def parseArgs():
    """Parses arguments and returns them as an args object"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    parser.add_argument(
        '-i', dest='i', action='store_true', help='Show the interactive form of the graphs in addition to saving to a PDF.')
    parser.add_argument(
        '-r', dest='r', action='store_true', help='Render images using Chimera raytracing')
    parser.add_argument(
        '-f', dest='f', action='store_true', help='Render images as flat, without shadows or highlights')
    parser.add_argument(
        '-hr', dest='hr', action='store_true', help='Render higher resolution images. Will make the process slower.')
    args = parser.parse_args()
    return args


def parseNumClasses(path):
    """Parse the run.job file. Returns the number of classes"""
    print("Parsing run.job file")
    try:
        runJob = glob.glob(path + "/run.job")[0]
    except:
        print("ERROR: Could not find a run.job file")
        print()

    numClasses = 0
    with open(runJob, "r") as f:
        for l in f:
            if l.startswith("Number of classes"):
                numClasses = (int)(l.split("== ")[1])
    return numClasses


def readModelStars(path):
    """Read the data we want from the dataframe.
    Returns four dictionaries for class distribution, resolution, accuracy rotations and accuracy translations
    The dictionaries map iteration number to a list which contains the values for all of the classes in order.
    """
    print("Parsing model.star files")
    try:
        modelStars = glob.glob(path + '/*model.star')
    except:
        print("ERROR: Could not find a model.star file")
        print()
    modelStars.sort(key=sortModelStars)
    classDict = {}
    resDict = {}
    rotDict = {}
    transDict = {}
    it = 0
    for name in modelStars:
        filename = name
        df = parseStar(filename, "data_model_classes")
        classDist = []
        resolution = []
        accRot = []
        accTrans = []
        for column in df:
            if column == "rlnClassDistribution":
                classDist = list(df[column])
            if column == "rlnEstimatedResolution":
                resolution = list(df[column])
            if column == "rlnAccuracyRotations":
                accRot = list(df[column])
            if column == "rlnAccuracyTranslations":
                accTrans = list(df[column])
        classDict[it] = classDist
        resDict[it] = resolution
        rotDict[it] = accRot
        transDict[it] = accTrans
        it += 1
    cd = pd.DataFrame.from_dict(classDict, orient='index')
    rs = pd.DataFrame.from_dict(resDict, orient='index')
    ar = pd.DataFrame.from_dict(rotDict, orient='index')
    at = pd.DataFrame.from_dict(transDict, orient='index')

    return cd, rs, ar, at


def graphToPDF(cd, rs, ar, at, legend, jobName):
    """Graph the dataframes and save to pdf"""

    pp = PdfPages(jobName + '.pdf')
    print("Saving graphs to PDF")

    # Plot the distribution and save it to the PDF
    plotDF(cd, legend, "Iteration", "Distribution",
           "Class Distributions", 1, 0, .05, .02)
    pp.savefig()
    plt.close()

    # Plot the resolution and save it to the PDF
    plotDF(rs, legend, "Iteration", "Resolution",
           "Class Resolution", None, 0, 10, 10)
    pp.savefig()
    plt.close()

    # Plot the accuray rotations and save it to the PDF
    plotDF(ar, legend, "Iteration", "Accuracy",
           "Accuracy Rotations", None, 0, 1, 1)
    pp.savefig()
    plt.close()

    # Plot the accuray rotations and save it to the PDF
    plotDF(at, legend, "Iteration", "Accuracy",
           "Accuracy Translations", None, 0, 1, 1)
    pp.savefig()
    plt.close()

    # Close the PDF
    pp.close()


def graphInteractive(cd, rs, ar, at, legend):
    """Show othe interactive plots of the data"""

    plotDF(cd, legend, "Iteration", "Distribution",
           "Class Distributions", 1, 0, .05, .02)
    plotDF(rs, legend, "Iteration", "Resolution",
           "Class Resolution", None, 0, 10, 10)
    plotDF(ar, legend, "Iteration", "Accuracy",
           "Accuracy Rotations (Degrees)", None, 0, 1, 1)
    plotDF(at, legend, "Iteration", "Accuracy",
           "Accuracy Translations (Pixels)", None, 0, 1, 1)
    plt.show()


def chimera(path, curr, args):
    """This function does all the work to render images in chimera using chimeraScript.py"""

    print("Rendering images in Chimera")
    # Make sure this variable equal to the full path to your chimera executable.
    chimera = ""
    if sys.platform == "linux" or sys.platform == "linux2":
        # linux
        chimera = "/programs/x86_64-linux/chimera/1.13.1/bin/chimera"
    elif sys.platform == "darwin":
        # OS X
        chimera = "/Applications/Chimera.app/Contents/MacOS/chimera"
    if(args.hr):
        h = "-hr "
    else:
        h = ''
    if args.r:
        subprocess.call(chimera + " --script " + "\"" + curr + "/chimeraScript.py -r " +
                        h + path + " " + curr + "\"", shell=True)
    elif args.f:
        subprocess.call(chimera + " --script " + "\"" + curr + "/chimeraScript.py -f " +
                        h + path + " " + curr + "\"", shell=True)
    else:
        subprocess.call(chimera + " --script " + "\"" + curr + "/chimeraScript.py " +
                        h + path + " " + curr + "\"", shell=True)

    """
    Attempting to render a movie using ffmpeg
    """
    os.chdir(curr + "/chimeraImages")
    try:
        subprocess.call(
            "ffmpeg -r 10 -f image2 -s 1920x1080 -i frame%04d.png -vcodec libx264 -crf 25 -pix_fmt yuv420p movie.mp4", shell=True)
    except:
        print("Rendering frames into movie failed. Check that you have ffmpeg installed")
        print("Try manually running the command from the chimeraImages folder: ffmpeg -r 10 -f image2 -s 1920x1080 -i it%04d.png -vcodec libx264 -crf 25 -pix_fmt yuv420p movie.mp4")


def main():
    """
    Parsing the path of the job folder
    """
    args = parseArgs()
    path = args.path[0]

    """
    Doing some tricks to get the path to the directory 
    that the script is acting on so we can use it to name the .pdf
    """
    curr = os.getcwd()
    os.chdir(path)
    path = os.getcwd()
    os.chdir(curr)
    jobName = path.split("/")
    jobName = jobName[len(jobName)-1]
    numClasses = parseNumClasses(path)

    """
    Read data from model.star dataframes
    """
    cd, rs, ar, at = readModelStars(path)

    """
    Saving graphs to PDF
    """
    legend = ''
    for i in range(numClasses):
        legend += str(i+1)
    os.chdir(curr)
    graphToPDF(cd, rs, ar, at, legend, jobName)

    """
    Making images in Chimera
    """
    chimera(path, curr, args)

    # Uncomment the line below to automatically open the PDF:
    #subprocess.call('xdg-open ' + jobName + '.pdf', shell=True)

    """
    If the -i flag was input, show the plots in python
    """
    if(args.i):
        graphInteractive(cd, rs, ar, at, legend)

    print("Finished")


main()
# TODO:
# Chimera stuff:
#   -Try to set up the classReport so it doesn't crash if chimera is not installed, but will throw an
#       informative exception saying chimera needs to be installed for the image part to work.
#   -See if I can integrate the chimeraScript.py into this file, and only execute it if there is a flag which I will call from the main method.
#	-Currently need to execute the script from the folder it's in or else the chimera script doesn't have the right path
# Make it work for other job types (2d class, refine, etc)
# Put some more things into functions. It will make the code nicer.
