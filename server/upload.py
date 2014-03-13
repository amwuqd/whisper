#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-4

import redis
import sys
import encoder
import config

class uploader(object):
	def __init__(self, password_file, conf_file):
		self.get_conf(conf_file)
		self.run()
    def get_conf(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.REDIS_PORT         = conf_parse.getint("listener", "REDIS_PORT")
        self.REDIS_DB           = conf_parse.getint("listener", "REDIS_DB")
        self.REDIS_AUTH         = conf_parse.get("listener", "REDIS_AUTH")
        self.PRIVATE_KEY_FILE   = conf_parse.get("listener", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE    = conf_parse.get("listener", "REMOTE_KEY_FILE")
        self.encode             = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)
    def run(self):
    	r = self.get_redis()
    	for line in open(self.password_file, 'r'):
    	   	try:
    	   		key, value = line.split()
    	   		r.setex(key, self.encode.encode(value))
    	   	except:
    	   		print >> sys.stderr, key, value, "upload fail."
    def get_redis(self):
    	return redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB, password=self.REDIS_AUTH)

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print >> sys.stderr, "Usage: %s <file_path>" % sys.argv[0]
    uploader(sys.argv[1], CONF_FILE)