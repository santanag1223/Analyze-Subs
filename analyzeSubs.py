import os 
import shutil
import argparse
from time import time
from pandas import DataFrame, concat
from tqdm import tqdm
from numpy.core.numeric import NaN


# pass args through argparse 
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("subdir"     , help = "zipped submissions data file or path to file", type = str)
    parser.add_argument('-a', "--all", help = "compile all submissions", action = "store_true")
    args   = parser.parse_args()
    return args

# returns if the argument is a path or not
def is_path(str):
    if '/' in str:  return True
    else:           return False

# return unzipped folder in current dir from a path to a zip
def unzip_from_path(zip_path):
    
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

# unzip current folder and return new name
def unzip_folder(zipFile):
    nozip = zipFile.replace('.zip','')
    shutil.unpack_archive(zipFile, nozip)
    return nozip

# compiles a zipped submission folder / returns 1 for compiling and 0 for not
def comp_sub(zippedSub):
    try   : temp = unzip_folder(zippedSub)          # unzip folder to new dir
    except: return -1                               # if not a zip file, return -1
    
    os.chdir(temp)                                  # open unzipped folder
    os.system("g++ -std=c++17 *.cpp -w 2> /dev/null") # try to compile cpp files

    if "a.out" in os.listdir():                     # if a.out exists, return 1 for compiling
        compiled = 1
    else:                                           # otherwise, return 0 for not compiling
        compiled = 0
    
    os.chdir('..')                                  # return to starting dir
    shutil.rmtree(temp)                             # delete temp folder

    return compiled                                 # return 1 or 0

# compiles every student's last sub in students dir | returns list of 1s and 0s
# returns 2 lists: [studentIDs, finalCompiles]
def comp_final_subs(studentsDir):
    studentIDs    = []
    finalCompiles = []
    totSubs       = 0

    os.chdir(studentsDir)
    for student in tqdm(os.listdir(), desc = "Student's Final Submissions",unit = "Student"):
        os.chdir(student)                           # go into each student dir
        studentIDs.append(student)                  # add student student to list
        
        totSubs += len(os.listdir())                # count how many subs in each dir

        finalSub = os.listdir()[-1]                 # get our final sub
        finalCompiles.append(comp_sub(finalSub))
        
        os.chdir('..')                              # steps back a directory
    return studentIDs, finalCompiles, totSubs
        
# compiles all zipped subs for each student in students dir
# returns 3 lists: [studentIDs, finalCompiles, allCompiles]
def comp_all_subs(studentsDir):
    studentIDs = []
    subNums    = []
    compiles   = []
    totSubs    = 0
    
    os.chdir(studentsDir)
    for student in tqdm(os.listdir(), desc = "All Students", unit = "Student"):
        os.chdir(student)                           # enter each student folder
        
        studentIDs.append(student)                  # add student to list of IDs
        subNums.append(NaN)
        compiles.append(NaN)
        subNum   = 1                  
        totSubs += len(os.listdir())

        for sub in tqdm(os.listdir(), desc = "Current Student's Submissions", leave = False, unit = "Submission"):
            compiles.append(comp_sub(sub))          # add whether each sub compiles or not
            subNums.append(subNum)                  # add submission num to list
            studentIDs.append('')                   # add blank student name to list
            subNum += 1                             # iterate counter
        
        os.chdir('..')
    return studentIDs, subNums, compiles, totSubs
 
def main():
    args       = get_args()                         # get our args from argparse
    studentDir = args.subdir
    allSubs    = args.all
    
    if is_path(studentDir):                         # check if arg is a path or folder in dir
        try:                                        # try to unzip folder from path
            studentDir = unzip_from_path(studentDir)
        except FileNotFoundError: 
            print(f"Directory '{studentDir}' doesn't exsist or couldn't be opened.")
            quit()
    
    else:
        try:                                        # try to unzip file to folder in dir
            print("unzipping file...")
            studentDir = unzip_folder(studentDir)
        except FileNotFoundError: 
            print(f"Directory '{studentDir}' doesn't exsist or couldn't be opened.")
            quit()

    # the user either wants all subs compiled, or just the final subs compiled
    if allSubs:
        IDs, subNums, compiles, totSubs = comp_all_subs(studentDir)
    else:
        IDs, finalComps, totSubs        = comp_final_subs(studentDir)

    # delete our unzipped file
    os.chdir('..')
    shutil.rmtree(studentDir) 

    # create our pandas data frames and concatenate them if necessary 
    if allSubs:    
        df = DataFrame({
            "Student IDs: "          : IDs,
            "Submission Number: "    : subNums,
            "Submission Compiles:"   : compiles,
        })
        df1 = DataFrame({"": []})
        df2 = DataFrame({"Total Submissions" : [totSubs] })
        df  = concat([df,df1,df2], axis = 1)
    else:
        df = DataFrame({
            "Student IDs:"               : IDs,
            "Final Submission Compiles:" : finalComps
        })
        df1 = DataFrame({"": []})
        df2 = DataFrame({"Total Submissions" : [totSubs] })
        df  = concat([df,df1,df2], axis = 1)

    # create our excel spreadsheet
    try:
        if allSubs:
            df.to_excel(f"./{studentDir} - All Submissions.xlsx"  , sheet_name = "All Submissions"  , index = False)
        else:
            df.to_excel(f"./{studentDir} - Final Submissions.xlsx", sheet_name = "Final Submissions", index = False)
    except: 
        print("A copy of this spreadsheet already exists! Make sure to move or rename the old spreadsheet!")
        print("Creating temp.xlsx ...")
        df.to_excel(f"./temp.xlsx", sheet_name = "Submissions", index = False, )

if __name__ == '__main__':
    start_time = time()
    main()
    end_time = time()
    print("Finished!\nTotal script runtime was: ", (end_time - start_time))
