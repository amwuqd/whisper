#!/usr/local/python/bin/python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-12

import whisperer
import sys

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print >> sys.stderr, "Usage: %s <hostname>" % sys.argv[0]
		sys.exit(1)
    whisperer.whisperer("%s.sandai.net" % sys.argv[1], "/usr/local/whisper/conf/whisperer.conf")