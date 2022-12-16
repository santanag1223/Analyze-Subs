import os 
from numpy import average
from pandas import DataFrame
from concurrent.futures import ProcessPoolExecutor
from Submission import Submission

def date_to_epoch(date: str) -> float:
    """
    Takes a formatted time (day:hr:min:sec) and returns a float in epoch time (seconds since 1/1/1970)
    """
    times = date.split(":")
    days  = int(times[0]) * (60*60*24)
    hours = int(times[1]) * (60*60)
    mins  = int(times[2]) * (60)
    secs  = float(times[3])

    return days + hours + mins + secs

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

class Student:
    """
    student class acts like a container for each student's submissions and basic info about student\n
    Each student holds:
    - Student ID
    - All of the student's submissions
    - Compile Rate
    - time between first and last submission (in epoch time)
    - average time between submissions (in epoch time)
    """

    studentID = ""
    compRate  = 1.00
    numOfSubs = 0

    workTime  = 0.0
    avgTime   = 0.0

    proc_err       = False
    subs           = list()

    def __init__(self, inputStr: str, proc_err = False, fromExcel = False):
        """
        The student constructor forms a student object differently based on the given input.\\
        If the inputStr is from a previously compiled excel output, it can parse the string for student information and rebuild the student
        structure, only without it's individual submissions.\\
        If the inputStr is a folder name from within a dataset, it still needs to be processed. This is done using the 
        __get_subs() and __set_times() methods in the constructor.
        """

        if fromExcel:
            cols = inputStr.split(" ")
            self.studentID = cols[0]
            self.numOfSubs = int(cols[1])
            self.compRate  = float(cols[2])
            self.avgTime   = date_to_epoch(cols[3])
            self.workTime  = date_to_epoch(cols[4])
        else: 
            self.studentID = inputStr.split(" ")[1]
            self.proc_err = proc_err
            self.__get_subs(inputStr)
            self.__set_times()

    def __get_subs(self, folder: str):

        # enter student's directory
        os.chdir(folder)

        # make sure file system is sorted and is only Submission zips
        subzips = list()
        for file in os.listdir():
            if file.startswith("Submission"): subzips.append(file)
        
        subzips.sort()

        self.numOfSubs = len(subzips)
        compiledSubs   = 0

        # use multiprocessing to compile submissions
        with ProcessPoolExecutor() as exe:
            results   = [exe.submit(Submission, zipfile, self.proc_err) for zipfile in subzips]
            self.subs = [sub.result() for sub in results]

        # calculate compilation rate for student
        for sub in self.subs:
            if sub.compiled: compiledSubs += 1
        self.compRate = compiledSubs / self.numOfSubs

        # return to beginning directory
        os.chdir("..")

    def __set_times(self):

        times     = list()      # list of times to average
        firstTime = None        # first submission time
        lastTime  = None        # submission time of last submission
        for sub in self.subs:
            if lastTime == None:
                firstTime = sub.timeCreated
                lastTime  = sub.timeCreated
            else:
                times.append(abs(lastTime - sub.timeCreated))
                lastTime = sub.timeCreated
        
        # account for people with only one submission
        if firstTime == lastTime:
            self.avgTime  = 0
            self.workTime = 0
        # otherwise, we calculate submission times
        else :
            self.avgTime  = (average(times))
            self.workTime = lastTime - firstTime

    def num_consec_fail(self):
        """
        Function to get the number of consecutive submissions that didn't compile for the student.
        """
        total = 0
        prev  = None
        for sub in self.subs:
            if prev == None:
                prev = sub
                continue
            if (not prev.compiled) and (not sub.compiled):
                total += 1
        
        return total

    def most_freq_error(self):
        """
        Function to get the most common error for the student.
        """
        errs = {}
        for sub in self.subs:
            if sub.error == "No Error": continue

            if sub.error in errs:   errs[sub.error] += 1
            else:                   errs[sub.error] = 1
        
        if len(errs) == 0:  return "No Errors"
        else:               return max(errs, key=errs.get)


    def to_DataFrame(self):

        df = DataFrame({
            "Student ID"            : [self.studentID],
            "Number of Submissions" : [self.numOfSubs],
            "Compile Rate"          : [self.compRate],
            "Average Time per Sub"  : [epoch_to_date(self.avgTime)],
            "Total Work Time"       : [epoch_to_date(self.workTime)],
            "Consecutive Failures"  : [self.num_consec_fail()]
        })

        if self.proc_err:
            df["Most Frequent Error"] = [self.most_freq_error()]

        return df

    def print_info(self):

        print("Student", self.studentID, ":")
        print("# of Subs:", self.numOfSubs)
        print("Compile Percentage: {:02.2f}".format(self.compRate * 100) + " %")
        print("Total Time Working:\t", epoch_to_date(self.workTime))
        print("Avg time per submission:", epoch_to_date(self.avgTime))
        print()