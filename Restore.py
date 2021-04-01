from os.path import expanduser, split
import subprocess
import sys

# Restore backup data from Google Drive
# Get the absolute path of a shell script

script_path = sys.argv[0]
script_dir = split(script_path)[0]
home = expanduser("~")

# Restore backup data to the user's profile
subprocess.Popen(['cp', '-R', '-v', f'{script_dir}/Desktop', f'{home}'])
subprocess.Popen(['cp', '-R', '-v', f'{script_dir}/Documents', f'{home}'])
subprocess.Popen(['cp', '-R', '-v', f'{script_dir}/Pictures', f'{home}'])
