import os 
import shutil
import argparse
from typing import List
from time   import time
from numpy  import nan
from pandas import DataFrame, concat
from tqdm   import tqdm
from numpy.core.numeric import NaN

### submission class
class submission:
    """
    submission Class acts as a container for all submission data.\n

    Each submissions holds:
    - Student ID
    - submission Folder Name
    - submission Number
    - Compiled Boolean
    - Error Type
    - Error Line
    """

    studentID   = ""
    sub_folder  = ""
    subNum      = -1
    is_compiled = False
    error       = ""
    errorLine   = ""

    def __init__(self, studentID: str, folder: str):
        self.studentID   = studentID
        self.sub_folder  = folder
        nozip            = folder.replace(".zip","")
        self.subNum      = int(nozip.split("_")[1])
        self.is_compiled = self.try_compile()

    def try_compile(self)-> bool:
        """
        Attempts compilation of submission.\n
        returns True if 'a.out' is created after compilation.\n
        calls 'get_error()' function if a.out not produced. 
        """

        # precausion for unzipped submission
        try:
            temp = unzip_folder(self.sub_folder)
        except Exception: 
            self.error = "SUB NOT .ZIP"
            return False
        
        os.chdir(temp)
        os.system("g++ -std=c++17 *.cpp -w 2>err.txt -O0")

        if "a.out" in os.listdir(): 
            compiled    = True
            self.error  = "No Error"
        else:
            compiled    = False
            self.error  = self.get_error()

        os.chdir("..")
        try:   shutil.rmtree(temp)
        except PermissionError: pass

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



