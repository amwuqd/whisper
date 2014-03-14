#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-12

import sys
import whisperer

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, "Usage: %s <hostname>" % sys.argv[0]
        sys.exit(1)
    try:
        whisperer.whisperer("%s.sandai.net" % sys.argv[1], "/usr/local/whisper/conf/whisperer.conf")
    except socket.error, msg:
        print >> sys.stderr, msg
