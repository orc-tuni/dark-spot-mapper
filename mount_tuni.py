#!/usr/bin/python3

"""Script for mounting Tampere University network drives"""

import os
import subprocess

MOUNTPOINT = "/media/lab/tuni"


def mount():
    print("Username: ", end="")
    username = input()

    proc = subprocess.Popen(
        ["sshfs", f"{username}@ssh.intra.tut.fi:/", MOUNTPOINT],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.communicate()


def unmount():
    subprocess.run(["fusermount", "-u", MOUNTPOINT])


def main():
    try:
        contents = os.listdir(MOUNTPOINT)
    except OSError:
        print("The network drive appears to be stuck. Closing connection.")
        unmount()
        return

    if os.listdir(MOUNTPOINT):
        print("Network drive appears to be already mounted. Unmount? (y/n)")
        res = input()
        while res not in ["y", "n"]:
            print("Please input y or n")
            res = input()

        if res == "y":
            unmount()
        else:
            return
    else:
        mount()

    print("Ready. Press enter to exit")
    input()

if __name__ == "__main__":
    main()
