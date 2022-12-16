import os 
from argparse import ArgumentParser
from shutil import copy
from typing import List
from time import time
from numpy import average, ndarray
from pandas import concat, read_excel
from tqdm import tqdm
from Student import Student

def get_students(source: str, proc_errors: bool, from_excel: bool) -> List[Student]:
    """
    Takes a source to student information should be retrieved from and returns a list of student objects.\n
    Source inputs:
    - A directory containing student folders (default operation)
    - File name of an excel file within the current directory (using -f or --fromExcel flag when running)
    """
    students = list()
    
    if from_excel:
        df = read_excel(source)
        for row in df.values:
            currRow = row_to_string(row)
            students.append(Student(currRow, fromExcel=True))
    else:
        os.chdir(source)
        # sorting student directories so excel output is in correct order
        studentDirs = os.listdir()
        studentDirs.sort()

        for folder in tqdm(studentDirs, desc = "Students", unit = "Student"):
            if not folder.startswith("Student"): continue

            try:                students.append(Student(folder, proc_errors))
            except Exception as e:   print("[ERROR]: " + folder + " Failed ", e)

        os.chdir("..")
        remove_folder(source)

    return students

def is_path(dir: str) -> bool:
    """
    Checks if string is a path to a directory, returns True if '/' is present in the string.
    """
    if '/' in dir in dir:  return True
    else:           return False

def unzip_from_path(path: str) -> str:
    """
    Copies '.zip' from another directory into current directory and unzips locally.
    Deletes the '.zip' folder copied over after unzipping it

    returns new unzipped folder name
    """
    start_dir = os.getcwd()
    
    os.chdir('/')                                   # go to root dir
    copy(path,start_dir)                            # copy zipfile to our current dir
    os.chdir(start_dir)                             # return to working dir

    zipFolder = os.path.basename(path)              # get our zipfolder name from path
    zipFolder = unzip_folder(zipFolder)             # unzip folder and rename our zipFolder

    os.remove(zipFolder + '.zip')                   # delete the copied over zip

    return zipFolder                                # return working unzip file

def unzip_folder(zipfile: str) -> str:
    """
    Unzips folder inside of current directory.\\
    returns new unzipped folder name
    """

    newfile = zipfile.replace('.zip','')
    os.mkdir(newfile)
    os.system("unzip -q " + zipfile + " -d " + newfile)
    return newfile

def unzip_submissions(subZip: str) -> str:
    """
    Determines how to unzip submission zip\\
    returns the new unzipped folder name
    """
    # working directory is a path
    if is_path(subZip):
        try:
            unzippedDir = unzip_from_path(subZip)
        except Exception as e:
            print(e)
            quit()
    # working directory not a path
    else:
        try:
            unzippedDir = unzip_folder(subZip)
        except Exception as e:
            print(e)
            quit()
    
    return unzippedDir

def remove_folder(folder: str) -> None:
    """
    Force remove a file or folder from directory.
    """
    os.system("rm -rf " + folder)

def row_to_string(row: ndarray) -> str:
    """
    Converts a row from a Dataframe into strings.
    """
    finalstr = ""
    for elem in row:
        finalstr += str(elem) + " "

    return finalstr

def epoch_to_date(epoch: float) -> str:
    """
    Takes a epoch time (seconds since 1/1/1970) and returns a string with the time amount in days, hours, minutes, and seconds.
    """
    days  =  int(epoch / (60*60*24))
    epoch -= days * (60*60*24)
    hours =  int(epoch / (60*60))
    epoch -= hours * (60*60)
    mins  =  int(epoch / 60)
    epoch -= mins * (60)
    secs  =  epoch

    return "{:02d}:{:02d}:{:02d}:{:05.2f}".format(days, hours, mins, secs)

