#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-12

import warnings
warnings.filterwarnings("ignore")
import socket
import os
import paramiko
import interactive
import encoder
import sys
import ConfigParser
import scp
import time

DEBUG = False

class whisperer(object):
    def __init__(self, hostname, conf_file, username="root1"):
        self.hostname = hostname
        self.username = username

        if DEBUG:
            print "[%.2f]get conf from file..." % time.time(),
        self.__get_conf__(conf_file)
        if DEBUG:
            print "done"
            sys.stdout.flush()
        if DEBUG:
            print "[%.2f]release root privallege..." % time.time(),
        self.__release_root_privallege__()
        if DEBUG:
            print "done"
            sys.stdout.flush()
        if DEBUG:
            print "[%.2f]get username..." % time.time(),
        self.__get_user__()
        if DEBUG:
            print "done"
            sys.stdout.flush()
        self.__proxyer__("%s|%s@%s" % (self.user,
            self.username, self.hostname))
        if DEBUG:
            print "[%.2f]create ssh session..." % time.time(),
        self.__ssh__()
        if DEBUG:
            print "done"
            sys.stdout.flush()

    def __get_conf__(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.SERVER_HOST = conf_parse.get("whisperer", "SERVER_HOST")
        self.SERVER_PORT = conf_parse.getint("whisperer", "SERVER_PORT")
        self.PUBLIC_KEY_FILE = conf_parse.get("whisperer", "PUBLIC_KEY_FILE")
        self.PRIVATE_KEY_FILE = conf_parse.get("whisperer", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE = conf_parse.get("whisperer", "REMOTE_KEY_FILE")
        self.encode = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)

    def __proxyer__(self, req):
        if DEBUG:
            print "[%.2f]create socket and send msg..." % time.time(),
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.SERVER_HOST, self.SERVER_PORT))
        sock.send(self.encode.encode(req))
        if DEBUG:
            print "done"
            sys.stdout.flush()
        if DEBUG:
            print "[%.2f]recv msg..." % time.time(),
        res = self.encode.decode(sock.recv(1024))
        if DEBUG:
            print "done"
            sys.stdout.flush()
        sock.close()
        if not res.startswith("0.."):
            print >> sys.stdout, "Permission deny."
            sys.exit(2)
        self.psd = res[3:]

    def __get_user__(self):
        self.user = os.getenv("SUDO_USER")

    def __release_root_privallege__(self):
        uid = int(os.getenv("SUDO_UID"))
        gid = int(os.getenv("SUDO_GID"))
        os.setgid(gid)
        os.setuid(uid)

    def __get_window_size(self):
        rows, columns = map(int, os.popen('stty size', 'r').read().split())
        return rows, columns

    def __get_term_type__(self):
        return os.getenv("TERM")

    def __ssh__(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.hostname, port=22,
                username=self.username, password=self.psd, compress=True)
        except Exception, msg:
            print >> sys.stdout, msg
            sys.exit(1)

    def interact(self):
        if DEBUG:
            print "[%.2f]start interact..." % time.time()
        rows, columns = self.__get_window_size()
        channel = self.ssh.invoke_shell(term=self.__get_term_type__(),
            width=columns, height=rows)
        interactive.interactive_shell(channel)        
        channel.close()

    def scp_start(self, mode, src, dest):
        try:
            transport = self.ssh.get_transport()
            s = scp.SCPClient(transport)
            print >> sys.stdout, "processing..."
            if mode == "scp_put":
                s.put(src, dest)
                print >> sys.stdout, "done."
                return True
            elif mode == "scp_get":
                s.get(src, dest)
                print >> sys.stdout, "done."
                return True
            else:
                return False
        except Exception, msg:
            print >> sys.stderr, msg
            return False

    def close(self):
        self.ssh.close()
