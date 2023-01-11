"""
Homework Analyzer - Main File

Author: Santana Gonzales
Date: 12/16/2022
"""

import os
from argparse import ArgumentParser
from shutil import copy
from typing import List
from time import time
from numpy import average
from pandas import concat
from tqdm import tqdm
from Student import Student


def get_students(targetDirectory: str, processErrors: bool) -> List[Student]:
    """
    Creates a student for each folder in target directory.
    """
    students = list()
    os.chdir(targetDirectory)
    studentDirs = os.listdir()
    studentDirs.sort()

    for folder in tqdm(studentDirs, desc="Students", unit="Student"):
        if not folder.startswith("Student"):
            continue

        try:
            students.append(Student(folder, processErrors))
        except Exception as e:
            print(e)

    os.chdir("..")
    os.system("rm -rf " + targetDirectory)

    return students


def unzip_from_path(path: str) -> str:
    """
    Copies '.zip' from another directory into current directory and unzips locally.
    Deletes the '.zip' folder copied over after unzipping it

    returns new unzipped folder name
    """
    start_dir = os.getcwd()

    # go to root dir
    os.chdir('/')
    # copy zipfile to our current dir
    copy(path, start_dir)
    # return to target dir
    os.chdir(start_dir)

    # get our zipfolder name from path
    zipFolder = os.path.basename(path)
    # unzip folder and rename our zipFolder
    zipFolder = unzip_folder(zipFolder)

    # delete the copied over zip
    os.remove(zipFolder + '.zip')

    return zipFolder


def unzip_folder(zipfile: str) -> str:
    """
    Unzips folder inside of current directory.\\
    returns new unzipped folder name
    """

    newfile = zipfile.replace('.zip', '')
    os.mkdir(newfile)
    os.system("unzip -q " + zipfile + " -d " + newfile)
    return newfile


def unzip_submissions(targetDirectory: str) -> str:
    """
    Determines how to unzip submission zip\\
    returns the new unzipped folder name
    """
    # working directory is a path
    if '/' in targetDirectory:
        try:
            unzippedDir = unzip_from_path(targetDirectory)
        except Exception as e:
            print(e)
            quit()
    else:
        try:
            unzippedDir = unzip_folder(targetDirectory)
        except Exception as e:
            print(e)
            quit()

    return unzippedDir


def epoch_to_date(epoch: float) -> str:
    """
    Takes a epoch time (seconds since 1/1/1970) and returns a string with the time amount in days, hours, minutes, and seconds.
    """
    days = int(epoch / (60*60*24))
    epoch -= days * (60*60*24)
    hours = int(epoch / (60*60))
    epoch -= hours * (60*60)
    mins = int(epoch / 60)
    epoch -= mins * (60)
    secs = epoch

    return "{:02d} days; {:02d} hrs; {:02d} mins; {:05.2f} secs".format(days, hours, mins, secs)


def print_students_info(studentList: List[Student], dir: str) -> None:
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

    totalWorkTimes = list()
    averageTimes = list()
    totalCompiled = 0
    numberOfSubmissions = list()

    for student in studentList:
        if student.totalWorkTime != 0:
            totalWorkTimes.append(student.totalWorkTime)
        if student.averageWorkTime != 0:
            averageTimes.append(student.averageWorkTime)
        totalCompiled += int(student.compileRate * student.numberOfSubmissions)
        numberOfSubmissions.append(student.numberOfSubmissions)

    print()
    print(ITALIC + "For students in " + YELLOW +
          "\"" + dir + "\" " + END_FORMATING + ":\n")

    print("Toral Number of Students:\t" + WHITE_BG + BLACK +
          "{:3d}".format(len(studentList)) + END_FORMATING)
    print("Total Number of Submissions:\t" + WHITE_BG + BLACK +
          "{:3d}".format(sum(numberOfSubmissions)) + END_FORMATING + "\n")

    print(BOLD + "Average total worktime:\t\t\t" +
          END_FORMATING, epoch_to_date(average(totalWorkTimes)))
    print(BOLD + "Average time per Submissions:\t\t" +
          END_FORMATING, epoch_to_date(average(averageTimes)))
    print(BOLD + "Average Compilation Rate:\t\t" + END_FORMATING,
          "{:5.2f}".format(totalCompiled / sum(numberOfSubmissions)*100) + " %")
    print(BOLD + "Average # of submission per student:\t" + END_FORMATING,
          "{:4.2f}".format(average(numberOfSubmissions)) + END_FORMATING)
    print()