def get_args():
    """
    Parses command line and returns parser object.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("subdir"     , help = "zipped submissions file in current directory or full path to file", type = str)
    parser.add_argument('-a', "--all", help = "compile all submissions", action = "store_true")
    args   = parser.parse_args()
    return args

def comp_final_subs(studentsDir) -> List[submission]:
    """
    Takes the submissions .zip file and processes only the final submission of each student, returing a list of submissions.
    """

    submissions = list()

    os.chdir(studentsDir)
    for student in tqdm(os.listdir(), desc = "Final Submissions", unit = "Student"):
        
        # go into each student dir 
        os.chdir(student)       
        
        # get our final sub
        finalSub = os.listdir()[-1]
        submissions.append(submission(student, finalSub))

        # steps back a directory
        os.chdir('..')                              

    os.chdir('..')
    try:   shutil.rmtree(studentsDir)
    except PermissionError: pass 

    return submissions
        
def comp_all_subs(studentsDir) -> List[submission]:
    """
    Takes the submissions .zip file and processes all submissions, returning a list of submissions.
    """

    submissions = list() 
    
    os.chdir(studentsDir)
    for student in tqdm(os.listdir(), desc = "All Students", unit = "Student"):
        os.chdir(student) 
        for sub in tqdm(os.listdir(), desc = "Current Student's submissions", leave = False, unit = "submission"):
            submissions.append(submission(student, sub))
        
        os.chdir('..')

    os.chdir('..')
    try:   shutil.rmtree(studentsDir)
    except PermissionError: pass

    return submissions

def subs_to_sheet(subDir: str, allSubs: bool, submissions: List[submission]):
    """
    Takes the submission.zip filename and the processed submissions and creates excel spreadsheet with all submissions data.
    """

    students         , subNums              = list(), list()
    subCompiles      , subErrors            = list(), list()
    errorLines       , failedList           = list(), list()
    syntaxErrors     , typeErrors           = 0, 0
    scopeErrors      , conversionErrors     = 0, 0
    noModuleErrors   , missingFileErrors    = 0, 0
    exitStatus1Errors, unknownErrors        = 0, 0 
    currStudent      , lastSub              = "", None
    consecFailed = 0

    for sub in submissions:
        
        # Lists the student IDs correctly
        if sub.studentID != currStudent:
            students.append(sub.studentID)
            currStudent = sub.studentID
        else:
            students.append(NaN)
        
        # Lists the rest of the Data
        subNums.append(sub.subNum)
        subCompiles.append(sub.is_compiled)
        subErrors.append(sub.error)
        errorLines.append(sub.errorLine)

        # Get number of consecutive non-compiling subs
        if allSubs:
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
    totalSub = len(submissions)

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
        ""                      : ["Error Count:"   , "Percent of Errors"       ,"Percent of all Submissions"],
        "Syntax Errors"         : [syntaxErrors     , syntaxErrors/totalErr     , syntaxErrors/totalSub     ],
        "Type Errors"           : [typeErrors       , typeErrors/totalErr       , typeErrors/totalSub       ],
        "Scope Errors"          : [scopeErrors      , scopeErrors/totalErr      , scopeErrors/totalSub      ],
        "Conversion Errors"     : [conversionErrors , conversionErrors/totalErr , conversionErrors/totalSub ],
        "NoModuleFound Errors"  : [noModuleErrors   , noModuleErrors/totalErr   , noModuleErrors/totalSub   ],
        "FileNotFound Errors"   : [missingFileErrors, missingFileErrors/totalErr, missingFileErrors/totalSub],
        "Exit Status 1 Errors"  : [exitStatus1Errors, exitStatus1Errors/totalErr, exitStatus1Errors/totalSub],
        "Unknown Errors"        : [unknownErrors    , unknownErrors/totalErr    , unknownErrors/totalSub    ],
        "Total Errors"          : [totalErr         , totalErr/totalErr         , totalErr/allSubs          ],
        })
    except ZeroDivisionError:
        totalErr = 1
        dataDF = DataFrame({
        "Total submissions"     : [totalSub         , nan                       , nan                       ],
        ""                      : ["Error Count:"   , "Percent of Errors:"    ,"Percent of all Submissions:"],
        "Syntax Errors"         : [syntaxErrors     , syntaxErrors/totalErr     , syntaxErrors/totalSub     ],
        "Type Errors"           : [typeErrors       , typeErrors/totalErr       , typeErrors/totalSub       ],
        "Scope Errors"          : [scopeErrors      , scopeErrors/totalErr      , scopeErrors/totalSub      ],
        "Conversion Errors"     : [conversionErrors , conversionErrors/totalErr , conversionErrors/totalSub ],
        "NoModuleFound Errors"  : [noModuleErrors   , noModuleErrors/totalErr   , noModuleErrors/totalSub   ],
        "FileNotFound Errors"   : [missingFileErrors, missingFileErrors/totalErr, missingFileErrors/totalSub],
        "Exit Status 1 Errors"  : [exitStatus1Errors, exitStatus1Errors/totalErr, exitStatus1Errors/totalSub],
        "Unknown Errors"        : [unknownErrors    , unknownErrors/totalErr    , unknownErrors/totalSub    ],
        "Total Errors"          : [0                , totalErr/totalErr         , 0/totalSub                ],
        })
    

    # Dataframe to hold Concurent Failed submissions
    if allSubs:
        try:
            avgConsecFail = sum(failedList)/len(failedList)
        except ZeroDivisionError:
            avgConsecFail = 0
        consecFailedDF = DataFrame({
            "Avg Consecutive Failed Subs" : [avgConsecFail]  ,
            "Max Consecutive Failed Subs" : [max(failedList)],
        })
        finalDF = concat([mainDF, blankDF, dataDF,blankDF,consecFailedDF], axis = 1)
    else:
        finalDF = concat([mainDF, blankDF, dataDF                       ], axis = 1)

    try:
        finalDF.to_excel(f"{subDir} submission Analysis.xlsx"       , sheet_name = "Submission Analysis", index = False)
    except PermissionError:
        print("[ERROR] - A previous version of the spreadsheet is open\ncreating a temp spreadsheet...")
        finalDF.to_excel(f"{subDir}_TEMP submission Analysis.xlsx"  , sheet_name = "Submission Analysis", index = False)



### helper functions
def is_path(dir: str) -> bool:
    """
    Checks if string is a path to a directory, returns True if '/' is present in the string.
    """
    if '/' in dir:  return True
    else:           return False

def unzip_from_path(zip_path: str) -> str:
    """
    Copies '.zip' from another directory into current directory and unzips locally.\n
    deletes the '.zip' folder copied over after unzipping it\n
    returns new unzipped folder name
    """
    start_dir = os.getcwd()
    
    os.chdir('/')                                   # go to root dir
    print("copying file from path...")
    shutil.copy(zip_path,start_dir)                 # copy zipfile to our current dir
    os.chdir(start_dir)                             # return to working dir

    zipFolder = os.path.basename(zip_path)          # get our zipfolder name from path
    print("unzipping file...")
    zipFolder = unzip_folder(zipFolder)             # unzip folder and rename our zipFolder

    os.remove(zipFolder + '.zip')                   # delete the copied over zip

    return zipFolder                                # return working unzip file

def unzip_folder(zipFile: str) -> str:
    """
    Unzips folder inside of current directory\n
    returns new unzipped folder name
    """

    nozip = zipFile.replace('.zip','')
    shutil.unpack_archive(zipFile, nozip,'zip')
    return nozip

def error_search(keywords: List[str], errorLine: str) -> bool:
    """
    Takes a set of keywords and the current error line and checks if a keyword in the set is within the error line.\n
    returns true if a keyword is found.
    """
    for key in keywords:
        if errorLine.find(key) != -1: return True
    return False

def subs_failed(sub1: submission, sub2: submission) -> bool:
    """Checks if two submissions both could not be compiled."""
    return (sub1.is_compiled == False) and (sub2.is_compiled == False)

def same_student(sub1: submission, sub2: submission) -> bool:
    """Checks if two submissions have the same author."""
    return (sub1.studentID == sub2.studentID)


def main():
    args        = get_args()
    studentsDir = args.subdir
    allSubs     = args.all
    
    # check if arg is a path or folder in dir
    if is_path(studentsDir):
        # try to unzip file to folder in dir
        try:                
            studentsDir = unzip_from_path(studentsDir)
        except FileNotFoundError as e:
            print(f"Directory '{studentsDir}' could not be found.\n",e)
            quit()
    else:
        try:
            print("unzipping file...")
            studentsDir = unzip_folder(studentsDir)
        except FileNotFoundError as e: 
            print(f"Directory '{studentsDir}' could not be found.\n",e)
            quit()
        except shutil.ReadError as e:
            print(f"'{studentsDir}' could not be unzipped.\n",e)
            quit() 
    
    if allSubs: submissions = comp_all_subs(studentsDir)
    else:       submissions = comp_final_subs(studentsDir)

    subs_to_sheet(studentsDir, allSubs, submissions)



### call to main function
if __name__ == '__main__':
    start   = time()
    main()
    end     = time()
    run     = end - start
    print(f"Total runtime - {int(run/60)}:{int(run % 60)}")
