"""
Homework Analyzer - Student Class

Author: Santana Gonzales
Date: 12/16/2022
"""

import os
from numpy import average
from pandas import DataFrame
from concurrent.futures import ProcessPoolExecutor
from Submission import Submission


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


class Student:
    """
    student class acts like a container for each student's submissions and basic info about student\\
    Each student holds:
    - Student ID
    - All of the student's submissions
    - Compile Rate
    - time between first and last submission (in epoch time)
    - average time between submissions (in epoch time)
    """

    studentID = ""
    compileRate = 1.00
    numberOfSubmissions = 0
    totalWorkTime = 0.0
    averageWorkTime = 0.0
    processErrors = False
    submissions = list()

    def __init__(self, studentDirectory: str, processErrors=False):
        """
        The studentDirectory is a folder name from within a dataset.
        """
        self.studentID = studentDirectory.split(" ")[1]
        self.processErrors = processErrors
        self.__get_subs(studentDirectory)
        self.__set_times()

    def __get_subs(self, folder: str):

        # enter student's directory
        os.chdir(folder)

        # make sure file system is sorted and is only Submission zips
        submissionZipfiles = list()
        for file in os.listdir():
            if file.startswith("Submission"):
                submissionZipfiles.append(file)

        submissionZipfiles.sort()

        self.numberOfSubmissions = len(submissionZipfiles)
        compiledSubmissions = 0

        # use multiprocessing to compile submissions
        with ProcessPoolExecutor() as exe:
            results = [exe.submit(Submission, zipfile, self.processErrors)
                       for zipfile in submissionZipfiles]
            self.submissions = [sub.result() for sub in results]

        # calculate compilation rate for student
        for submission in self.submissions:
            if submission.compiled:
                compiledSubmissions += 1
        self.compileRate = compiledSubmissions / self.numberOfSubmissions

        # return to beginning directory
        os.chdir("..")

    def __set_times(self):

        times = list()
        firstTime = None
        lastTime = None
        for sub in self.submissions:
            if lastTime == None:
                firstTime = sub.timeCreated
                lastTime = sub.timeCreated
            else:
                times.append(abs(lastTime - sub.timeCreated))
                lastTime = sub.timeCreated

        # account for people with only one submission
        if firstTime == lastTime:
            self.averageWorkTime = 0
            self.totalWorkTime = 0
        # otherwise, we calculate submission times
        else:
            self.averageWorkTime = (average(times))
            self.totalWorkTime = lastTime - firstTime

    def num_consec_fail(self):
        """
        Function to get the number of consecutive submissions that didn't compile for the student.
        """
        total = 0
        prevSub = None
        for sub in self.submissions:
            if prevSub == None:
                prevSub = sub
            elif (not prevSub.compiled) and (not sub.compiled):
                total += 1

        return total

    def most_freq_error(self):
        """
        Function to get the most common error for the student.
        """
        errs = {}
        for sub in self.submissions:
            if sub.error == "No Error":
                continue

            if sub.error in errs:
                errs[sub.error] += 1
            else:
                errs[sub.error] = 1

        if len(errs) == 0:
            return "No Errors"
        else:
            return max(errs, key=errs.get)

    def to_DataFrame(self):

        df = DataFrame({
            "Student ID": [self.studentID],
            "Number of Submissions": [self.numberOfSubmissions],
            "Compile Rate": [self.compileRate],
            "Average Time per Sub": [epoch_to_date(self.averageWorkTime)],
            "Total Work Time": [epoch_to_date(self.totalWorkTime)],
            "Consecutive Failures": [self.num_consec_fail()]
        })

        if self.processErrors:
            df["Most Frequent Error"] = [self.most_freq_error()]

        return df

    def print_info(self):

        print("Student", self.studentID, ":")
        print("# of Subs:", self.numberOfSubmissions)
        print("Compile Percentage: {:02.2f}".format(
            self.compileRate * 100) + " %")
        print("Total Time Working:\t", epoch_to_date(self.totalWorkTime))
        print("Avg time per submission:", epoch_to_date(self.averageWorkTime))
        print()