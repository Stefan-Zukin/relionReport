#!/usr/bin/python3
# coding: utf-8

import glob
import argparse
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import subprocess
import sys
import numpy as np
from datetime import datetime


try:
    import pandas as pd
    from IPython.display import display, HTML
    from chimera import runCommand as rc
    from chimera import replyobj
except:
    pass


class starTable():

    def __readModelGeneral(self, starFile):
        """
        This function is a special case to read the ModelGeneral table
        This is necessary because ModelGeneral has different formatting than all the other tables
        in the model.star file. Returns a Pandas dataframe
        """
        dictionary = {}
        foundTable = False
        reading = False
        with open(starFile, "r") as star:
            for line in star:
                if line.startswith(self.tableName):
                    foundTable = True
                if foundTable:
                    if line.startswith("_"):
                        reading = True
                        head = line.split(' ')
                        value = float(head[len(head)-1])
                        head = head[0][1:]
                        dictionary[head] = [value]
                    if reading and line.startswith("\n"):
                        break
        df = pd.DataFrame.from_dict(dictionary)
        return df  # A Pandas data frame object is returned

    def __parseStar(self, starFile):
        """
        Used to read any table from a .star file, other than dataModelGeneral
        Taken from PyEM package. Slightly modified for my use. Returns a Pandas dataframe
        """

        if self.tableName == "data_model_general":
            return self.__readModelGeneral(starFile)
        headers = []
        foundTable = False
        foundheader = False
        ln = 0
        lb = 0
        #print("starFile:", starFile)
        with open(starFile, "r") as star:
            for line in star:
                if line.startswith(self.tableName):
                    foundTable = True
                else:
                    ln += 1
                    if foundheader and not readingHeader:
                        # Don't add to skipped line value if I'm reading the data
                        ln -= 1
                if foundTable:
                    if line.startswith("_"):
                        foundheader = True
                        readingHeader = True
                        head = line.split('#')[0].rstrip().lstrip('_')
                        headers.append(head)
                    else:
                        readingHeader = False
                    if foundheader and not readingHeader:
                        # Read through the data to see how long it is, record length in lb
                        # Use this value in the pd.read_csv line
                        if line.startswith("\n"):
                            lb -= 1
                            break
                        lb += 1
        df = pd.read_csv(starFile, skiprows=ln,
                         delimiter='\s+', nrows=lb, header=None)
        df.columns = headers
        return df  # A PANDAS data frame object is returned

    def graph(self, parameter):
        paramTable = self.table[parameter]
        paramTable.unstack().plot(kind='line')

    def __init__(self, starFiles, tableName):
        self.starFiles = starFiles
        self.tableName = tableName
        iterations = {}
        it = 0
        for s in starFiles:
            df = self.__parseStar(s)
            df.index.name = "class"
            iterations[it] = df
            it += 1
        self.table = pd.concat(iterations.values(),
                               axis=0, keys=iterations.keys())
        self.table.to_html("meta.html")
        # for i in self.table.keys():
        # print(i)
        # self.table.unstack()
        # self.table.to_html("met1.html")
        # print(self.table)
        #self.df = self.__parseStar()
        #resolutions = self.table["rlnClassDistribution"]
        # print(self.table["rlnEstimatedResolution"][0])
        # resolutions.unstack().plot(kind='line')
        # plt.show()
        # print(p)


