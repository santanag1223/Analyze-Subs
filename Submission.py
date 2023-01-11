"""
Homework Analyzer - Submission Class

Author: Santana Gonzales
Date: 12/16/2022
"""

import os
from typing import List
from time import time
from threading import Thread


def unzip_folder(zipfile: str) -> str:
    """
    Unzips folder inside of current directory.

    returns new unzipped folder name
    """

    newfile = zipfile.replace('.zip', '')
    os.mkdir(newfile)
    os.system("unzip -q " + zipfile + " -d " + newfile)
    return newfile


class Submission:
    """
    submission Class acts as a container for all submission data.\\
    Each submissions holds:
    - submission Folder Name
    - submission Number
    - Compiled Boolean
    - (optional) Error Type
    - (optional) Error Line
    """

    folderName = ""
    submissionNumber = 0
    timeCreated = 0.0
    compiled = None
    processErrors = False
    error = "Not Processed"
    errorLine = ""

    def __init__(self, folder: str, processErrors=False):
        """ submission constructor expects a submission zipfile (Submission_<NUM>.zip)"""
        self.folderName = folder
        nozip = folder.replace(".zip", "")
        self.submissionNumber = int(nozip.split("_")[1])
        self.processErrors = processErrors

        self.__try_compile()

    def __try_compile(self):
        """
        Attempts compilation of submission.\\
        returns True if 'a.out' is created after compilation.\\
        calls 'get_error()' function if a.out not produced. 
        """

        # precausion for zipping error submission
        try:
            temp = unzip_folder(self.folderName)
        except Exception:
            self.compiled = False
            self.error = "Could Not Unzip"
            return

        # go into unzipped folder
        os.chdir(temp)

        # get time created
        self.timeCreated = os.path.getmtime(os.listdir()[0])

        # create thread to try compile and time
        compileThread = Thread(target=self.__compile_thread_func)
        compileThread.start()

        # don't let the system try to compile for longer than 3.5 sec
        startTime = time()
        currTime = startTime
        while (currTime - startTime < 3.5):
            currTime = time()
            if not compileThread.is_alive():
                break

        if compileThread.is_alive():
            self.compiled = False
            if (self.processErrors):
                self.error = "Error when compiling"

        if self.compiled == False:
            self.error = self.__get_error()

        # exit the unzipped folder and delete it
        os.chdir("..")

        try:
            os.system("rm -rf " + temp)
        except Exception:
            pass

    def __compile_thread_func(self):

        # call compilation and check for a.out
        os.system("g++ -std=c++17 *.cpp -w 2>err.txt")

        if "a.out" in os.listdir():
            self.compiled = True
            if (self.processErrors):
                self.error = "No Error"
        else:
            self.compiled = False

    def __get_error(self) -> str:
        """
        Opens the submission's error file 'err.txt' and processes first error found.\\
        returns a preset error type based on keywords in compiler output.
        """

        syntax_keys = list({" parse error", " expected", " redefinition", " overload", " stray", " unary",
                            " token", " shadows a parameter", "not declared", "no matching",
                            " does not have any field", "return-statement", "no member", "not within",
                            " old-style", "lvalue", "read-only", "conflict"})
        type_keys = list({" type", " types"})
        scope_keys = list({"declared", " no match ", " nested too deeply",
                          "redeclaration", "previous declaration"})
        convert_keys = list({" cannot convert", "invalid conversion"})
        noMod_keys = list({" no module "})
        noFike_keys = list({" no such file "})
        exit1_keys = list({" 1 exit status"})

        try:
            with open("err.txt", "r") as file:
                for line in file.readlines():
                    if " error: " in line:
                        line = line.rstrip()
                        line = line.lower()
                        self.errorLine = line

                        if self.__error_search(syntax_keys, line):
                            return "Syntax Error"
                        if self.__error_search(type_keys, line):
                            return "Type Error"
                        if self.__error_search(scope_keys, line):
                            return "Scope Error"
                        if self.__error_search(convert_keys, line):
                            return "Converson Error"
                        if self.__error_search(noMod_keys, line):
                            return "NoModuleFound Error"
                        if self.__error_search(noFike_keys, line):
                            return "FileNotFound Error"
                        if self.__error_search(exit1_keys, line):
                            return "Exit Status 1 Error"

                        return "Unknown Error"
        except Exception:
            return "COULD NOT READ"

    def __error_search(keywords: List[str], errorLine: str) -> bool:
        """
        Takes a set of keywords and the current error line and checks if a keyword in the set is within the error line.

        returns true if a keyword is found.
        """
        for key in keywords:
            if errorLine.find(key) != -1:
                return True
        return False