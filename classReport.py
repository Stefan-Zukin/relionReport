#!/usr/bin/python
# coding: utf-8

import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb

#ParesStar function taken from PyEM
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
                    #Don't add to skipped line value if I'm reading the data
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
                    #Read through the data to see how long it is, record length in lb
                    #Use this value in the pd.read_csv line
                    if l.startswith(" "):
                        break
                    lb += 1
    # print("ln:" + str(ln))
    # print("lb:" + str(lb))
    df = pd.read_csv(starFile, skiprows=ln, delimiter='\s+', nrows=lb, header=None)
    df.columns = headers
    return df  #A PANDAS data frame object is returned


#     #Original ParesStar function taken from PyEM
# def parseStar(starfile, keep_index=False, augment=False):
#     headers = []
#     foundheader = False
#     ln = 0
#     with open(starfile, "r") as f:
#         for l in f:
#             if l.startswith("_"):
#                 foundheader = True
#                 lastheader = True
#                 if keep_index:
#                     head = l.rstrip()
#                 else:
#                     head = l.split('#')[0].rstrip().lstrip('_')
#                 headers.append(head)
#             else:
#                 lastheader = False
#             if foundheader and not lastheader:
#                 break
#             ln += 1
#     df = pd.read_csv(starfile, skiprows=ln, delimiter='\s+', header=None)
#     df.columns = headers
#     return df  #A PANDAS data frame object is returned
        

#Use the runJob file to determine the number of classes without having to iterate through the whole data.star file        
runJob = glob.glob("run.job")[0]
numClasses = 0
micrographs = 0
with open(runJob, "r") as f:
    for l in f:
        if l.startswith("Number of classes"):
            numClasses = (int)(l.split("== ")[1])
    
#Iterate through model.star files, reading the class distribution
modelStars = sorted(glob.glob('*model.star'))
classDict = {}
it = 0
for name in modelStars:
    # print("Reading " + name)
    filename = name
    df = parseStar(filename, "data_model_classes")
    classDist = []
    for column in df:
        if column == "rlnClassDistribution":
            classDist = list(df[column])
    classDict[it] = classDist
    it += 1
    # print(df)
cd = pd.DataFrame.from_dict(classDict, orient='index')
headers = []
legend = ''
for i in range(numClasses):
    headers.append("class_" + str(i))
    legend += str(i+1)
cd.columns = headers
print(cd)

cd.plot(use_index=True)
plt.legend(legend, ncol=2, loc='upper left');
plt.show()

#Read the data.star files, iterating through them
# dataStars = glob.glob('*data.star')
# it = 1
# classDict = {}
# for name in dataStars:
#     print("Reading " + name)
#     dataFilename = name
#     df = parseStar(dataFilename)
#     classes = []
#     for i in range(numClasses):
#         classes.append(0)
#     for column in df:
#         if column == "rlnClassNumber":
#             for i in df[column]:
#                 classes[i-1] = classes[i-1] + 1
#     print(classes)
#     if micrographs == 0:
#         for i in classes:
#             micrographs += i
#     classDict["it_" + str(it)] = classes
#     it += 1
# cd = pd.DataFrame.from_dict(classDict, orient='index')
# cd.plot()
# plt.show()



#TODO: This whole thing is more than I had to do. I don't actually have to read in all the data and then iterate through it, the 
#Class distribution is stored in the model.star file, so I just have to read that in. I'll keep this code because it might be useful
#But that will be a much faster way to do this.