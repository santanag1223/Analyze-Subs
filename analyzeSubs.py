import os 
import argparse
from plistlib import InvalidFileException
from shutil   import rmtree, copy
from typing   import List
from time     import time
from numpy    import average, nan
from pandas   import DataFrame, concat
from tqdm     import tqdm



#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#-#-#- submission and student Classes #-#-#
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

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
    timeCreated = 0.000000000000
    compiled    = False
    error       = "Not Processed"
    errorLine   = ""

    def __init__(self, folder: str):
            self.sub_folder  = folder
            nozip            = folder.replace(".zip","")
            self.subNum      = int(nozip.split("_")[1])
            self.compiled    = self.try_compile()

    def try_compile(self)-> bool:
        """
        Attempts compilation of submission.\n
        returns True if 'a.out' is created after compilation.\n
        calls 'get_error()' function if a.out not produced. 
        """

        # precausion for zipping error submission
        try:
            temp = unzip_folder(self.sub_folder)
        except Exception: 
            self.error = "Could Not Unzip"
            return False
        
        # go into unzipped folder
        os.chdir(temp)

        # get time created (seconds since creation) (unzipping process makes this current time)
        self.timeCreated = os.path.getmtime(os.listdir()[0])

        # call compilation and check for 'a.out'
        os.system("g++ -std=c++17 *.cpp -w 2>err.txt -O0")

        if "a.out" in os.listdir(): 
            compiled    = True
            if (ERROR_PROC): self.error  = "No Error"
        else:
            compiled    = False
            if (ERROR_PROC): self.error  = self.get_error()

        # exit the unzipped folder and delete it
        os.chdir("..")
        try:   rmtree(temp)
        except PermissionError: pass

        # return if submissions compiled
        return compiled

    def get_error(self) -> str:
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
    student class acts like a container for each student's submissions and basic info about student

    Each student holds:
    - Student ID
    - All of the student's submissions
    - Compile Rate
    - time between first and last submission (unzipping causes conflict)
    - average time between submissions (unzipping causes conflict)
    """

    studentID = ""
    compRate  = 1.00
    numOfSubs = 0
    workTime  = 0.0
    avgTime   = 0.0
    subs      = list()


    def __init__(self, folder: str):
        """student constructor expects a student directory from an unzipped data set"""
        self.studentID = folder.split(" ")[1]
        self.__get_subs(folder)
        self.__set_times()

    def __get_subs(self, folder: str):

        # enter student's directory
        os.chdir(folder)

        # make sure file system is sorted
        subZips = os.listdir()
        subZips.sort()

        self.numOfSubs = len(subZips)
        compiledSubs   = 0


        # if we are compiling all submissions, calculate compile rate
        if ALL_SUBS:
            for subZip in tqdm(subZips, desc = "Submissions Processed", unit = "Submission"):
                if not subZip.endswith(".zip"): continue
                currentSub = submission(subZip)

                # count compiled submissions
                if currentSub.compiled: compiledSubs += 1

                # add to student's submissions
                self.subs.append(currentSub)
                            
            self.compRate = compiledSubs / self.numOfSubs

        # otherwise, we only append the final submission to student's list
        else:
            currentSub = submission(subZips[-1])
            self.subs.append(currentSub)

            # calculate compile rate out of 1
            if currentSub.compiled: self.compRate = 1   
            else:                   self.compRate = 0

        # return to beginning directory
        os.chdir("..")

    def __set_times(self):

        if ALL_SUBS:
            self.workTime = self.subs[-1].timeCreated - self.subs[0].timeCreated

        # calculate average submission time
        times    = list()
        lastTime = None
        for sub in self.subs:
            if lastTime == None:
                lastTime = sub.timeCreated
            else:
                times.append(abs(lastTime - sub.timeCreated))
                lastTime = sub.timeCreated

        self.avgTime  = (average(times))

    def print_info(self):

        print("Student", self.studentID, ":")
        print("# of Subs:", self.numOfSubs)
        print("Compile Percentage: {:02.2f}".format(self.compRate * 100) + " %")
        print("Total Time Working:\t", epoch_to_date(self.workTime))
        print("Avg time per submission:", epoch_to_date(self.avgTime))
        print()

def get_args():
    """
    Parses command line and returns parser object.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("workingDir"        , help = "zipped submissions file in current directory or full path to file", type = str)
    parser.add_argument("-a", "--allSubs"   , help = "compile all submissions"     , action = "store_true")
    parser.add_argument("-m", "--multiSet"  , help = "Folder to multiple sets"     , action = "store_true")
    parser.add_argument("-e", "--errorProc" , help = "Processes submission errors" , action = "store_true")
    args   = parser.parse_args()
    return args

