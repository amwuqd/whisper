#!/usr/local/python27/bin/python
#--*-- coding: utf-8 --*--
# Liszt 2014-4-11

import sys
import whisperer

'''
def get_conf():
    import optparse

    usage = "Usage: %prog <hostname> [remote_username]"
    parser = optparse.OptionParser(usage)
    parser.add_option("-H", "--hostname", help="host to connect")
    parser.add_option("-u", "--user",
                      default="root1",
                      help="username of remote host")
    parser.add_option("-m", "--mode",
                      type="choice",
                      choices=["ssh", "scp"],
                      default="ssh",
                       help="ssh mode (ssh, scp, sftp etc...)")
    parser.add_option("-s", "--src", 
                      default=None,
                      help="scp source file path")
    parser.add_option("-d", "--dest",
                      default=None,
                      help="scp dest file path")
    options, args = parser.parse_args()

    if options.hostname is None:
        parser.print_help()
        sys.exit(3)
    try:
        host, path = options.src.split(':')
        mode = "scp_get"
    except Exception, e:
        pass
    try:
        host, path = options.dest.split(':')
        mode = "scp_put"
    except Exception, e:
        pass

    if mode is None:
        print >> stderr, "You must specify which host for transport."
        sys.exit(1)

    return (
            mode, options.user,
            options.hostname, options.src,
            options.dest
            )
            '''


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
        print >> sys.stderr, "Usage: %s [[username]@]<hostname>"
        sys.exit(42)
    if len(sys.argv) < 2:
        usage()
    mode = sys.argv[1]
    if mode == "ssh":
        if len(sys.argv) == 3:
            host = sys.argv[2]
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
            host, dest = split_opt(dest, ':')
            if host is None:
                usage()
            user, host = split_opt(host, '@', "root1")
        return mode, user, host, src, dest
    usage()

if __name__ == '__main__':

    mode, user, host, src, dest = get_conf()

    
    try:
        w = whisperer.whisperer(hostname="%s.sandai.net" % host,
                                conf_file="/usr/local/whisper/etc/whisperer.conf",
                                username=user)
        if mode == "ssh":
            w.interact()
        elif mode == "scp_get" or mode == "scp_put":
            w.scp_start(mode, src, dest)
    except KeyboardInterrupt:
        print >> sys.stderr, "User Interrput."
    except Exception, msg:
        print >> sys.stderr, msg
    finally:
        w.close()
