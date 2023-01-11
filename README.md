### *From My Research at Texas A&M University*
# Homework Analyzer - `Analyzer.py`

## Description:
Python script that takes C++ homework submissions from Mirmir Classroom (now shutdown) and scrapes files for metadata to track student performance.

## Arguments:
The script has **1 required argument** and **1 optional argument** to be passed when running:
  - (required) &nbsp; *targetDirectory* : 
<br /> The target directory should be:
    - A Mimir dataset zipfile in the current directory
    - The absolute path to a Mimir dataset zipfile
    - The absolute path to a folder containing multiple Mimir datasets (using the `-m` flag) 
  - (optional) &nbsp; *mulitpleSets* - `-m`:
<br /> Allows for a group of datasets to be ran together, and output into a single excel file.
  - (optional) &nbsp; *processErrors* - `-e`:
<br /> If a submission fails to compile, the script attempts to classify the submission's error.

## Dependencies:
  - **Python Modules**
    - pandas
    - numpy
    - tdqm 
  - **Environment**
    - linux envrionment
    - unzip command


## How to run: 
Terminal Input : `python3 Analyzer.py <-m> <-e> <targetDirectory>`