class relionJob():
    tables = []
    parameters = []

    def __sortModelStars(self, model=" "):
        """Sorting method which sorts model.star files by iteration number
        Important to do this double split, to get only the filename of the .star
        Otherwise had a bug if enclosing folders had 'it" in the name, like /titan/"""
        s = model.split("run_")[1]
        s = s.split("it")
        it = int(s[1][0:3])
        if s[0].startswith("run_ct"):
            it += 1
        return it

    def __readModelStars(self):
        #print("Parsing model.star files")
        modelStars = glob.glob(self.path + '/*model.star')
        if len(modelStars) == 0:
            raise Exception("ERROR: Could not find a model.star file")
        modelStars.sort(key=self.__sortModelStars)
        return modelStars

    def __getJobName(self):
        split = self.path.split("/")
        return split[len(split)-1]

    def read(self, tableName):
        table = starTable(self.modelStars, tableName)
        self.tables.append(table)

    def graph(self):
        for t in self.tables:
            for p in self.parameters:
                print(p)
                t.graph(p)
        plt.show()

    def graphToPDF(self):
        pp = PdfPages(self.jobName + '.pdf')
        print("Saving graphs as " + self.jobName + ".pdf")
        for t in self.tables:
            for p in self.parameters:
                t.graph(p)
                pp.savefig()
                plt.close()
        pp.close()

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.jobName = self.__getJobName()
        self.modelStars = self.__readModelStars()


class class3D(relionJob):

    def __addParameters(self):
        self.parameters.append("rlnClassDistribution")
        self.parameters.append("rlnEstimatedResolution")
        self.parameters.append("rlnAccuracyRotations")
        self.parameters.append("rlnAccuracyTranslations")

    def getTable(self):
        # If we have the starTable, return it, if not parse it
        pass

    def renderMovie(self):
        chimera = "" #Enter your chimera executable location here
        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            chimera = "/programs/x86_64-linux/chimera/1.13.1/bin/chimera"
        elif sys.platform == "darwin":
            # OS X
            chimera = "/Applications/Chimera.app/Contents/MacOS/chimera"
        else:
            if(chimera == ""):
                raise Exception("Your operating system was not recognized so the script cannot auto-detect your chimera executable location. "
                            + "Please manually edit the script to include your chimera executable location at line 190")
        selfPath = os.path.realpath(__file__)
        argsString = " "
        if(args.f):
            argsString += "-f "
        if(args.r):
            argsString += "-r "
        if(args.hr):
            argsString += "-hr "
        print(args)
        subprocess.run(chimera + " --script " + "\"" +
                       selfPath + " -chimera " + argsString + self.path + "\"", shell=True)

    def numClasses(self):
        pass

    def __init__(self, path):
        super(class3D, self).__init__(path)
        self.__addParameters()
        self.read("data_model_classes")
        self.graphToPDF()


