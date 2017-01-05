import argparse
import logging
import os
import pipes
import subprocess
import sys
import urlparse

import gitremotequbes.copier
# pylint: disable=missing-docstring

QREXEC="/usr/lib/qubes/qrexec-client-vm"

logging.basicConfig(format="local:" + logging.BASIC_FORMAT, level=logging.DEBUG
        if os.getenv("QUBES_DEBUG") else logging.INFO,)

l = logging.getLogger()


def get_main_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", metavar="NAME")
    parser.add_argument("url", metavar="URL")
    return parser


def get_rpcarg(url):
    rpcarg = subprocess.check_output(["systemd-escape", "--", url.path])[:-1]
    if len(rpcarg) > 64:
        # Path is too long!  We must do without rpcarg.
        rpcarg = None
    return rpcarg


def get_vm_connection(name, url, upload = False):
    rpcarg = get_rpcarg(url)

    remoteargs = [name, url.path]
    if os.getenv("QUBES_DEBUG"):
        remoteargs = ["-d"] + remoteargs

    quotedargs = " ".join(pipes.quote(x) for x in remoteargs)
    quotedlen = len(quotedargs)
    rpc = 'ruddo.Git.'
    if upload:
        rpc += 'Upload'
    else:
        rpc += 'Receive'

    if rpcarg:
        rpc += "+%s" % rpcarg

    l.debug([QREXEC, url.netloc, rpc])

    vm_connection = subprocess.Popen(
        [QREXEC, url.netloc, rpc],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    vm_connection.stdin.write("%s\n" % quotedlen + quotedargs)
    return vm_connection


def is_upload(cmd):
    sub_cmd = cmd.split()[-1]
    if sub_cmd == 'git-receive-pack':
        return False
    elif sub_cmd == 'git-upload-pack':
        return True
    else:
        l.error('Unsupported command %s', sub_cmd)
        sys.exit(1)

def main():
    args = get_main_parser().parse_args()
    name = args.name
    url = urlparse.urlparse(args.url)
    assert url.scheme == "qubes"

    cmd = sys.stdin.readline()
    assert cmd == "capabilities\n"
    sys.stdout.write("connect\n\n")

    cmd = sys.stdin.readline()
    vm_connection = get_vm_connection(name, url, is_upload(cmd))

    line = vm_connection.stdout.readline()
    if line != "confirmed\n":
        l.debug("the request appears to have been refused or it malfunctioned")
        return 128

    ret = 0
    while ret == 0:
        if not cmd:
            l.debug("no more commands, exiting")
            break
        elif cmd.startswith("connect "):
            l.debug("asked to run %s", cmd)
            vm_connection.stdin.write(cmd)
            reply = vm_connection.stdout.readline()
            assert reply == "\n", "local: wrong reply %r" % reply
            sys.stdout.write(reply)

            ret = gitremotequbes.copier.call(
                vm_connection,
                sys.stdin,
                sys.stdout
            )
            if ret != 0:
                l.debug("remote side exited with %s", ret)
            else:
                l.debug("remote side exited normally")
            break
        elif cmd == "\n":
            l.debug("git sent us an empty line as command")
        else:
            l.error("invalid command %r", cmd)
            ret = 127
        for data in sys.stdin, vm_connection.stdin, sys.stdout, \
                vm_connection.stdout:
            gitremotequbes.copier.b(data)

        cmd = sys.stdin.readline()


    return ret
