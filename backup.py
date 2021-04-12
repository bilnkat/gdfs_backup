#!/usr/bin/env

import shutil
import os
from datetime import datetime
from sys import platform
import threading
import psutil
from time import sleep
import sys
import subprocess
from os.path import dirname, abspath, join

# Copies user folders to Google Drive File Stream (GDFS)

END = '\033[0m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'
UNBOLD = '\033[0m'

# Disables bold and underline strings
if sys.platform == "win32":
    END = ''
    UNDERLINE = ''
    BOLD = ''
    UNBOLD = ''

# sets now as a string as it will be added to the backup directory name
now = str(datetime.now()).replace(' ','_').replace('.', '_').replace(':', '-')

# GDFS checks
gdfs_signedin = False
gdfs_installed = False
gdfs_running = False

# checks operating system and returns the name of the OS, filepath of GDFS, and GDFS executable name.
def checkOS():
    backup_folder = f'backup_{now}'
    username = os.path.expanduser('~')
    if platform == 'win32':
        drive_letter = ''
        try:
            drive_letter = getDriveLetter()
        except:
            pass
        gdfs_drive_path = join(f'{drive_letter}', 'My Drive')
        backup_path = join(f'{gdfs_drive_path}', backup_folder)
        script_path = dirname(abspath(__file__))
        restore_file_win = f'{join(script_path, "Resources", "Restore.exe")}'
        app_cache = join(username, 'AppData\Local\Google\DriveFS')
        return {
            'name':'Windows',
            'gdfs_app_path':r'C:\Program Files',
            'gdfs_process_name':'GoogleDriveFS.exe',
            'selected_folders': ('Desktop', 'Documents', 'Pictures'),
            'backup_folder': backup_folder,
            'backup_path': backup_path,
            'gdfs_drive_path': gdfs_drive_path,
            'open_gdfs': lambda: subprocess.Popen(winAppPathFinder(r'C:\Program Files', 'GoogleDriveFS.exe')),
            'clear': lambda: os.system('cls'),
            'restore': restore_file_win,
            'app_cache': app_cache
        }
    elif platform == 'darwin':
        gdfs_drive_path = join(os.path.abspath(os.sep), 'Volumes', 'GoogleDrive', 'My Drive')
        backup_path = join(f'{gdfs_drive_path}', backup_folder)
        app_cache = join(username, 'Library/Application Support/Google/DriveFS')
        return {
            'name': 'macOS',
            'gdfs_app_path': '/Applications',
            'gdfs_process_name' : 'Google Drive',
            'selected_folders': ('Desktop', 'Documents', 'Pictures'),
            'backup_folder': backup_folder,
            'backup_path': backup_path,
            'gdfs_drive_path': gdfs_drive_path,
            'open_gdfs': lambda: subprocess.Popen(["/usr/bin/open", "/Applications/Google Drive.app"]),
            'clear': lambda: os.system('clear'),
            'restore': '/Applications/EA Basic Backup.app/Contents/Restore.zip',
            'app_cache': app_cache
        }
    else: print(f'Sorry! unknown OS {platform}')

# Finds GDFS file path if it exists
def winAppPathFinder(app_path, app_process_name):
    gdfs_paths = []
    for dirpath, dirnames, filenames in os.walk(app_path):
        for filename in filenames:
            if app_process_name in filename:
                gdfs_paths.append(os.path.join(dirpath, filename))

    return max(gdfs_paths)

def option():
    option = input(f"Press 'c' to {BOLD}continue{UNBOLD} or press any other key to {BOLD}cancel{UNBOLD}: ")
    if option.lower() == 'c':
        print('Retrying backup...')
    else:
        sys.exit("User cancelled")

# checks if GDFS is installed
def isProgramInstalled(os_ver, app_path, app_process_name, clear_terminal):
    clear_terminal()
    filexist = False
    if os_ver.lower() == 'windows':
        gdfs = []
        for dirpath, dirnames, filenames in os.walk(app_path):
            gdfs.extend([f for f in filenames if f == app_process_name])
        if gdfs:
            filexist = True
    elif os_ver.lower() == 'macos':
        if f'{app_process_name}.app' in os.listdir(app_path):
            filexist = True
    if not filexist:
        print(f'''
        {BOLD}WARNING!!!{UNBOLD} Google Drive File Stream is {BOLD}NOT INSTALLED{UNBOLD}.
        Please perform the steps below before proceeding...
        1. Install Google Drive File Stream from Software Center
        2. Launch Google Drive File Stream
        3. Sign in to Google Drive File Stream with your email and password
        4. Enter 'c' below and press Enter 
        ''')
        option()
    else:
        global gdfs_installed
        gdfs_installed = True

# checks if GDFS is running
def isProgramRunning(process_name, open_process, clear_terminal):
    clear_terminal()
    running = []
    for p in psutil.process_iter():
        try:
            if p.name():
                running.append(p._name)
        except Exception: pass
    if process_name not in running:
        print(f'''
        {BOLD}WARNING!!!{UNBOLD} {process_name} is {BOLD}NOW RUNNING{UNBOLD}.
        Please perform the steps below before proceeding...
        1. Sign in to Google Drive File Stream with your email and password
        2. Enter 'c' below and press Enter 
        ''')

        # opens GDFS
        open_process()
        option()
    else:
        global gdfs_running
        gdfs_running = True