def print_students_info(students: List[Student], dir: str) -> None:
    """
    Print information about a list of students\\
    Arguements:
        - `students: List[student]` is the list of students the function will calculate data from.
        - `dir: str` is the directory the student's were originally located.
    """

    END_FORMATING = '\33[0m'
    ITALIC = '\33[3m'
    BLACK = '\33[30m'
    YELLOW = '\33[33m'
    WHITE = '\33[37m'
    BOLD = '\33[1m'
    WHITE_BG = '\33[47m'

    workTimes = list()
    subTimes  = list()
    totalComp = 0
    totalSubs = list()
    
    for s in students:
        if s.workTime != 0: workTimes.append(s.workTime)
        if s.avgTime  != 0: subTimes.append(s.avgTime)
        totalComp += int(s.compRate * s.numOfSubs)
        totalSubs.append(s.numOfSubs)

    print()
    print(ITALIC + "For students in " + YELLOW + "\"" + dir + "\" " + END_FORMATING + ":\n")

    print("Toral Number of Students:\t"    + WHITE_BG + BLACK + "{:3d}".format(len(students))  + END_FORMATING)
    print("Total Number of Submissions:\t" + WHITE_BG + BLACK + "{:3d}".format(sum(totalSubs)) + END_FORMATING + "\n")

    print(BOLD + "Average total worktime:\t\t\t"          + END_FORMATING, epoch_to_date(average(workTimes)))
    print(BOLD + "Average time per Submissions:\t\t"      + END_FORMATING, epoch_to_date(average(subTimes)))
    print(BOLD + "Average Compilation Rate:\t\t"          + END_FORMATING, "{:5.2f}".format(totalComp / sum(totalSubs)*100) + " %")
    print(BOLD + "Average # of submission per student:\t" + END_FORMATING, "{:4.2f}".format(average(totalSubs)) + END_FORMATING)
    print()

def proc_single(workingDir: str, proc_errors: bool = False, from_excel: bool = False):
    """
    Compiles a single set.\\
    Arguements:
        - `workingDir: str` should be the name to a zipfile in the current directory or a path to a zipfile from the root directory.
        - `proc_errors: bool` is used to process errors (Optional).
        - `from_excel: bool` used to denote when students are sourced from excel file. (Optional).

    Generates an excel output for the set and prints basic information gathered from the students.\\
    Returns a dataframe of the students (same dataframe that is output as an excel).
    """
    
    if from_excel:
        students = get_students(workingDir, proc_errors, True)
        print_students_info(students, workingDir)
    else:
        unzippedDir = unzip_submissions(workingDir)
        students    = get_students(unzippedDir, proc_errors, False)
        print_students_info(students, unzippedDir)
    

    # create dataframe containing all students from set
    dfs = [s.to_DataFrame() for s in students]
    df  = concat(dfs, axis=0)

    # output current dataset as excel
    if not from_excel: df.to_excel(f"{unzippedDir} output.xlsx", sheet_name = "Submission Analysis", index = False)
    else:              print(df)
    
    return df
    
def proc_multi(workingDir: str, proc_errors: bool = False):
    """
    Compiles multiple datasets.\n
    Arguements:
        - `workingDir: str` should be the name to a zipfile in the current directory or a path to a zipfile from the root directory.
        - `proc_errors: bool` is used to process errors (Optional).

    Generates an excel output for each set, as well as one containing all sets together.\n
    Returns a dataframe of the students (same dataframe that is output as an excel).
    """
    
    os.chdir(workingDir)

    # create list to contain students from all datasets
    dfs = list()

    for zipfile in os.listdir():
        if not zipfile.endswith(".zip"): continue
        
        try:
            dfs.append(proc_single(zipfile, proc_errors, False))
        except Exception as e:
            print("[ERROR]: " + zipfile + " analysis failed", e)
            continue

    # output all students in all datasets in single excel
    df  = concat(dfs, axis=0)
    df.to_excel("Multiple Dataset output.xlsx", sheet_name = "Submission Analysis", index = False)
    
    return df

    
def debug(workingDir: str, proc_errors: bool, multiSet: bool, fromExcel: bool):
    """
    Method used for debugging.\n
    No real functionalities    
    """
    students = get_students(workingDir, proc_errors, fromExcel)
    print_students_info(students, workingDir)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("workingDir"            , help = "zipped submissions file in current directory or full path to file", type = str)
    parser.add_argument("-f", "--fromExcel"     , help = "Read submissions from excel" , action = "store_true")
    parser.add_argument("-m", "--multiSet"      , help = "Folder to multiple sets"     , action = "store_true")
    parser.add_argument("-e", "--errorProc"     , help = "Processes submission errors" , action = "store_true")
    parser.add_argument("-d", "--debugging"     , help = "Run the debugging function"  , action = "store_true")
    args = parser.parse_args()

    workingDir = args.workingDir
    proc_errors = args.errorProc 
    multiSet = args.multiSet
    debugging = args.debugging
    fromExcel = args.fromExcel

    start = time()

    if debugging: debug(workingDir, proc_errors, multiSet, fromExcel)
    elif multiSet: proc_multi(workingDir, proc_errors)
    else: proc_single(workingDir, proc_errors, fromExcel)

    end = time()
    run = end - start
    print("Total runtime - " + "{:1d}".format(int(run/60)) + " minutes and " + "{:05.2f}".format(run%60) + " seconds.")
