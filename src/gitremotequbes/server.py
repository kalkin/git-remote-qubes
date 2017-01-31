import logging
import time
import os
import shlex
import subprocess
import sys

import gitremotequbes.copier


def main():
    upload = len(sys.argv) > 1 and sys.argv[1] == "upload"
    quotedlen = sys.stdin.readline()
    quotedlen = int(quotedlen, 10)
    if quotedlen > 65535 or quotedlen < 1:
        assert 0, "invalid len"
    args = sys.stdin.read(quotedlen)
    if len(args) != quotedlen:
        assert 0, "invalid argument list"
    try:
        args = shlex.split(args)
    except Exception, e:
        assert 0, "invalid argument list: %s" % e
    if args[0] == "-d":
        args = args[1:]
        level = logging.DEBUG
    else:
        level = logging.INFO
    git_dir = args[1]

    logging.basicConfig(format="remote:" + logging.BASIC_FORMAT, level=level)
    l = logging.getLogger()

    if git_dir.startswith('/cache/'):
        url = git_dir.split('/cache/', 1)[1]
        l.debug("Caching %s", url)
        git_dir = get_from_cache(url, l)

    sys.stdout.write("confirmed\n")

    while True:
        for f in sys.stdin, sys.stdout:
            gitremotequbes.copier.b(f)
        cmd = sys.stdin.readline()

        if not cmd:
            l.debug("no more commands, exiting")
            break
        if cmd.startswith("connect "):
            cmd = cmd[8:-1]
            err_msg = "remote: bad command %r" % cmd
            if upload:
                assert cmd == "git-upload-pack", err_msg
            else:
                assert cmd == "git-receive-pack", err_msg

            sys.stdout.write("\n")
            # And here we go.  We no longer are in control.  Child is.
            os.execvp("git", ["git", cmd[4:], git_dir])
        else:
            assert 0, "invalid command %r" % cmd


def get_from_cache(src, l):
    cache_dir = "/git/_cache/"
    dst = cache_dir + src.split("://", 1)[1]

    if os.path.exists("%s/config" % dst):
        try:
            cmd = ["stat", "-c", "%Y", "FETCH_HEAD"]
            last_fetch = int(subprocess.check_output(cmd, cwd=dst))
        except:
            last_fetch = 0

        now = int(time.time())

        if last_fetch + (15 * 60 * 60) - now < 0:
            update_repo(dst, l)
    else:
        l.info("Creating cache")
        basedir = os.path.dirname(dst)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        cmd = ["git", "clone", "--mirror", src, dst]
        subprocess.Popen(cmd, cwd=cache_dir).communicate()
    return dst


def update_repo(dst, l):
    l.info("Updating cache")
    cmd = ["git", "fetch"]
    subprocess.Popen(cmd, cwd=dst).communicate()
