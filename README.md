### *From My Research at Texas A&M University*
# Analyze Submissions `analyzeSubs.py`

## Description:
Python Script that takes C++ assignment submissions in a zipfile and outputs an Excel spreadsheet to analyize data from submissions.

See example_submissions.zip for zipfile formatting.

## Arguments:
The Script has **1 required argument** and **2 optional arguments** to be passed when running:
  - (required) &nbsp; *workingDir* : 
<br /> The workingDir should be a zipfile either in the current directory OR a path to the zipfile from the root directory 
<br /> (i.e. `/mnt/c/users/.../<workingDir>`)  
  - (optional) &nbsp;  *allSubs* : 
<br /> Allows for either all submissions to be compiled or only the final submissions of each student. By default it will only compile the final submissions, passing `-a` or `--allSubs` will compile all submissions.
  - (optional) &nbsp; *mulitSet*:
<br /> Allows for a group of datasets to be ran together, and output into a single excel file. When running as a multiSet, the *workingDir* passed should be a path to a folder with multiple datasets (zipfiles) within it. 
<br /> By default the script assumes only one set, and is looking for a zipfile, passing `-m` or `--multiSet` allows for multiple sets to be analyzed. Arguement *allSubs* is set to True.


## How to run: 
Terminal Input : `user$: <python / python3> analyzeSubs.py <workingDir> <-a OR -m>`

Demo script with example_submissions.zip
