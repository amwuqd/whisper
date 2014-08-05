#!/usr/local/python27/bin/python
#--*-- coding: utf-8 --*--
# Liszt 2014-4-11

# Liszt 2014-6-10
# 将默认登陆用户修改为twin14：xl_dev，其他：root1

import sys
import whisperer
import time

DEBUG = whisperer.DEBUG

def get_conf():
    def split_opt(arg, d, default=None):
        a = b = None
        try:
            a, b = arg.split(d)
        except Exception, e:
            pass
        if a is None:
            return default, arg
        else:
            return a, b
    def usage():
        print >> sys.stdout, "Usage:   rssh [username@]<hostname>"
        print >> sys.stdout, "         rscp [username@]<hostname>:<filepath> <filepath>"
        print >> sys.stdout, "         rscp <filepath> [username@]<hostname>:<filepath>"
        print >> sys.stdout, "example: rscp root1@twin14001:/path/to/something /path/"
        sys.exit(42)
    if len(sys.argv) < 2:
        usage()
    mode = sys.argv[1]
    if mode == "ssh_debug":
        mode = "ssh"
        DEBUG = whisperer.DEBUG = True
    if mode == "ssh":
        if len(sys.argv) == 3:
            host = sys.argv[2]
            if host.startswith("twin14"):
                user = "xl_dev"
            else:
                user, host = split_opt(host, '@', "root1")
            return mode, user, host, None, None
        elif len(sys.argv) == 4:
            host = sys.argv[2]
            user = sys.argv[3]
            print >> sys.stderr, "Please use this command: rssh %s@%s" % (user, host)
            sys.exit(1)
    elif mode == "scp":
        if len(sys.argv) == 4:
            src = sys.argv[2]
            dest = sys.argv[3]
            host, src = split_opt(src, ':')
            mode = "scp_get"
            if host is None:
                host, dest = split_opt(dest, ':')
                mode = "scp_put"
                if host is None:
                    usage()
            if host.startswith("twin14"):
                user = "xl_dev"
            else:
                user, host = split_opt(host, '@', "root1")
            return mode, user, host, src, dest
    usage()

if __name__ == '__main__':
    if DEBUG:
        print "[%.2f]reading argument..." % time.time(),
    mode, user, host, src, dest = get_conf()
    if DEBUG:
        print "done."

    try:
        w = whisperer.whisperer(hostname="%s.sandai.net" % host,
                                conf_file="/usr/local/whisper/etc/whisperer.conf",
                                username=user)
        if mode == "ssh":
            w.interact()
        elif mode == "scp_get" or mode == "scp_put":
            w.scp_start(mode, src, dest)
        w.close()
    except KeyboardInterrupt:
        print >> sys.stderr, "User Interrput."
    except Exception, msg:
        print >> sys.stderr, msg
        

