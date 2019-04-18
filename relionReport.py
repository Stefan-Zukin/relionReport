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


class starTable():

    def __readModelGeneral(self):
        """
        This function is a special case to read the ModelGeneral table
        This is necessary because ModelGeneral has different formatting than all the other tables
        in the model.star file
        Returns a PANDAS dataframe
        """
        dictionary = {}
        foundTable = False
        reading = False
        with open(self.starFile, "r") as star:
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

    def __parseStar(self):
        """
        Used to read any table from a .star file, other than dataModelGeneral
        Taken from PyEM package. Slightly modified to read only the specific table.
        Returns a PANDAS dataframe
        """

        if self.tableName == "data_model_general":
            return self.__readModelGeneral()
        headers = []
        foundTable = False
        foundheader = False
        ln = 0
        lb = 0
        with open(self.starFile, "r") as star:
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
                        print(head)
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
        df = pd.read_csv(self.starFile, skiprows=ln,
                         delimiter='\s+', nrows=lb, header=None)
        df.columns = headers
        return df  # A PANDAS data frame object is returned

    def plot(self):
        #maxDist = self.df.max(axis=0).max()
        #minDist = self.df.min(axis=0).min()
        #ymax = maxDist + yMaxBuffer
        #ymin = minDist - yMinBuffer
        print(self.df.index)
        #df.plot(x='index', y='resolution', style='o')
    

    def writeToPDF(self):
        pass

    def __init__(self, starFile, tableName):
        self.starFile = starFile
        self.tableName = tableName
        self.df = self.__parseStar()
        print(self.df)


class starFile():

    def __init__(self):
        pass

    def table(self, tableName):
        pass


class relionJob():

    def __init__(self, path):
        self.path = path
        self.tables = {}


class class3D(relionJob):

    def __init__(self, path):
        self.path = path
        self.tables = {}

    def getTable(self):
        # If we have the starTable, return it, if not parse it
        pass

    def showGraphs(self):
        pass

    def graphToPDF(self):
        pass

    def renderMovie(self):
        pass

    def numClasse(self):
        pass


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


if __name__ == '__main__':
    args = parseArgs()
    path = args.path[0]
    job = class3D(path)
    job.showGraphs()


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
"""


class Snake:

    def __init__(self, name=""):
        self.name = name

    def change_name(self, new_name):
        self.name = new_name
        print(self.name)