def get_students(studentsDir: str) -> List[student]:
    
    students = list()
    
    os.chdir(studentsDir)
    for s in tqdm(os.listdir(), desc = "Students Processed", unit = "Student"):
        if not s.startswith("Student"): continue
        students.append(student(s))

    os.chdir("..")

    return students


##########################################################
##  UPDATE Student lists and Student_to_Sheet Function  ##
##########################################################

def subs_to_sheet(subDir: str, submissions: List[submission], numOfSets: int = 0):
    """
    Takes the submission.zip filename and the processed submissions and creates excel spreadsheet with all submissions data.
    """

    students         , subNums              = list(), list()
    subCompiles      , subErrors            = list(), list()
    errorLines       , failedList           = list(), list()
    syntaxErrors     , typeErrors           = 0, 0
    scopeErrors      , conversionErrors     = 0, 0
    noModuleErrors   , missingFileErrors    = 0, 0
    exitStatus1Errors, unknownErrors        = 0, 0 - numOfSets
    currStudent      , lastSub              = "", None
    consecFailed = 0

    for sub in submissions:
        
        # Lists the student IDs correctly
        if sub.studentID != currStudent:
            students.append(sub.studentID)
            currStudent = sub.studentID
        else:
            students.append(nan)
        
        # Lists the rest of the Data
        subNums.append(sub.subNum)
        subCompiles.append(sub.is_compiled)
        subErrors.append(sub.error)
        errorLines.append(sub.errorLine)

        # Get number of consecutive non-compiling subs
        if ALL_SUBS:
            if lastSub != None:
                if (subs_failed(lastSub,sub) and same_student(lastSub,sub)):
                    consecFailed += 1
                elif same_student(lastSub,sub) == False:
                    failedList.append(consecFailed)
                    consecFailed = 0                

        # Gets number of each error
        err = sub.error
        if err == "No Error":
            pass
        elif err == "Syntax Error":
            syntaxErrors += 1
        elif err == "Type Error":
            typeErrors  += 1
        elif err == "Scope Error":
            scopeErrors += 1
        elif err == "Converson Error":
            conversionErrors += 1
        elif err == "NoModuleFound Error":
            noModuleErrors   += 1
        elif err == "FileNotFound Error":
            missingFileErrors += 1
        elif err == "Exit Status 1 Error":
            exitStatus1Errors += 1
        else:
            unknownErrors += 1
        
        lastSub = sub

    totalErr = unknownErrors + exitStatus1Errors + missingFileErrors + conversionErrors + scopeErrors + typeErrors + syntaxErrors
    totalSub = len(submissions) - numOfSets

    # Main DataFrame to hold Sub Analysis Data
    mainDF = DataFrame({
        "Student IDs"        : students,
        "submission #"       : subNums,
        "submission Compiles": subCompiles,
        "submission Error"   : subErrors,
        "Error Line"         : errorLines
    })

    # Blank DataFrame for clearer exporting to Excel
    blankDF = DataFrame({"":[]})

    # DataFrames to hold error data
    try: dataDF = DataFrame({
        "Total submissions"     : [totalSub         , nan                       , nan                       ],
        ""                      : ["Error Count:"   , "Percent of Errors"      ,"Percent of all Submissions"],
        "Syntax Errors"         : [syntaxErrors     , "{0:.0f}%".format(syntaxErrors/totalErr*100)     , "{0:.0f}%".format(syntaxErrors/totalSub*100)     ],
        "Type Errors"           : [typeErrors       , "{0:.0f}%".format(typeErrors/totalErr*100)       , "{0:.0f}%".format(typeErrors/totalSub*100)       ],
        "Scope Errors"          : [scopeErrors      , "{0:.0f}%".format(scopeErrors/totalErr*100)      , "{0:.0f}%".format(scopeErrors/totalSub*100)      ],
        "Conversion Errors"     : [conversionErrors , "{0:.0f}%".format(conversionErrors/totalErr*100) , "{0:.0f}%".format(conversionErrors/totalSub*100) ],
        "NoModuleFound Errors"  : [noModuleErrors   , "{0:.0f}%".format(noModuleErrors/totalErr*100)   , "{0:.0f}%".format(noModuleErrors/totalSub*100)   ],
        "FileNotFound Errors"   : [missingFileErrors, "{0:.0f}%".format(missingFileErrors/totalErr*100), "{0:.0f}%".format(missingFileErrors/totalSub*100)],
        "Exit Status 1 Errors"  : [exitStatus1Errors, "{0:.0f}%".format(exitStatus1Errors/totalErr*100), "{0:.0f}%".format(exitStatus1Errors/totalSub*100)],
        "Unknown Errors"        : [unknownErrors    , "{0:.0f}%".format(unknownErrors/totalErr*100)    , "{0:.0f}%".format(unknownErrors/totalSub*100)    ],
        "Total Errors"          : [totalErr         , 1                                                , "{0:.0f}%".format(totalErr/totalSub*100)          ],
        })
    except ZeroDivisionError:
        totalErr = 1
        dataDF = DataFrame({
        "Total submissions"     : [totalSub         , nan                       , nan                       ],
        ""                      : ["Error Count:"   , "Percent of Errors:"    ,"Percent of all Submissions:"],
        "Syntax Errors"         : [syntaxErrors     , "{0:.0f}%".format(syntaxErrors/totalErr*100)     , "{0:.0f}%".format(syntaxErrors/totalSub*100)     ],
        "Type Errors"           : [typeErrors       , "{0:.0f}%".format(typeErrors/totalErr*100)       , "{0:.0f}%".format(typeErrors/totalSub*100)       ],
        "Scope Errors"          : [scopeErrors      , "{0:.0f}%".format(scopeErrors/totalErr*100)      , "{0:.0f}%".format(scopeErrors/totalSub*100)      ],
        "Conversion Errors"     : [conversionErrors , "{0:.0f}%".format(conversionErrors/totalErr*100) , "{0:.0f}%".format(conversionErrors/totalSub*100) ],
        "NoModuleFound Errors"  : [noModuleErrors   , "{0:.0f}%".format(noModuleErrors/totalErr*100)   , "{0:.0f}%".format(noModuleErrors/totalSub*100)   ],
        "FileNotFound Errors"   : [missingFileErrors, "{0:.0f}%".format(missingFileErrors/totalErr*100), "{0:.0f}%".format(missingFileErrors/totalSub*100)],
        "Exit Status 1 Errors"  : [exitStatus1Errors, "{0:.0f}%".format(exitStatus1Errors/totalErr*100), "{0:.0f}%".format(exitStatus1Errors/totalSub*100)],
        "Unknown Errors"        : [unknownErrors    , "{0:.0f}%".format(unknownErrors/totalErr*100)    , "{0:.0f}%".format(unknownErrors/totalSub*100)    ],
        "Total Errors"          : [0                , 1                                                , 0                                                ],
        })
    

    # Dataframe to hold Concurent Failed submissions
    if ALL_SUBS:
        try:
            avgConsecFail = sum(failedList)/len(failedList)
            maxFailed     = max(failedList)
        except Exception:
            avgConsecFail = 0
            maxFailed     = 0
        consecFailedDF = DataFrame({
            "Avg Consecutive Failed Subs" : [avgConsecFail]  ,
            "Max Consecutive Failed Subs" : [maxFailed]      ,
        })
        finalDF = concat([mainDF, blankDF, dataDF,blankDF,consecFailedDF], axis = 1)
    else:
        finalDF = concat([mainDF, blankDF, dataDF                       ], axis = 1)

    try:
        finalDF.to_excel(f"{subDir} submission Analysis.xlsx"       , sheet_name = "Submission Analysis", index = False)
    except PermissionError:
        print("[ERROR] - A previous version of the spreadsheet is open\ncreating a temp spreadsheet...")
        finalDF.to_excel(f"{subDir}_TEMP submission Analysis.xlsx"  , sheet_name = "Submission Analysis", index = False)



