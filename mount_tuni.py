#!/usr/bin/python3

"""Script for mounting Tampere University network drives

SFTP access to Tampere University network drives was shut down on 2020-02-20,
so this script no longer works.
"""

import os
# Usage of the subprocess module is necessary
import subprocess   # nosec

MOUNTPOINT = "/media/lab/tuni"


def yesno() -> bool:
    res = input()  # nosec
    while res not in ["y", "n"]:
        print("Please input y or n")
        res = input()  # nosec

    if res == "y":
        return True
    elif res == "n":
        return False
    else:
        raise RuntimeError()


def mount():
    print("Please input credentials for mounting the network drive")
    print("Username: ", end="")
    username = input()  # nosec

    proc = subprocess.Popen(  # nosec
        # Passing of user-given parameters is ok, as their usage is explicit
        ["sshfs", f"{username}@ssh.intra.tut.fi:/", MOUNTPOINT],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.communicate()
    print("The network drive should now be mounted")


def unmount():
    print("Unmounting")
    subprocess.run(["fusermount", "-u", MOUNTPOINT])  # nosec
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
        res = input()  # nosec
    unmount()

    print("Ready. Press enter to exit")
    input()  # nosec


if __name__ == "__main__":
    main()
