#!/usr/bin/python3
#coding: utf-8

import glob
import argparse
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import subprocess
import sys
from datetime import datetime


try:
    import pandas as pd
    from IPython.display import display, HTML
except:
    pass

CHIMERA_PATH = "/Applications/ChimeraX-1.1.1.app/Contents/MacOS/ChimeraX"
LEVEL = 6

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

    def get(self, columnName):
        return self.table[columnName]

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


class relionJob():
    tables = []  # A list of starTables
    parameters = []  # A list of strings

    def sortModelStars(self, model=" "):
        """Sorting method which sorts model.star files by iteration number
        Important to do this double split, to get only the filename of the .star
        Otherwise had a bug if enclosing folders had 'it" in the name, like /titan/"""
        s = model.split("run_")[1]
        s = s.split("it")
        it = int(s[1][0:3])
        if 'ct' in s[0]:
            it += 1
        return it

    def __getCurrentDirectory(self):
        return os.getcwd()

    def __readModelStars(self):
        modelStars = glob.glob(self.path + '/run_*t*model.star')
        if len(modelStars) == 0:
            raise Exception("ERROR: Could not find a model.star file")
        modelStars.sort(key=self.sortModelStars)
        return modelStars

    def __readPipeline(self):
        pipelineStars = glob.glob(self.path + '/job_pipeline.star')
        if len(pipelineStars) != 1:
            raise Exception(
                "ERROR: Looked for exactly 1 pipeline.star file, found " + str(len(pipelineStars)) + ".")
        return pipelineStars

    def __getJobName(self):
        split = self.path.split("/")
        return split[len(split)-1]

    def read(self, tableName):
        table = starTable(self.modelStars, tableName)
        self.tables.append(table)

    def graph(self):
        """For each parameter, graph that parameter from the table"""
        for t in self.tables:
            for p in self.parameters:
                print(p)
                t.graph(p)
        plt.show()

    def format(self, p):
        """This method should be implemented in the subclass to ensure that they format the graph how they want."""
        pass

    def renderMovie(self):
        """Sets up the script to be run from chimera so it will render a movie."""
        print("Connecting to ChimeraX")
        chimera = CHIMERA_PATH
        if(chimera == ""):
            raise Exception("Your operating system was not recognized so the script cannot auto-detect your chimera executable location. "
                            + "Please manually edit the script to include your chimera executable location at line 165")
        selfPath = os.path.realpath(__file__)
        argsString = "-v '{}' ".format(args.v[0]) + "-s '{}' ".format(args.s[0])
        imagePath = self.__getCurrentDirectory() + "/" + self.jobName + "Images"
        print("Rendering")
        command = chimera + " --script " + "\"" + selfPath + " -type " + self.jobType() + " " + argsString + self.path + "\""
        # subprocess.run('echo {}'.format(command))
        subprocess.run(chimera + " --script " + "\"" +
                       selfPath + " -type " + self.jobType() + " " + argsString + self.path + "\"", shell=True)
        os.chdir(imagePath)
        try:
            subprocess.call(
                "ffmpeg -r 10 -f image2 -s 1920x1080 -i frame%04d.png -vcodec libx264 -crf 25 -pix_fmt yuv420p movie.mp4", shell=True)
        except:
            print("Rendering frames into movie failed. Check that you have ffmpeg installed")
            print("Try manually running the command from the chimeraImages folder: ffmpeg -r 10 -f image2 -s 1920x1080 -i it%04d.png -vcodec libx264 -crf 25 -pix_fmt yuv420p movie.mp4")

    def graphToPDF(self):
        """Save the graphs to a pdf with the job name"""
        pp = PdfPages(self.jobName + '.pdf')
        style = args.style[0]
        print("Using style " + style)
        print("Saving graphs as " + self.jobName + ".pdf")
        for t in self.tables:
            for p in self.parameters:
                # Use the style input with -s, defualt to seaborn-paper
                plt.style.use(style)
                t.graph(p)

                # Take the title and ylabel from the parameter name, removing "rln"
                plt.title(p[3:])
                plt.ylabel(p[3:])
                self.format(plt)
                pp.savefig()
                plt.close()
        pp.close()

    def jobType(self):
        """Determine the job type by reading the pipeline file"""
        self.pipeline = starTable(
            self.__readPipeline(), "data_pipeline_processes")
        x = self.pipeline.get("rlnPipeLineProcessName")[0]
        jobType = x.iloc[0].split("/")[0]
        return jobType

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.jobName = self.__getJobName()
        self.modelStars = self.__readModelStars()