#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#-#-#-        Helper Functions       -#-#-#
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

def is_path(dir: str) -> bool:
    """
    Checks if string is a path to a directory, returns True if '/' is present in the string.
    """
    if '/' in dir:  return True
    else:           return False

def unzip_from_path(zip_path: str) -> str:
    """
    Copies '.zip' from another directory into current directory and unzips locally.\n
    deletes the '.zip' folder copied over after unzipping it

    returns new unzipped folder name
    """
    start_dir = os.getcwd()
    
    os.chdir('/')                                   # go to root dir
    copy(zip_path,start_dir)                        # copy zipfile to our current dir
    os.chdir(start_dir)                             # return to working dir

    zipFolder = os.path.basename(zip_path)          # get our zipfolder name from path
    zipFolder = unzip_folder(zipFolder)             # unzip folder and rename our zipFolder

    os.remove(zipFolder + '.zip')                   # delete the copied over zip

    return zipFolder                                # return working unzip file

def unzip_folder(zipfile: str) -> str:
    """
    Unzips folder inside of current directory.
    
    returns new unzipped folder name
    """

    if not zipfile.endswith(".zip"): raise InvalidFileException("ERROR: Non zipfile can not be unzipped.")

    newfile = zipfile.replace('.zip','')
    os.mkdir(newfile)
    os.system("unzip -q " + zipfile + " -d " + newfile)
    return newfile

def error_search(keywords: List[str], errorLine: str) -> bool:
    """
    Takes a set of keywords and the current error line and checks if a keyword in the set is within the error line.
    
    returns true if a keyword is found.
    """
    for key in keywords:
        if errorLine.find(key) != -1: return True
    return False

