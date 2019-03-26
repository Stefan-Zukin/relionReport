#!/usr/bin/python
# coding: utf-8

import glob
import pandas as pd

def parseStar(starfile, keep_index=False, augment=False):
    headers = []
    foundheader = False
    ln = 0
    with open(starfile, "r") as f:
        for l in f:
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
                break
            ln += 1
    df = pd.read_csv(starfile, skiprows=ln, delimiter='\s+', header=None)
    df.columns = headers
    return df  #A PANDAS data frame object is returned
        

#Use the runJob file to determine the number of classes without having to iterate through the whole data.star file        
runJob = glob.glob("run.job")[0]
numClasses = 0
micrographs = 0
with open(runJob, "r") as f:
    for l in f:
        if l.startswith("Number of classes"):
            numClasses = (int)(l.split("== ")[1])

#Read the data.star files, iterating through them
dataStars = glob.glob('*data.star')
for name in dataStars:
    dataFilename = name
    df = parseStar(dataFilename)
    classes = {}
    for column in df:
        if column == "rlnClassNumber":
            for i in df[column]:
                if i not in classes :
                    classes[i] = 1
                else:
                    classes[i] = classes[i] + 1
    print(classes)
    if micrographs == 0:
        for i in classes:
            micrographs += classes[i]
print(micrographs)