# checks if GDFS is configured
def isSignedInToGDFS(app_cache_path, clear_terminal):
    clear_terminal()
    lst = []
    for dirpath, dirnames, filenames in os.walk(app_cache_path):
        lst.extend(filenames)
    if 'enabled' not in lst:

        print(f'''
        {BOLD}WARNING!!!{UNBOLD} Google Drive File Stream is running but {BOLD}NOT CONFIGURED{UNBOLD}.
        Please perform the steps below before proceeding...
        1. Sign in to Google Drive File Stream with your email and password
        2. Enter 'c' below and press Enter 
        ''')
        option()
    else:
        global gdfs_signedin
        gdfs_signedin = True

# Creates the backup destination folder
def createBackupFolder(backup_path):
    os.mkdir(backup_path)

# Initiate macOS folder access permissions
def accessMacOSFolders(source_path):
    for dirpath, dirnames, filenames in os.walk(source_path):
        subprocess.Popen(['ls', dirpath], stdout=subprocess.PIPE)

# gets the drive letter of GDFS path (only used when OS is Windows)
def getDriveLetter():
    cmd = 'wmic logicaldisk get deviceid, volumename  | findstr "Google Drive File Stream"'
    tempstr = os.popen(cmd).read()
    driveletter = tempstr.split()
    return driveletter[0]

# gets total size of a path and it's subpaths in bytes
def getSizeOfPath(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        filenames = [f for f in filenames if not f[0] == '.']
        for f in filenames:
            fp = os.path.join(dirpath, f)

            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

# gets size of list of paths and adds them together in bytes
def getSizeOfPaths(list_of_paths):
    total_size = 0
    for path in list_of_paths:
        total_size += getSizeOfPath(path)
    return total_size

# gets file count in directory and subdirectories
def fileCountInPath(path):
    total_files = 0
    for root, dirs, files in os.walk(path):
        files = [f for f in files if not f[0] == '.']
        total_files += len(files)
    return total_files

# gets file count in multiple directories and their subdirectories
def fileCountInPaths(list_of_paths):
    total_files_in_paths = 0
    for path in list_of_paths:
        total_files_in_paths += fileCountInPath(path)
    return total_files_in_paths

# gets a list of the source and destination
def getSourceAndDestination(user_path, destination_path, *selected_directories):
    paths = []
    for directory in selected_directories:
        source = os.path.join(user_path, directory)
        destination = os.path.join(destination_path, directory)
        paths.append((directory, source, destination))
    return paths

# shows progress bar representing the percentage value of copied so far vs total to be copied
def progress_bar(copied_so_far, total_to_be_copied, unit):
    size = os.get_terminal_size()                           # os.get_terminal_size() gets an error when running on IDE
    max_bars = size.columns * 0.25
    max_bars = int(max_bars)
    percentage = copied_so_far / total_to_be_copied * 100
    print('\r', end='')
    print('[' + '=' * int(percentage / 100 * max_bars) + ' ' * (max_bars - int(percentage / 100 * max_bars)) + ']' + "{:.2f}".format(percentage) + '%' + f'    {copied_so_far:,} {unit} of {total_to_be_copied:,} {unit}', end='')
    sleep(.5)

# another way of showing progress without percentage and a bar representation since progress_bar can be inaccurate.
def progress(copied_so_far, unit='files'):
    print('\r', end='')
    print(f'Copying... {copied_so_far:,} {unit}', end='')
    sleep(.1)

# start backup process
def backup():
    os_ver = checkOS()
    os_ver.get('clear')

    # checking if GDFS is set up properly
    while(gdfs_installed == False or gdfs_running == False or gdfs_signedin == False):
        isProgramInstalled(os_ver.get('name'), os_ver.get('gdfs_app_path'), os_ver.get('gdfs_process_name'), os_ver.get('clear'))
        isProgramRunning(os_ver.get('gdfs_process_name'), os_ver.get('open_gdfs'), os_ver.get('clear'))
        isSignedInToGDFS(os_ver.get('app_cache'), os_ver.get('clear'))

    # checking if GDFS mount path is ready
    while not os.path.exists(os_ver.get('gdfs_drive_path')):
        sleep(2)

    # creates backup directory
    createBackupFolder(os_ver.get('backup_path'))


    user_path = os.path.expanduser('~')
    backup_path = os_ver.get('backup_path')
    selected_directories = os_ver.get('selected_folders')

    # getting the source and destination path for the selected folders
    source_dest = getSourceAndDestination(user_path, backup_path, *selected_directories)

    # if macos, initiate terminal access to user folders (source)
    if os_ver.get('name').lower() == 'macos':
        for each_folder in source_dest:
            accessMacOSFolders(each_folder[1])

    # copies restore command to backup folder
    shutil.copy2(os_ver.get('restore'), os_ver.get('backup_path'))

    # goes through each source and destination in the source_dest list
    for each_folder in source_dest:
        directory = each_folder[0]
        source = each_folder[1]
        dest = each_folder[2]

        print(directory, '==>', dest)

        # starts a separate thread for copying
        copying = threading.Thread(name='copying', target=shutil.copytree, args=(source, dest))
        copying.start()

        while copying.is_alive():
            files_copied_so_far = fileCountInPath(dest)
            progress(files_copied_so_far)
        print(f'\rCopied from {directory}... {fileCountInPath(dest)} files\n\n')

    print(f'''\nTotal of {fileCountInPath(backup_path)} files copied\n
Please give Google Drive File Stream time to fully sync newly copied data to the cloud. To verify data backup, please check folder named {UNDERLINE}{os_ver.get('backup_folder')}{END} in https://drive.work.ea.com
''')



if __name__ == "__main__":
    backup()