class class3D(relionJob):

    def __addParameters(self):
        """Defines the parameters to be graphed"""
        self.parameters.append("rlnClassDistribution")
        self.parameters.append("rlnEstimatedResolution")
        self.parameters.append("rlnAccuracyRotations")
        self.parameters.append("rlnAccuracyTranslationsAngst")

    def format(self, p):
        """Graph formatting rules for class3D"""
        p.legend(loc='upper left', title="Classes")
        p.xlabel("Iteration")

    def __init__(self, path):
        super(class3D, self).__init__(path)
        self.__addParameters()
        self.read("data_model_classes")
        self.graphToPDF()


class initialModel(relionJob):

    def __addParameters(self):
        """Defines the parameters to be graphed"""
        self.parameters.append("rlnCurrentResolution")
        self.parameters.append("rlnCurrentImageSize")
        self.parameters.append("rlnSigmaOffsetsAngst")
        self.parameters.append("rlnLogLikelihood")
        self.parameters.append("rlnAveragePmax")

    def format(self, p):
        """Graph formatting rules for class3D"""
        p.xlabel("Iteration")
        ax = p.gca()
        ax.get_legend().remove()

    def format(self, p):
        p.xlabel("Iteration/10")

    def __init__(self, path):
        super(initialModel, self).__init__(path)
        self.__addParameters()
        self.read("data_model_general")
        self.graphToPDF()


