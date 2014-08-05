#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-4

import redis
import sys
import encoder
import ConfigParser
import config

class uploader(object):
    def __init__(self, conf_file, host):
        self.host = host
        self.get_conf(conf_file)
        self.get_pass()
        self.run()
    def get_conf(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.password_file      = conf_parse.get("upload", "PW_PATH")
        self.REDIS_HOST         = conf_parse.get("listener", "REDIS_HOST")
        self.REDIS_PORT         = conf_parse.getint("listener", "REDIS_PORT")
        self.REDIS_DB           = conf_parse.getint("listener", "REDIS_DB")
        self.REDIS_AUTH         = conf_parse.get("listener", "REDIS_AUTH")
        self.PRIVATE_KEY_FILE   = conf_parse.get("listener", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE    = conf_parse.get("listener", "REMOTE_KEY_FILE")
        self.encode             = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)
        server_define           = conf_parse.get("upload", "SERVER_DEFINE")
        self.max_expire = {}
        for s in server_define.split(','):
            s = s.strip()
            expire = conf_parse.get("upload", "%s_max_expire" % s)
            path = conf_parse.get("upload", "%s_PATH" % s)
            servers = set()
            try:
                for h in open(path, 'r'):
                    host = h.strip()
                    if host.startswith('#') or host == '':
                        continue
                    servers.add(host)
            except Exception, e:
                print >> sys.stderr, e
                sys.exit(1)
            self.max_expire[s] = {"max_expire": expire, "hosts": servers}
    def get_pass(self):
        self.passwd = {}
        for line in open(self.password_file, 'r'):
            try:
                remote_user, hostname, password = line.split()
            except:
                pass
            if remote_user not in self.passwd:
                self.passwd[remote_user] = {hostname: password}
            else:
                self.passwd[remote_user][hostname] = password
    def run(self):
        r = self.get_redis()
        for username, remote_user, hostname, expire in self.host:
            for k, v in self.max_expire.items():
                if hostname in v["hosts"]:
                    expire = v["max_expire"]
            key = "%s|%s@%s.sandai.net" % (username, remote_user, hostname)
            try:
                value = self.encode.encode("0..%s" % self.passwd[remote_user][hostname])
            except KeyError:
                print >> sys.stderr, "%s[Failed]%s  %s password not exist" % (bcolors.FAIL, bcolors.ENDC, key)
                continue
            try:
                expire = self.timedelta(expire)
            except ExpireError, e:
                print >> sys.stderr, "%s[Failed]%s  %s %s" % (bcolors.FAIL, bcolors.ENDC, key, e)
                continue
            
            r.setex(key, value, expire)
            print >> sys.stdout, "%s[Success]%s %s [%d seconds]" % (bcolors.OKGREEN, bcolors.ENDC, key, expire)
       
    def get_redis(self):
        return redis.Redis(host=self.REDIS_HOST,
                           port=self.REDIS_PORT,
                           db=self.REDIS_DB, 
                           password=self.REDIS_AUTH)

    def timedelta(self, time):
        sec = { 'm': 60,
                'h': 3600,
                'd': 86400,
                'M': 2592000
                }

        if time.isdigit():
            expire = int(time)
        else:
            time_d = time[:-1]
            time_t = time[-1]
            if time_d.isdigit() and time_t in sec:
                expire = int(time_d) * sec[time_t]
            else:
                raise ExpireError("expire is not digit")
        if expire == 0:
            raise ExpireError("zero expire")
        return expire


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

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class ExpireError(Exception):
    pass

if __name__ == '__main__':
    if len(sys.argv) == 1:
        res = set()
        for lines in sys.stdin:
            for line in lines.split():
                try:
                    username, hostname, expire = line.strip().split(',')
                except Exception, e:
                    print >> sys.stderr, "Failed in parse line '%s'" % line
                    continue
                remote_user, hostname = split_opt(hostname, '@', "xl_dev")
                res.add((username, remote_user, hostname, expire))
        uploader(conf_file=config.CONF_FILE, host=res)
    
                
    else:
        print >> sys.stderr, "Usage: %s <username> <expire> [<remote_user>@]<hostname>" % sys.argv[0]
        sys.exit(1)
