### *From My Research at Texas A&M University*
# Analyze Submissions `analyzeSubs.py`

## Description:
Python Script that takes C++ assignment submissions in a zipfile and outputs an Excel spreadsheet to analyze data from submissions.

## Arguments:
The Script has **1 required argument** and **1 optional argument** to be passed when running:
  - (required) &nbsp; *workingDir* : 
<br /> The workingDir should be a zipfile either in the current directory **OR** a path to the zipfile from the root directory 
<br /> (i.e. `/mnt/c/users/.../<workingDir>`)  
  - (optional) &nbsp; *mulitSet*:
<br /> Allows for a group of datasets to be ran together, and output into a single excel file. When running as a multiSet, the *workingDir* passed should be a path to a folder with multiple datasets (zipfiles) within it. 
<br /> By default the script assumes only one set, and is looking for a zipfile, passing `-m` or `--multiSet` allows for multiple sets to be analyzed.

## Dependencies:
  - **Python Modules**
    - pandas
    - numpy
    - tdqm 
  - **Environment**
    - linux envrionment
    - unzip command


## How to run: 
Terminal Input : `user$: python3 Analyzer.py <workingDir> <-a OR -m>`