def subs_failed(sub1: submission, sub2: submission) -> bool:
    """
    Checks if two submissions both could not be compiled.
    """
    return (sub1.is_compiled == False) and (sub2.is_compiled == False)

def same_student(sub1: submission, sub2: submission) -> bool:
    """
    Checks if two submissions have the same author.
    """
    return (sub1.studentID == sub2.studentID)

def epoch_to_date(epoch: float) -> str:
    """
    Takes a epoch time in seconds and returns a string with the epoch amount in days, hours, minutes, and seconds.
    """
    days  =  int(epoch / (60*60*24))
    epoch -= days * (60*60*24)
    hours =  int(epoch / (60*60))
    epoch -= hours * (60*60)
    mins  =  int(epoch / 60)
    epoch -= mins * (60)
    secs  =  epoch

    return "{:1d} days {:2d} hrs {:2d} mins {:02.2f} secs".format(days, hours, mins, secs)

def print_avg_student_info(students: List[student]) -> None:
    """
    Takes a list of students and prints information about the students
    """

    workTimes = list()
    subTimes  = list()
    compRates = list()
    numOfSubs = list()
    for s in students:
        workTimes.append(s.workTime)
        subTimes.append(s.avgTime)
        compRates.append(s.compRate)
        numOfSubs.append(s.numOfSubs)

    print()
    print(CITALIC + "For students in " + CYELLOW + "\"" + WORKING_DIR + "\" " + CEND + ":\n")

    print("Toral Number of Students:\t"    + CWHITEBG + CBLACK + str(len(students))  + CEND)
    print("Total Number of Submissions:\t" + CWHITEBG + CBLACK + str(sum(numOfSubs)) + CEND + "\n")

    print(CBOLD + "Average total worktime:\t\t\t"          + CEND, epoch_to_date(average(workTimes)))
    print(CBOLD + "Average time per Submissions:\t\t"      + CEND, epoch_to_date(average(subTimes)))
    print(CBOLD + "Average Compilation Rate:\t\t"          + CEND, "{:02.2f}".format(average(compRates) * 100) + " %")
    print(CBOLD + "Average # of submission per student:\t" + CEND, "{:02.2f}".format(average(numOfSubs)) + CEND)
    print()



#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#-#-#- Main Functions of the Script  -#-#-#
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

def proc_single():
    
    if is_path(WORKING_DIR):
    # working directory is a path
        try:
            unzippedDir = unzip_from_path(WORKING_DIR)
        except FileNotFoundError as e:
            print(f"Directory '{WORKING_DIR}' could not be found.\n" + e)
            quit()
    else:
    # working directory not a path
        try:
            unzippedDir = unzip_folder(WORKING_DIR)
        except FileNotFoundError as e:
            print(f"Directory '{WORKING_DIR}' could not be found.\n" + e)
            quit()
        except InvalidFileException as e:
            print(f"'{WORKING_DIR}' could not be unzipped.\n" + e)
            quit()

    students = get_students(unzippedDir)

    print_avg_student_info(students)

    rmtree(unzippedDir)    


    ##########################################################
    ##  UPDATE Student lists and Student_to_Sheet Function  ##
    ##########################################################
    
def proc_multi():
    """
    Compiles submissions from mulitple datasets and `outputs` to one excel sheet.
    - Assumes subdir passed is a directory with multiple datasets.
    - Compiles all submissions.
    """

    subs        = list()

    os.chdir(WORKING_DIR)
    sets = 0

    ##########################################################
    ##  UPDATE Student lists and Student_to_Sheet Function  ##
    ##########################################################

def debug():
    studentsDir = unzip_folder(WORKING_DIR)
    os.chdir(studentsDir)

    s = student(os.listdir()[2])
    ss = list()
    ss.append(s)
    print_avg_student_info(ss)

    os.chdir("..")
    rmtree(studentsDir)    



#-#-#- Global Variables for Script Arguements -#-#-#
args        = get_args()
WORKING_DIR = args.workingDir
ERROR_PROC  = args.errorProc 
ALL_SUBS    = args.allSubs
MUTISET     = args.multiSet

#-#-#- Global Variables for text formatting -#-#-#
CEND    = '\33[0m'
CITALIC = '\33[3m'
CBLACK  = '\33[30m'
CYELLOW = '\33[33m'
CWHITE  = '\33[37m'
CBOLD   = '\33[1m'
CWHITEBG  = '\33[47m'

#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#-#-#-  Call to '__main__' function   #-#-#
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

if __name__ == '__main__':
    start    = time()
    
    if MUTISET:     proc_multi()
    else:           proc_single()
    #debug()

    end     = time()
    run     = end - start
    print("Total runtime - " + "{:1d}".format(int(run/60)) + " minutes and " + "{:02.2f}".format(run%60) + " seconds.")