def proc_single(targetDirectory: str, proc_errors: bool = False):
    """
    Compiles a single set.\\
    Arguements:
        - `targetDirectory: str` should be the name to a zipfile in the current directory or a path to a zipfile from the root directory.
        - `processErrors: bool` is used to process errors (Optional).

    Generates an excel output for the set and prints basic information gathered from the students.\\
    Returns a dataframe of the students (same dataframe that is output as an excel).
    """
    if not targetDirectory.endswith('.zip'):
        return

    unzippedDirectory = unzip_submissions(targetDirectory)
    students = get_students(unzippedDirectory, proc_errors)
    print_students_info(students, unzippedDirectory)

    # create dataframe containing all students from set
    dataframes = [s.to_DataFrame() for s in students]
    mainDataFrame = concat(dataframes, axis=0)

    # output current dataset as excel
    mainDataFrame.to_excel(f"{unzippedDirectory} output.xlsx",
                           sheet_name="Submission Analysis", index=False)

    return mainDataFrame


def proc_multi(targetDirectory: str, proc_errors: bool = False):
    """
    Compiles multiple datasets.\\
    Arguements:
        - `targetDirectory: str` should be the name to a zipfile in the current directory or a path to a zipfile from the root directory.
        - `processErrors: bool` is used to process errors (Optional).

    Generates an excel output for each set, as well as one containing all sets together.\\
    Returns a dataframe of the students (same dataframe that is output as an excel).
    """

    os.chdir(targetDirectory)

    # create list to contain students from all datasets
    dataframes = list()

    for zipfile in os.listdir():
        if not zipfile.endswith(".zip"):
            continue

        try:
            dataframes.append(proc_single(zipfile, proc_errors))
        except Exception as e:
            print("[ERROR]: " + zipfile + " analysis failed", e)
            continue

    # output all students in all datasets in single excel
    mainDataframe = concat(dataframes, axis=0)
    mainDataframe.to_excel("Multiple Dataset output.xlsx",
                           sheet_name="Submission Analysis", index=False)

    return mainDataframe


def debug(workingDir: str, proc_errors: bool, multiSet: bool):
    """
    Method used for debugging.\\
    No real functionalities    
    """
    students = get_students(workingDir, proc_errors)
    print_students_info(students, workingDir)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "targetDirectory", help="zipped submissions file in current directory or full path to file", type=str)
    parser.add_argument("-m", "--mulitpleSets",
                        help="Folder to multiple sets", action="store_true")
    parser.add_argument("-e", "--processErrors",
                        help="Processes submission errors", action="store_true")
    parser.add_argument("-d", "--debug",
                        help="Run the debugging function", action="store_true")
    args = parser.parse_args()

    targetDirectory = args.targetDirectory
    processErrors = args.processErrors
    multipleSets = args.mulitpleSets
    debugging = args.debug

    start = time()

    if debugging:
        debug(targetDirectory, processErrors, multipleSets)
    elif multipleSets:
        proc_multi(targetDirectory, processErrors)
    else:
        proc_single(targetDirectory, processErrors)

    end = time()
    run = end - start
    print("Total runtime - " + "{:1d}".format(int(run/60)) +
          " minutes and " + "{:05.2f}".format(run % 60) + " seconds.")