class refine3D(relionJob):

    def __readModelStars(self):
        """Overriding __readModelStars in relionJob, need to make it so it only reads the half1_model.stars"""
        modelStars = glob.glob(self.path + '/run_*t*half1_model.star')
        if len(modelStars) == 0:
            raise Exception("ERROR: Could not find a model.star file")
        modelStars.sort(key=super(refine3D, self).sortModelStars)
        return modelStars

    def format(self, p):
        """Graph formatting rules for refine3D, notably, has no legend"""
        p.xlabel("Iteration")
        ax = p.gca()
        ax.get_legend().remove()

    def __addParameters(self):
        """Defines the parameters to be graphed"""
        self.parameters.append("rlnEstimatedResolution")
        self.parameters.append("rlnAccuracyRotations")
        self.parameters.append("rlnAccuracyTranslationsAngst")
        self.parameters.append("rlnOverallFourierCompleteness")

    def __init__(self, path):
        super(refine3D, self).__init__(path)
        self.modelStars = self.__readModelStars()
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

        s = model.split("_it")
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
        with the paths to the classes for that iteration in order """

        mrcs = glob.glob(self.path + '/*.mrc')
        if(self.jobType == "Refine3D"):
            mrcs = glob.glob(self.path + '/*half1_class001.mrc')
        if(self.jobType == 'InitialModel'):
            mrcs = [x for x in mrcs if 'class' in x]
        if len(mrcs) == 0:
            raise Exception("ERROR: Could not find any mrc files")
        mrcs.sort(key=self.__sortMrcs)
        iterations = {}
        for fn in mrcs:
            s = fn.split("_it")
            it = int(s[1][0:3])
            if self.jobType == "InitialModel":
                it = int(it / 10)
            if "ct" in fn:
                it += 1
            if(it in iterations):
                iterations[it] = iterations[it] + [fn]
            else:
                iterations[it] = [fn]
        # If we're rendering a refinement, add the maximixed version as the final iteration
        if(self.jobType == "Refine3D"):
            iterations[it+1] = glob.glob(self.path + '/run_class001.mrc')

        for k in iterations.keys():
            iterations[k].sort(key=self.__sortClasses)
        return iterations

    def __saveImage(self, png_name, visuals, save, closeModelsAfterSaving=True, autoFitWindow=True):
        """Save an image from chimera into the output folder"""
        run(session, visuals)
        run(session, "save " + png_name + " " + save)
        if closeModelsAfterSaving:
            run(session, "close all")

    def render(self):
        """Render frames of the iterations in chimera"""
        for it in list(self.iterations.keys()):
            run(session, "cd " + self.path)
            model_number = 1
            for c in self.iterations[it]:
                run(session, "open " + c)
                run(session, "volume #{} sdlevel {}".format(model_number, LEVEL))
                model_number += 1
                
            run(session, "volume all step 1")
            run(session, "tile")
            run(session, "preset publication")
            run(session, "view")
            png_name = "frame" + f'{it:04}' + ".png"
            run(session, "cd " + self.output)
            self.__saveImage(png_name, visuals=self.args.v[0], save=self.args.s[0])
            subprocess.call("echo \"Finished iteration " + str(it) + " at " +
                            datetime.now().strftime('%H:%M:%S') + "\"", shell=True)
            finalIt = it

        #Spin with the final iteration
        subprocess.call("echo \"Rendering final spin at " +
                        datetime.now().strftime('%H:%M:%S') + "\"", shell=True)
        run(session, "cd " + self.path)
        model_number = 1
        for c in self.iterations[it]:
            run(session, "open " + c)
            run(session, "volume #{} sdlevel {}".format(model_number, LEVEL))
            model_number += 1

        run(session, "volume all step 1")
        run(session, "tile")
        run(session, "preset publication")
        for x in range(90):
            model_number = 1
            for c in self.iterations[it]:
                run(session, "turn y 4 model #{} center #{}".format(model_number, model_number))
                model_number += 1
            num = finalIt + 1 + x
            png_name = "frame" + f'{num:04}' + ".png"
            run(session, "cd " + self.output)
            self.__saveImage(png_name, visuals=self.args.v[0], save=self.args.s[0], closeModelsAfterSaving=False)
        run(session, "exit")

    def makeOutputFolder(self):
        """Create the jobImages output folder"""
        self.current = self.__getCurrentDirectory()
        self.jobName = self.__getJobName()
        self.output = self.current + "/" + self.jobName + "Images"
        try:
            os.mkdir(self.output)
        except:
            pass

    def __init__(self, path, args):
        self.path = path  #Path to the job folder
        self.jobType = args.type[0]
        self.args = args
        self.makeOutputFolder()
        self.iterations = self.__readMrcs()
        self.render()
        


def parseArgs():
    """Parses arguments and returns them as an args object"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    parser.add_argument(
        '-i', dest='i', action='store_true', help='Show the interactive form of the graphs in addition to saving to a PDF.')
    parser.add_argument(
        '-m', dest='m', action='store_true', help='Render a movie of the job using ChimeraX')
    parser.add_argument(
        '-v', nargs=1, default=["lighting soft"], help='Specify visual settings to be used during ChimeraX rendering.')
    parser.add_argument(
        '-s', nargs=1, default=["supersample 4 width 1024 height 1024 transparentBackground true"], help='Specify save settings to be used during ChimeraX rendering.')
    parser.add_argument(
        '-style', nargs=1, default=["seaborn-paper"], help='Use this argument to define which style matplotlib will use to plot the graphs.')
    parser.add_argument(
        '-type', nargs=1, help='Input the job type, should not be used by any user')
    args = parser.parse_args()
    return args


if "ChimeraX" in __name__:
    from chimerax.core.commands import run
    args = parseArgs()
    path = args.path[0]
    chimeraRenderer(path, args)


if __name__ == '__main__':
    args = parseArgs()
    path = args.path[0]
    
    """ If this script is called from chimera, then args.chimera = True
    If this is the case, we run a totally different script than if it were
    called by the used alone"""
    job = relionJob(path)
    print("Recognized job as " + job.jobType())
    if(job.jobType() == "Class3D"):
        job = class3D(path)
    elif(job.jobType() == "Refine3D"):
        job = refine3D(path)
    elif(job.jobType() == "InitialModel"):
        job = initialModel(path)
    if(args.i):
        job.graph()
    if(args.m):
        job.renderMovie()

"""
TODO:
-Make it not crash when filling the table with N/A values, such as during a alignment free classification (This seems to be fine...)
-If a job is continued twice, ie. ct_20 & ct_30, the ct_30 will have double the data because 
 it will already increment by one for ct_20 and won't know to increment by 2 for ct_30
-Maybe make it able to set the SD level manually, currently would have to edit the script
"""
