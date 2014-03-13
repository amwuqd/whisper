#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-12

import ConfigParser
import redis
import encoder
import socket
import logging

class PermissionDeny(Exception):
    pass

class listener(object):
    def __init__(self, conf_file):
        self.get_conf(conf_file)
        self.init_log()
        self.run()
    def get_conf(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.BIND_IP            = conf_parse.get("listener", "BIND_IP")
        self.BIND_PORT          = conf_parse.getint("listener", "BIND_PORT")
        self.REDIS_HOST         = conf_parse.get("listener", "REDIS_HOST")
        self.REDIS_PORT         = conf_parse.getint("listener", "REDIS_PORT")
        self.REDIS_DB           = conf_parse.getint("listener", "REDIS_DB")
        self.REDIS_AUTH         = conf_parse.get("listener", "REDIS_AUTH")
        self.PUBLIC_KEY_FILE    = conf_parse.get("listener", "PUBLIC_KEY_FILE")
        self.PRIVATE_KEY_FILE   = conf_parse.get("listener", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE    = conf_parse.get("listener", "REMOTE_KEY_FILE")
        self.LOG_LEVEL          = conf_parse.get("listener", "LOG_LEVEL")
        self.encode             = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)
    def init_log(self):
        self.logger = logging.getLogger("auth-ctrl")
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler("access.log")
        fh.setLevel(logging.DEBUG)
        #ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        #ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        #logger.addHandler(ch)
    def get_redis(self):
        return redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB, password=self.REDIS_AUTH)
    def run(self):
        try:
            r = self.get_redis()
        except:
            self.logger.error("Redis connect error.")
        self.logger.info("Redis connected.")
        try:
            listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_fd.bind((self.BIND_IP, self.BIND_PORT))
            listen_fd.listen(1024)
        except socket.error, msg:
            self.logger.error(msg)
        self.logger.info("Socket listened.")
        self.logger.info("Initial finished.")
        while True:
            conn, addr = listen_fd.accept()
            try:
                conn.settimeout(5)
                buf = self.encode.decode(conn.recv(1024))
                res = self.handler(buf, r)
                conn.send(self.encode.encode(res))
                self.logger.info("%s %s" % (addr, buf))
                self.logger.debug("%s %s %s" % (addr, buf, res))
            except socket.error, msg:
                self.logger.error(msg)
            except redis.WatchError, msg:
                self.logger.error(msg)
                r = self.get_redis()
            except PermissionDeny:
                self.logger.error("%s %s PD" % (addr, buf))
                conn.send(self.encode.encode("1..deny"))
            conn.close()
        listen_fd.close()
    def handler(self, message, r):
        res = r.get(message)
        if res is None:
            raise PermissionDeny
        else:
            return "0..%s" % res