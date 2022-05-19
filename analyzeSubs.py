import os 
import argparse
from shutil   import copy
from typing   import List
from time     import time
from numpy    import average, ndarray
from pandas   import DataFrame, concat, read_excel
from tqdm     import tqdm
from threading import Thread
from concurrent.futures import ProcessPoolExecutor

#-#-#- Command Line Parsing -#-#-#
def get_args():
    """
    Parses command line and returns parser object.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("workingDir"            , help = "zipped submissions file in current directory or full path to file", type = str)
    parser.add_argument("-f", "--fromExcel"     , help = "Read submissions from excel" , action = "store_true")
    parser.add_argument("-m", "--multiSet"      , help = "Folder to multiple sets"     , action = "store_true")
    parser.add_argument("-e", "--errorProc"     , help = "Processes submission errors" , action = "store_true")
    parser.add_argument("-d", "--debugging"     , help = "Run the debugging function"  , action = "store_true")
    args   = parser.parse_args()

    return args

#-#-#- Global Variables for text formatting -#-#-#
CEND      = '\33[0m'
CITALIC   = '\33[3m'
CBLACK    = '\33[30m'
CYELLOW   = '\33[33m'
CWHITE    = '\33[37m'
CBOLD     = '\33[1m'
CWHITEBG  = '\33[47m'

#-#-#- submission and student Classes #-#-#
class submission:
    """
    submission Class acts as a container for all submission data.\n
    Each submissions holds:
    - submission Folder Name
    - submission Number
    - Compiled Boolean
    - (optional) Error Type
    - (optional) Error Line
    """

    sub_folder  = ""
    subNum      = 0
    timeCreated = 0.0
    compiled    = None
    
    proc_err    = False
    error       = "Not Processed"
    errorLine   = ""

    def __init__(self, folder: str, proc_err = False):
        """ submission constructor expects a submission zipfile (Submission_<NUM>.zip)"""
        self.sub_folder  = folder
        nozip            = folder.replace(".zip","")
        self.subNum      = int(nozip.split("_")[1])
        self.proc_err    = proc_err

        self.__try_compile()

    def __compile_thread_func(self):

        # call compilation and check for a.out
        os.system("g++ -std=c++17 *.cpp -w 2>err.txt")

        if "a.out" in os.listdir(): 
            self.compiled    = True
            if (self.proc_err): self.error  = "No Error"
        else:
            self.compiled    = False

    def __try_compile(self):
        """
        Attempts compilation of submission.\n
        returns True if 'a.out' is created after compilation.\n
        calls 'get_error()' function if a.out not produced. 
        """

        # precausion for zipping error submission
        try:
            temp = unzip_folder(self.sub_folder)
        except Exception: 
            self.compiled = False
            self.error  = "Could Not Unzip"
            return
        
        # go into unzipped folder
        os.chdir(temp)

        # get time created
        self.timeCreated = os.path.getmtime(os.listdir()[0])

        # create thread to try compile and time
        comp_thread = Thread(target = self.__compile_thread_func)
        comp_thread.start()

        # don't let the system try to compile for longer than 3.5 sec
        start_time, cur_time = time(), time()
        while (cur_time - start_time < 3.5):
            cur_time = time()
            if not comp_thread.is_alive(): break
            
        if comp_thread.is_alive(): 
            self.compiled = False
            if (self.proc_err): self.error  = "Error when compiling"
        
        if self.compiled == False: self.error  = self.__get_error()

        # exit the unzipped folder and delete it
        os.chdir("..")

        try:   remove_folder(temp)
        except Exception: pass

    def __get_error(self) -> str:
        """
        Opens the submission's error file 'err.txt' and processes first error found.\n
        returns a preset error type based on keywords in compiler output.
        """

        syntax_keys  = list({" parse error"," expected"," redefinition"," overload"," stray"," unary",\
                            " token", " shadows a parameter", "not declared", "no matching",          \
                            " does not have any field", "return-statement", "no member", "not within",\
                            " old-style", "lvalue", "read-only", "conflict"})
        type_keys    = list({" type"," types"})
        scope_keys   = list({"declared"," no match ", " nested too deeply", "redeclaration", "previous declaration"})
        convert_keys = list({" cannot convert", "invalid conversion"})
        noMod_keys   = list({" no module "})
        noFike_keys  = list({" no such file "})
        exit1_keys   = list({" 1 exit status"})

        try: 
            with open("err.txt","r") as file:
                for line in file.readlines():
                    if " error: " in line:
                        line = line.rstrip()
                        line = line.lower()
                        self.errorLine = line

                        if error_search(syntax_keys,line):
                            return "Syntax Error"
                        if error_search(type_keys,line):
                            return "Type Error"
                        if error_search(scope_keys,line):
                            return "Scope Error"
                        if error_search(convert_keys,line):
                            return "Converson Error"
                        if error_search(noMod_keys,line):
                            return "NoModuleFound Error"
                        if error_search(noFike_keys,line):
                            return "FileNotFound Error"
                        if error_search(exit1_keys,line):
                            return "Exit Status 1 Error"
                        
                        return "Unknown Error"
        except Exception:
            return "COULD NOT READ"

class student:
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
        The student constructor forms a student object differently based on the given input.\n
        If the inputStr is from a previously compiled excel output, it can parse the string for student information and rebuild the student
        structure, only without it's individual submissions. \n
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
            results   = [exe.submit(submission, zipfile, self.proc_err) for zipfile in subzips]
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

def get_students(src: str, proc_errors: bool, from_excel: bool) -> List[student]:
    """
    Takes a source to student information should be retrieved from and returns a list of student objects.\n
    Source inputs:
    - File name of an excel file within the current directory (using -f or --fromExcel flag when running)
    - a directory containing student folders (default operation)
    """
    students = list()
    
    if from_excel:
        df = read_excel(src)
        for row in df.values:
            currRow = row_to_string(row)
            students.append(student(currRow, fromExcel=True))

    else:
        os.chdir(src)

        # sorting student directories so excel output is in correct order
        studentDirs = os.listdir()
        studentDirs.sort()

        for folder in tqdm(studentDirs, desc = "Students", unit = "Student"):
            if not folder.startswith("Student"): continue

            try:                students.append(student(folder, proc_errors))
            except Exception as e:   print("[ERROR]: " + folder + " Failed ", e)

        os.chdir("..")
        remove_folder(src)

    return students



#-#-#-        Helper Functions       -#-#-#
def is_path(dir: str) -> bool:
    """
    Checks if string is a path to a directory, returns True if '/' is present in the string.
    """
    if '/' in dir:  return True
    else:           return False

def unzip_from_path(path: str) -> str:
    """
    Copies '.zip' from another directory into current directory and unzips locally.\n
    deletes the '.zip' folder copied over after unzipping it

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
    Unzips folder inside of current directory.
    
    returns new unzipped folder name
    """

    newfile = zipfile.replace('.zip','')
    os.mkdir(newfile)
    os.system("unzip -q " + zipfile + " -d " + newfile)
    return newfile

def unzip_submissions(subZip: str) -> str:
    """
    Determines how to unzip submission zip\n
    returns the new unzipped folder name
    """
    if is_path(subZip):
    # working directory is a path
        try:
            unzippedDir = unzip_from_path(subZip)
        except Exception as e:
            print(e)
            quit()
    else:
    # working directory not a path
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

def error_search(keywords: List[str], errorLine: str) -> bool:
    """
    Takes a set of keywords and the current error line and checks if a keyword in the set is within the error line.
    
    returns true if a keyword is found.
    """
    for key in keywords:
        if errorLine.find(key) != -1: return True
    return False

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

def date_to_epoch(date: str) -> float:
    """
    Takes a formatted time (d:h:m:s) and returns a float in epoch time (seconds since 1/1/1970)
    """
    times = date.split(":")
    days  = int(times[0]) * (60*60*24)
    hours = int(times[1]) * (60*60)
    mins  = int(times[2]) * (60)
    secs  = float(times[3])

    return days + hours + mins + secs

def row_to_string(row: ndarray) -> str:
    """
    Converts a row from a Dataframe into strings.
    """
    finalstr = ""
    for elem in row:
        finalstr += str(elem) + " "

    return finalstr

def print_students_info(students: List[student], dir: str) -> None:
    """
    Prints some information about a list of students\n
    Arguements:
        - `students: List[student]` is the list of students the function will calculate data from.
        - `dir: str` is the directory the student's were originally located.
    """

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
    print(CITALIC + "For students in " + CYELLOW + "\"" + dir + "\" " + CEND + ":\n")

    print("Toral Number of Students:\t"    + CWHITEBG + CBLACK + "{:3d}".format(len(students))  + CEND)
    print("Total Number of Submissions:\t" + CWHITEBG + CBLACK + "{:3d}".format(sum(totalSubs)) + CEND + "\n")

    print(CBOLD + "Average total worktime:\t\t\t"          + CEND, epoch_to_date(average(workTimes)))
    print(CBOLD + "Average time per Submissions:\t\t"      + CEND, epoch_to_date(average(subTimes)))
    print(CBOLD + "Average Compilation Rate:\t\t"          + CEND, "{:5.2f}".format(totalComp / sum(totalSubs)*100) + " %")
    print(CBOLD + "Average # of submission per student:\t" + CEND, "{:4.2f}".format(average(totalSubs)) + CEND)
    print()




#-#-#- Main Functions of the Script  -#-#-#
def proc_single(workingDir: str, proc_errors: bool = False, from_excel: bool = False):
    """
    Compiles a single set.\n
    Arguements:
        - `workingDir: str` should be the name to a zipfile in the current directory or a path to a zipfile from the root directory.
        - `proc_errors: bool` is used to process errors (Optional).
        - `from_excel: bool` used to denote when students are sourced from excel file. (Optional).

    Generates an excel output for the set and prints basic information gathered from the students.\n
    Returns a dataframe of the students (same dataframe that is output as an excel) 
    """
    
    if from_excel:
        students = get_students(workingDir, proc_errors, from_excel)
        print_students_info(students, workingDir)
    else:
        unzippedDir = unzip_submissions(workingDir)
        students = get_students(unzippedDir, proc_errors, from_excel)
        print_students_info(students, unzippedDir)
    

    # create dataframe containing all students from set
    dfs = [s.to_DataFrame() for s in students]
    df  = concat(dfs, axis=0)

    # output current dataset as excel
    if not from_excel: df.to_excel(f"{unzippedDir} output.xlsx", sheet_name = "Submission Analysis", index = False)
    else:              print(df)
    
    return df
    
def proc_multi(workingDir: str = False, proc_errors: bool = False):
    """
    Compiles multiple datasets.\n
    Arguements:
        - `workingDir: str` should be the name to a zipfile in the current directory or a path to a zipfile from the root directory.
        - `proc_errors: bool` is used to process errors (Optional).

    Generates an excel output for each set, as well as one containing all sets together.
    """
    
    os.chdir(workingDir)

    # create list to contain students from all datasets
    dfs = list()

    for zipfile in os.listdir():
        if not zipfile.endswith(".zip"): continue
        
        try:
            dfs.append(proc_single(zipfile, proc_errors, False))
        except Exception:
            print("[ERROR]: " + zipfile + " analysis failed")
            continue

    # output all students in all datasets in single excel
    df  = concat(dfs, axis=0)
    df.to_excel("Multiple Dataset output.xlsx", sheet_name = "Submission Analysis", index = False)

    
def debug(workingDir: str, proc_errors: bool, multiSet: bool, fromExcel: bool):
    """
    Method used for debugging.\n
    No real functionalities    
    """
    students = get_students(workingDir, proc_errors, fromExcel)
    print_students_info(students, workingDir)


#-#-#-  Call to '__main__' function   #-#-#
if __name__ == '__main__':
    start    = time()

    args        = get_args()
    workingDir  = args.workingDir
    proc_errors = args.errorProc 
    multiSet    = args.multiSet
    debugging   = args.debugging
    fromExcel   = args.fromExcel

    if   debugging:   debug(workingDir, proc_errors, multiSet, fromExcel)
    elif multiSet:    proc_multi(workingDir, proc_errors)
    else:             proc_single(workingDir, proc_errors, fromExcel)

    end     = time()
    run     = end - start
    print("Total runtime - " + "{:1d}".format(int(run/60)) + " minutes and " + "{:5.2f}".format(run%60) + " seconds.")
