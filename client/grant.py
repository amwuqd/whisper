#!/usr/local/python27/bin/python
#--*-- coding: utf-8 --*--
# Liszt 2014-5-15

# Liszt 2014-6-10
# 修改默认授权用户为xl_dev

import warnings
warnings.filterwarnings("ignore")
import socket
import ConfigParser
import encoder
import sys
import os
import time

DEBUG = False

class grant_agent(object):
    def __init__(self, conf_file, data):
        if DEBUG:
            print "[%.2f]get conf from file..." % time.time(),
        self.__get_conf__(conf_file)
        if DEBUG:
            print "done"
        if DEBUG:
            print "[%.2f]get user from env..." % time.time(),
        self.user = self.__get_user__()
        if DEBUG:
            print "done"
        if DEBUG:
            print "[%.2f]release privallege..." % time.time(),
        self.__release_root_privallege__()
        if DEBUG:
            print "done"
        if DEBUG:
            print "[%.2f]parse data..." % time.time(),
        self.req = self.__parse__(data)
        if DEBUG:
            print "done"
        if DEBUG:
            print "[%.2f]proxy..." % time.time(),
        self.__proxy__("%s\r\n" % self.user)
        if DEBUG:
            print "done"

    def __proxy__(self, header):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.SERVER_HOST, self.SERVER_PORT))
        sock.send(self.encode.encode(header))
        res = self.encode.decode(sock.recv(1024))
        key = res
        if DEBUG:
            print "AES Key is: %s" % key
        self.aes_encode = encoder.AES_encoder(key)
        if DEBUG:
            print "Request is: %s ..." % self.req,
        sock.send("%s\r\n" % self.aes_encode.encode(self.req))
        if DEBUG:
            print "sent."
        res = ''
        if DEBUG:
            print "[%.2f]proxy..." % time.time(),
        while True:
            buf = sock.recv(1024)
            res += buf
            if DEBUG:
                print buf,
            if buf[-2:] == '\r\n' or len(buf) == 0:
                break
        if DEBUG:
            print "done"
        res = self.aes_encode.decode(res)
        print >> sys.stdout, res

    def __parse__(self, data):
        return data

    def __get_user__(self):
        #return = 'lirui'
        return os.getenv("SUDO_USER")

    def __release_root_privallege__(self):
        uid = int(os.getenv("SUDO_UID"))
        gid = int(os.getenv("SUDO_GID"))
        os.setgid(gid)
        os.setuid(uid)

    def __get_conf__(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.SERVER_HOST = conf_parse.get("uploader", "SERVER_HOST")
        self.SERVER_PORT = conf_parse.getint("uploader", "SERVER_PORT")
        self.PUBLIC_KEY_FILE = conf_parse.get("whisperer", "PUBLIC_KEY_FILE")
        self.PRIVATE_KEY_FILE = conf_parse.get("whisperer", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE = conf_parse.get("whisperer", "REMOTE_KEY_FILE")
        self.encode = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)

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

class MsgTooLong(Exception):
    pass


if __name__ == '__main__':
    try:
        cnt = 0
        res = ''
        for lines in sys.stdin:
            for line in lines.split():
                try:
                    username, hostname, expire = line.strip().split(',')
                except Exception, e:
                    print >> sys.stderr, "Failed in parse line '%s'" % line
                    continue
                remote_user, hostname = split_opt(hostname, '@', "xl_dev")
                res += "%s,%s,%s,%s " % (username, remote_user, hostname, expire)
                cnt += 1
                if cnt > 1000:
                    print >> sys.stderr, "you grant too many servers"
                    raise MsgTooLong("Message too long")
        if res != '':
            grant_agent(conf_file="/usr/local/whisper/etc/whisperer.conf", data=res)
    except Exception, e:
        print >> sys.stderr, e
        sys.exit(1)
