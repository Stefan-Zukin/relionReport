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


try:
    import pandas as pd
    from IPython.display import display, HTML
    from chimera import runCommand as rc
    from chimera import replyobj
except:
    pass


"""
Invariants:
    -The path variable should always hold the absolute path to the target directory.
    -The curr variable should always hold the absolute path to the directory from which the script was run.


"""


class starTable():

    def __readModelGeneral(self, starFile):
        """
        This function is a special case to read the ModelGeneral table
        This is necessary because ModelGeneral has different formatting than all the other tables
        in the model.star file
        Returns a PANDAS dataframe
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
        return df  # A PANDAS data frame object is returned

    def __parseStar(self, starFile):
        """
        Used to read any table from a .star file, other than dataModelGeneral
        Taken from PyEM package. Slightly modified to read only the specific table.
        Returns a PANDAS dataframe
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
        self.table = pd.concat(iterations.values(), axis=0, keys=iterations.keys())
        self.table.to_html("meta.html")
        #for i in self.table.keys():
            #print(i)
        #self.table.unstack()
        #self.table.to_html("met1.html")
        #print(self.table)
        #self.df = self.__parseStar()
        #resolutions = self.table["rlnClassDistribution"]
        #print(self.table["rlnEstimatedResolution"][0])
        #resolutions.unstack().plot(kind='line')
        #plt.show()
        #print(p)

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
        #Works, the only thing I need to do is get the jobName
        pp = PdfPages(self.jobName + '.pdf')
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
        chimera = ""
        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            chimera = "/programs/x86_64-linux/chimera/1.13.1/bin/chimera"
        elif sys.platform == "darwin":
            # OS X
            chimera = "/Applications/Chimera.app/Contents/MacOS/chimera"
        selfPath = os.path.realpath(__file__)
        #print(chimera + " --script " + "\"" + selfPath + " -chimera" "\"")
        #subprocess.run(chimera + " --script " + "\"" + "/Users/stefanzukin/Desktop/Programming/Python/relionReport/cScriptTest.py" + "\"", shell= True)
        print(1)
        #print(selfPath)
        subprocess.run(chimera + " --script " + "\"" + selfPath + " -chimera " + "/" + "\"", shell= True)
        print(2)

    def numClasses(self):
        pass

    def __init__(self, path):
        super(class3D, self).__init__(path)
        self.__addParameters()
        self.read("data_model_classes")
        self.graphToPDF()
        
class chimeraRenderer():

    def __init__(self):
        print('hello')
        try:
            from chimera import runCommand as rc
            from chimera import replyobj
        except:
            pass
        rc("open /Users/stefanzukin/Desktop/postprocess.mrc")

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
    parser.add_argument(
        '-chimera', dest='chimera', action='store_true', help='Execute the script run from chimera')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parseArgs()
    path = args.path[0]
    subprocess.call("echo  chimeraFlag:" + str(args.chimera), shell=True)
    if(args.chimera):
        renderer = chimeraRenderer()
        subprocess.call("echo  3", shell=True)
        #sys.exit(0) 
    else:
        job = class3D(path)
        if(args.i):
            job.graph()
        if(not args.chimera):
            job.renderMovie()

"""
Considerations:
    -The way I have it set up now, you would have to read through the star file for
    each table you want to read. It's pretty redundant. Maybe I can just read the star file once
    and get all the tables. Too much ram? If I open up 40 model.stars with everything as a dataframe
    Thats at least 40 x .5Mb around 20Mb. Not a huge amount, but honestlty that also seems like a bad
    solution.
    -I'll run some tests and see how slow it is to read through a file.
        -Nevermind. It's actually very fast to read through these files. It terminates
        once it finds the correct table. Even changing it so it reads the whole table took only 0.009seconds.
    -For some reason, the data_model_general table is formatted differently from all the other star file tables
    I would like to access it, but would have to code in a special case.
    -What I really want is a 3D data table
        On one axis will be the class number,
        On one axis will be the data
        On one axis will be the iteration number
        ie:

        Class   Resolution
        0          5
        1          4
        2          7

        And extending vertically is the different iterations.
    This will have to be done for an individual star table. So I can implement it there.
"""
