#!/usr/bin/python3
# coding: utf-8

import glob
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os

# ParseStar function taken from PyEM, slightly modified to work with model.star files containing multiple tables


def parseStar(starFile, tableName, keep_index=False, augment=False):
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
    s = model.split("it")
    it = int(s[1][0:3])
    if s[0].startswith("run_ct"):
        it += 1
    return it


def plotDF(df, legend, xlabel, ylabel, title, absMax, absMin, yMaxBuffer=0.1, yMinBuffer=0.1):
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

# Use the runJob file to determine the number of classes without having to iterate through the whole data.star file


def main():
    """
    Parsing the path of the job folder
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    parser.add_argument(
        '-i', dest='i', action='store_true', help='Show the interactive form of the graphs in addition to saving to a PDF.')
    parser.add_argument(
        '-r', dest='r', action='store_true', help='Render images using Chimera raytracing')
    args = parser.parse_args()
    path = args.path[0]

    """
    Doing some tricks to get the path to the directory 
    that the script is acting on so we can use it to name the .pdf
    """
    curr = os.getcwd()
    os.chdir(path)
    new = os.getcwd()
    os.chdir(curr)
    jobName = new.split("/")
    jobName = jobName[len(jobName)-1]
    print("Parsing run.job file")
    try:
        runJob = glob.glob(path + "/run.job")[0]
    except:
        print("ERROR: Could not find a run.job file")
        print()

    numClasses = 0
    micrographs = 0
    min = 1
    max = 0
    with open(runJob, "r") as f:
        for l in f:
            if l.startswith("Number of classes"):
                numClasses = (int)(l.split("== ")[1])

    """
    Here we iterate through the model.star files, reading the data we want into PANDAS data frames
    So far I'm taking the class distribution data and the estimated resolution data
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

    """
    Setting up the tables to be graphed
    """
    headers = []
    legend = ''
    for i in range(numClasses):
        headers.append("class" + str(i))
        legend += str(i+1)
    cd.columns = headers
    rs.columns = headers
    pp = PdfPages(jobName + '.pdf')

    """
    Outputting to the PDF
    """
    print("Saving graphs to PDF")
    os.chdir(new)
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

    # If the -i flag was input, show the plots in python
    if(args.i):
        plotDF(cd, legend, "Iteration", "Distribution",
               "Class Distributions", 1, 0, .05, .02)
        plotDF(rs, legend, "Iteration", "Resolution",
               "Class Resolution", None, 0, 10, 10)
        plotDF(ar, legend, "Iteration", "Accuracy",
               "Accuracy Rotations (Degrees)", None, 0, 1, 1)
        plotDF(at, legend, "Iteration", "Accuracy",
               "Accuracy Translations (Pixels)", None, 0, 1, 1)
        plt.show()

    """
    Making images in Chimera
    """
    chimera = "/Applications/Chimera.app/Contents/MacOS/chimera"
    #This works
    if(args.r):
        print("arrr")
        os.system(chimera + " --script " +"\"" +  curr + "/chimeraScript.py -r " + curr +"/" + path + "\"")
    else:
        os.system(chimera + " --script " +"\"" +  curr + "/chimeraScript.py " + curr +"/" + path + "\"")

    """
    Returning to starting directory and opening the pdf
    """    
    os.chdir(curr)
    os.system('open ' + jobName + '.pdf')
    print("Finished")
    


main()
# TODO:
# Chimera stuff:
#   -Make it output the images to a subdirectory of where we are when we run the script
#   -Make sure it works on linux with just the chimera command, here I have the path to chimera hard coded
#       because I'm running it on my mac.
#   -Tweak the settings of chimera renderer to make it look nice and how I want
#   -Try to set up the classReport so it doesn't crash if chimera is not installed, but will throw an
#       informative exception saying chimera needs to be installed for the image part to work.
#   -See if headless chimera is isntalled, if I can look for it and if it is there use it rather than the gui version.
#   -See if I can integrate the chimeraScript.py into this file, and only execute it if there is a flag which I will call from the main method.
# Make it work for other job types (2d class, refine, etc)
#Maybe make an auto ffmpeg command, at least do a try, except
