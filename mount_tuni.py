#!/usr/bin/python3

"""Script for mounting Tampere University network drives"""

import os
import subprocess

MOUNTPOINT = "/media/lab/tuni"


def yesno() -> bool:
    res = input()
    while res not in ["y", "n"]:
        print("Please input y or n")
        res = input()

    if res == "y":
        return True
    elif res == "n":
        return False
    else:
        raise RuntimeError()


def mount():
    print("Please input credentials for mounting the network drive")
    print("Username: ", end="")
    username = input()

    proc = subprocess.Popen(
        ["sshfs", f"{username}@ssh.intra.tut.fi:/", MOUNTPOINT],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.communicate()
    print("The network drive should now be mounted")


def unmount():
    print("Unmounting")
    subprocess.run(["fusermount", "-u", MOUNTPOINT])
    print("Unmounted")


def main():
    try:
        contents = os.listdir(MOUNTPOINT)
    except OSError:
        print("The network drive appears to be stuck. Closing connection.")
        unmount()
        return

    if contents:
        print("Network drive appears to be already mounted. Unmount? (y/n)")
        res = yesno()
        if res:
            unmount()
        return

    mount()
    res = ""
    while res != "u":
        print("Enter u to unmount the drive")
        res = input()
    unmount()

    print("Ready. Press enter to exit")
    input()


if __name__ == "__main__":
    main()