class chimeraRenderer():

    def __getJobName(self):
        split = self.path.split("/")
        return split[len(split)-1]

    def __getCurrentDirectory(self):
        return os.getcwd()

    def __sortMrcs(self, model=" "):
        """Sorting method to sort by mrc iteration number"""

        s = model.split("it")
        it = int(s[1][0:3])
        if s[0].startswith("run_ct"):
            it += 1
        return it

    def __sortClasses(self, model=" "):
        """Sorting method to sort by mrc class number"""

        s = model.split("class")
        classNum = int(s[1][0:3])
        return classNum

    def __readMrcs(self):
        """Goes to the directory given in path, then reads in all the .mrc files
        Iterates over the read MRCs, organizing them by iteration number and class number.
        Returns a dictionary where the keys are the iterations in order, and the item is a list
        with the classes for that iteration in order """

        mrcs = glob.glob(self.path + '/*.mrc')
        if len(mrcs) == 0:
            raise Exception("ERROR: Could not find any mrc files")
        mrcs.sort(key=self.__sortMrcs)
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
            iterations[k].sort(key=self.__sortClasses)
        return iterations

    def __saveImage(self, png_name, raytrace, flat, highRes, closeModelsAfterSaving=True, autoFitWindow=True):
        try:
            from chimera import runCommand as rc
        except:
            pass
        rc("lighting contrast .7")
        rc("lighting sharpness 100")
        rc("lighting reflectivity .8")
        rc("lighting brightness 1.1")
        raytraceString = ""
        if(raytrace):
            rc("lighting reflectivity .8")
            rc("lighting brightness 0.85")
            raytraceString = "raytrace rtwait rtclean "
        resolutionString = ""
        if(highRes):
            resolutionString = "width 8  height 8 dpi 256 units inches"
        else:
            resolutionString = "width 8  height 8 dpi 128 units inches"
        if autoFitWindow:
            rc("windowsize 1024 1024")
            rc("window")
        if(flat):
            rc("lighting mode ambient")
            rc("set silhouetteWidth 8")
        else:
            rc("lighting mode two-point")
            rc("set silhouetteWidth 4")
        rc("copy file " + png_name +
                   " supersample 4 " + raytraceString + resolutionString)
        if closeModelsAfterSaving:
            rc("close all")

    def render(self):
        try:
            from chimera import runCommand as rc
        except:
            pass
        for it in self.iterations.keys():
            modelNum = 0
            rc("cd " + self.path)
            for c in self.iterations[it]:
                rc("open " + c)
                rc("volume #" + str(modelNum) + " sdlevel 7")
                modelNum += 1
            rc("volume all step 1")
            rc("tile")
            rc("preset apply publication 1")
            num = str(it)
            while len(num) < 4:
                num = "0" + num
            png_name = "frame" + num + ".png"
            subprocess.call("echo \"Finished iteration " + str(it) + " at " +
                            datetime.now().strftime('%H:%M:%S') + "\"", shell=True)
            rc("cd " + self.output)
            self.__saveImage(png_name, args.r, args.f, args.hr)
            finalIt = it

        # Spin with the final iteration
        modelNum = 0
        subprocess.call("echo \"Rendering final spin at " +
                        datetime.now().strftime('%H:%M:%S') + "\"", shell=True)
        rc("cd " + path)
        for c in self.iterations[it]:
            rc("open " + c)
            rc("volume #" + str(modelNum) + " sdlevel 7")
            modelNum += 1
        rc("volume all step 1")
        rc("tile")
        rc("preset apply publication 1")
        rc("window")
        for x in range(90):
            rc("turn y 4 model #0-" + str(modelNum))
            num = str(finalIt + 1 + x)
            while len(num) < 4:
                num = "0" + num
            png_name = "frame" + num + ".png"
            rc("cd " + self.output)
            self.__saveImage(png_name, args.r, args.f, args.hr,
                             False, False)
        rc("stop now")

    def makeOutputFolder(self):
        self.current = self.__getCurrentDirectory()
        self.jobName = self.__getJobName()
        self.output = self.current + "/" + self.jobName + "Images"
        try:
            os.mkdir(self.output)
        except:
            pass

    def __init__(self, path, args):
        self.path = path
        self.makeOutputFolder()
        self.iterations = self.__readMrcs()
        self.render()
        self.args = args


def parseArgs():
    """Parses arguments and returns them as an args object"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    parser.add_argument(
        '-i', dest='i', action='store_true', help='Show the interactive form of the graphs in addition to saving to a PDF.')
    parser.add_argument(
        '-m', dest='m', action='store_true', help='Render a movie of the job using Chimera')
    parser.add_argument(
        '-r', dest='r', action='store_true', help='Render images using Chimera raytracing')
    parser.add_argument(
        '-f', dest='f', action='store_true', help='Render images as flat, without shadows or highlights')
    parser.add_argument(
        '-hr', dest='hr', action='store_true', help='Render higher resolution images. Will make the process slower.')
    parser.add_argument(
        '-chimera', dest='chimera', action='store_true', help='Execute the script run from chimera')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parseArgs()
    path = args.path[0]

    """ If this script is called from chimera, then args.chimera = True
    If this is the case, we run a totally different script than if it were
    called by the used alone"""
    if(args.chimera):
        renderer = chimeraRenderer(path, args)
    else:
        job = class3D(path)
        if(args.i):
            job.graph()
        if(args.m):
            job.renderMovie()

"""
TODO:
-Make the graphs autoformat in a nice matter. Right now I have nothing.
"""
