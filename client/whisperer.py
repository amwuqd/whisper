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

class whisperer(object):
    def __init__(self, hostname, conf_file, username="root1"):
        self.hostname = hostname
        self.username = username
        self.__get_conf__(conf_file)
        self.__get_user__()
        self.__proxyer__("%s|%s@%s" % (self.user, self.username, self.hostname))
        self.__ssh__()

    def __get_conf__(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.SERVER_HOST        = conf_parse.get("whisperer", "SERVER_HOST")
        self.SERVER_PORT        = conf_parse.getint("whisperer", "SERVER_PORT")
        self.PUBLIC_KEY_FILE    = conf_parse.get("whisperer", "PUBLIC_KEY_FILE")
        self.PRIVATE_KEY_FILE   = conf_parse.get("whisperer", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE    = conf_parse.get("whisperer", "REMOTE_KEY_FILE")
        self.encode             = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)
    def __proxyer__(self, req):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.SERVER_HOST, self.SERVER_PORT))
        sock.send(self.encode.encode(req))
        res = self.encode.decode(sock.recv(1024))
        sock.close()
        if not res.startswith("0.."):
            print >> sys.stdout, "Permission deny."
            sys.exit(2)
        self.psd = res[3:]
    def __get_user__(self):
        self.user = os.getenv("SUDO_USER")
    def __ssh__(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.hostname, port=22, username=self.username, password=self.psd, compress=True)
            channel = ssh.invoke_shell()
            interactive.interactive_shell(channel)
            channel.close()
            ssh.close()
        except Exception, msg:
            print >> sys.stdout, msg
            sys.exit(1)
