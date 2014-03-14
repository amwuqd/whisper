#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-12

import sys
import socket
import whisperer

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, "Usage: %s <hostname>" % sys.argv[0]
        sys.exit(1)
    try:
        whisperer.whisperer("%s.sandai.net" % sys.argv[1], "/usr/local/whisper/etc/whisperer.conf")
    except socket.error, msg:
        print >> sys.stderr, msg
    except KeyboardInterrupt:
        print >> sys.stderr, "User Interrput."
