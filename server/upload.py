#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-4

import redis
import sys

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB   = 0
REDIS_AUTH = "foobared"


def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_AUTH)

def main(filename):
    r = get_redis()
    for line in open(filename, 'r'):
        try:
            key, value = line.split()
        except:
            pass
        r.setex(key, value, 3600)

if __name__ == '__main__':
    main(sys.argv[1])