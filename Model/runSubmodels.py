import sys
import subprocess

cmd_file = open("runSubmodels.txt","r")
Lines = cmd_file.readlines()

for line in Lines:
    print(line)
    subprocess.run(line,shell=True,executable="/bin/bash")

cmd_file.close()
