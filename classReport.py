#!/usr/bin/python
# coding: utf-8

import glob

dataStars = glob.glob('*data.star')
if len(dataStars) != 1:
    raise ValueError('should be only one data.star file in the current directory')

dataFilename = dataStars[0]
dataReadList = open(dataFilename, "r")
dataLines = dataReadList.readlines()
for x in dataLines:
    print(x)
print(len(dataLines))