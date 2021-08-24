import os
import argparse
import shutil
from random import sample
from tqdm import tqdm

# returns args object from argparse
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("subs", help = "submissions to be anonymized and zipped")
    args   = parser.parse_args()
    return args

# returns if the string passed is a path
def is_path(pth: str):
    if '/' in pth:  return True
    else:           return False

# returns if the string passed is a zipped file
def is_zip(file: str):
    if '.zip' in file: return True
    else:             return False

# copies folder / file from path and returns basename
def copy_from_path(sub_dir: str):
    start_dir = os.getcwd()                         # save our current dir
    os.chdir("/")                                   # go to the root dir
    shutil.copy(sub_dir, start_dir)                 # copy over subs folder
    os.chdir(start_dir)                             # go back to working dir

    return os.path.basename(sub_dir)                # return new working folder

# unzips file and returns new folder name 'temp'
def unzip_folder(zipFile: str):
    nozip = zipFile.replace(".zip" ,"")
    shutil.unpack_archive(zipFile, nozip)
    return nozip

def main():
    # get args from argparse
    args = get_args()
    subs = args.subs
    wasPath = False

    # get our new temp folder
    if (not is_path(subs)) and (not is_zip(subs)):  # checks if the subs arg is just a nonzipped folder in current dir
        if subs not in os.listdir():
            print(f"Directory '{subs}' doesn't exsist in current directory.")
            quit()
        else:
            shutil.copytree(subs, subs + '_copy')           # if open folder exists, copy contents to temp folder
            subs += '_copy'

    if is_path(subs):                               # checks if subs arg is a path
        try:                                        
            subs = copy_from_path(subs)             # if path exists, we copy the basefile to our current dir
            wasPath = True                          # save that we did copy from another dir
        except :
            print(f"Directory '{subs}' doesn't exsist or couldn't be opened.")
            quit()
    
    if is_zip(subs):                                # check if the sub arg is a zip file
        try:
            print('unzipping folder...')
            subs = unzip_folder(subs)               # if is a zip, unzip and rename working file to unzipped name
            if wasPath : os.remove(subs + ".zip")   # if originally from path, we can delete our zipfile
        except:
            print(f"Directory '{subs}' doesn't exsist or couldn't be opened.")
            quit()

    os.chdir(subs)

    # list of numbers from 0 to size of dir, in random order
    size = len(os.listdir())
    possIDs = sample([i for i in range(size)], size)
    
    # for every student in subs dir / rename to vaild id
    for student in tqdm(os.listdir(), desc = "Folders Anonymized", unit = "Folders"):
        os.rename(student, "Student {:0>5}".format(possIDs.pop()))
    os.chdir("..")
    
    # zip working folder to 'subs_anonymized'
    print('creating new zip...')
    shutil.make_archive(subs + "_anonymized", "zip", subs)
    
    # delete subs
    shutil.rmtree(subs)

    
if __name__ == "__main__":
    main()