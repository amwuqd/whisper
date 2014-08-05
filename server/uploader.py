#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-5-15

import select
import redis
import sys
import encoder
import ConfigParser
import config
import logging
import socket

class uploader(object):
    def __init__(self, conf_file):
        self.get_conf(conf_file)
        self.get_pass()
        self.get_group(self.group_file, self.dev_file)
        self.print_pri(self.ser_dev)
        self.init_log()
        self.run()
    def print_pri(self, ser_dev):
        for host in ser_dev:
            if host.startswith("xl_dev"):
                print host, ser_dev[host]
    def get_conf(self, conf_file):
        conf_parse = ConfigParser.ConfigParser()
        conf_parse.read(conf_file)
        self.BIND_IP            = conf_parse.get("upload", "BIND_IP")
        self.BIND_PORT          = conf_parse.getint("upload", "BIND_PORT")
        self.password_file      = conf_parse.get("upload", "PW_PATH")
        self.group_file         = conf_parse.get("upload", "SERVER_GROUP_PATH")
        self.dev_file           = conf_parse.get("upload", "DEV_GROUP_PATH")
        self.REDIS_HOST         = conf_parse.get("listener", "REDIS_HOST")
        self.REDIS_PORT         = conf_parse.getint("listener", "REDIS_PORT")
        self.REDIS_DB           = conf_parse.getint("listener", "REDIS_DB")
        self.REDIS_AUTH         = conf_parse.get("listener", "REDIS_AUTH")
        self.PRIVATE_KEY_FILE   = conf_parse.get("listener", "PRIVATE_KEY_FILE")
        self.REMOTE_KEY_FILE    = conf_parse.get("listener", "REMOTE_KEY_FILE")
        self.encode             = encoder.encoder(self.PRIVATE_KEY_FILE, self.REMOTE_KEY_FILE)
        server_define           = conf_parse.get("upload", "SERVER_DEFINE")
        ROOT                    = conf_parse.get("upload", "ROOT")
        self.ext_expire         = self.timedelta(conf_parse.get("upload", "MAX_EXPIRE"))
        self.group_file = [ x.strip() for x in self.group_file.split(',')]
        self.max_expire = {}
        self.root = set()
        for u in ROOT.split(','):
            self.root.add(u.strip())
        print "############ Root ############"
        print self.root
        print "############ Root ############"
        for s in server_define.split(','):
            s = s.strip()
            print "load server_define" + s
            expire = conf_parse.get("upload", "%s_max_expire" % s)
            path = conf_parse.get("upload", "%s_PATH" % s)
            servers = set()
            try:
                for h in open(path, 'r'):
                    host = h.split('#')[0].strip()
                    if host == '':
                        continue
                    servers.add(host)
            except Exception, e:
                print >> sys.stderr, e
                sys.exit(1)
            self.max_expire[s] = {"max_expire": expire, "hosts": servers}
    def get_pass(self):
        print "get passwd file..."
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
        print "get passwd file done."

    def get_group(self, sg_paths, dev_path):
        import json

        sg_info = {}
        self.ser_dev = {}

        print "get_group step 1."
        try:
            for sg_path in sg_paths:
                print "load file[%s]" % sg_path
                contents = open(sg_path, 'r').read()
                if len(contents) == 0: continue
                sg_info.update(json.loads(contents))
        except KeyError, msg:
            print >> sys.stderr, msg
            sys.exit(1)

        print "get_group step 2."
        try:
            dev_info = json.loads(open(dev_path, 'r').read())
        except ValueError, msg:
            print >> sys.stderr, msg
            sys.exit(2)

        print "get_group step 3."
        for host, groups in sg_info.items():
            dev = set()
            root = set()
            for group in groups:
                #if group == "root":
                #    root.add(set(dev_info[group]))
                #    continue
                if group not in dev_info: continue
                dev = dev.union(set(dev_info[group]))
            if len(dev) == 0: continue
            if host.startswith("twin14"):
                remote_user = "xl_dev"
            else:
                remote_user = "root1"
            self.ser_dev["%s@%s" % (remote_user, host)] = dev
        #print self.ser_dev

    def handle(self, data):
        r = self.get_redis()
        res = ''
        grant_user = data['username']
        for t in data['data'].split():
            username, remote_user, hostname, expire = t.strip().split(',')
            # data check
            if username == '': username = grant_user
            if expire == '': expire = "1h"
            key = "%s|%s@%s.sandai.net" % (username, remote_user, hostname)
            if hostname == '':
                res += "%s[Failed]%s  %s hostname must be specified\n" % (bcolors.FAIL, bcolors.ENDC, key)
                continue


            # permission check
            try:
                if grant_user not in self.root:
                    if grant_user not in self.ser_dev["%s@%s" (remote_user, hostname)]:
                        raise KeyError, "grant_user no permission"
            except KeyError:
                res += "%s[Failed]%s  %s grant_user has no permission\n" % (bcolors.FAIL, bcolors.ENDC, key)
                continue

            for k, v in self.max_expire.items():
                if hostname in v["hosts"]:
                    expire = v["max_expire"]
            try:
                value = self.encode.encode("0..%s" % self.passwd[remote_user][hostname])
            except KeyError:
                res += "%s[Failed]%s  %s authority not exist\n" % (bcolors.FAIL, bcolors.ENDC, key)
                continue
            try:
                expire = self.timedelta(expire)
                if expire > self.ext_expire: expire = self.ext_expire
            except ExpireError, e:
                res += "%s[Failed]%s  %s %s\n" % (bcolors.FAIL, bcolors.ENDC, key, e)
                continue
            
            r.setex(key, value, expire)
            res += "%s[Success]%s %s [%d seconds]\n" % (bcolors.OKGREEN, bcolors.ENDC, key, expire)
        return res
       
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

    def init_log(self):
        self.logger = logging.getLogger("whisper")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler("grant.log")
        fh.setLevel(logging.INFO)
        #ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        #ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        #logger.addHandler(ch)

    def run(self):
        try:
            listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_fd.bind((self.BIND_IP, self.BIND_PORT))
            listen_fd.listen(1024)
        except socket.error, msg:
            self.logger.error(msg)
        self.logger.info("Socket listened.")
        self.logger.info("Initial finished.")
        inputs = [listen_fd]
        queues = {}
        while True:
            r, w, e = select.select(inputs, [], [])
            for c in r:
                if c is listen_fd:
                    conn, addr = c.accept()
                    inputs.append(conn)
                    queues[conn] = {'handshaked': False, 'data': ''}
                else:
                    try:
                        c.settimeout(5)
                        buf = c.recv(1024)
                        if buf:
                            try:
                                if not queues[c]['handshaked']: buf = self.encode.decode(buf)
                            except Exception, e:
                                grant_user = queues[c]['username'] if queues[c]['handshaked'] else 'unhandshaked'
                                self.logger.error("%s [%s] decrypt fail" % (c.getpeername(), grant_user))
                                inputs.remove(c)
                                del queues[c]
                                c.close()
                                continue
                            queues[c]['data'] += buf
                            if buf[-2:] == '\r\n':
                                if not queues[c]['handshaked']:
                                    queues[c]['username'] = queues[c]['data'][:-2]
                                    key = self.__new_aes_key__()
                                    c.send(self.encode.encode(key))
                                    queues[c]['data'] = ''
                                    queues[c]['handshaked'] = True
                                else:
                                    queues[c]['data'] = self.aes_encode.decode(queues[c]['data'][:-2])
                                    data = self.parse_request(queues[c])
                                    res = self.handle(data)
                                    print data
                                    c.send(self.aes_encode.encode("%s\r\n" % res))
                                    self.logger.info("%s [%s] handle result:\n%s" % (c.getpeername(), data['username'], res))
                                    inputs.remove(c)
                                    del queues[c]
                                    c.close()
                        else:
                            conn.close()
                    except socket.error, msg:
                        self.logger.error(msg)
                    except ParseError, msg:
                        self.logger.error("Parse Error")
                    #except Exception, msg:
                    #    self.logger.error("unexpected exception")
                #print queues
        listen_fd.close()

    def __new_aes_key__(self):
        self.aes_encode = encoder.AES_encoder()
        return self.aes_encode.key

    def parse_request(self, data):
        return data

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
class ParseError(Exception):
    pass
class PermissionDeny(Exception):
    pass

if __name__ == '__main__':
    while True:
        try:
            u = uploader("/usr/local/whisper/etc/listener.conf")
        except Exception, e:
            print >> sys.stderr, e
            break
            #continue
    
