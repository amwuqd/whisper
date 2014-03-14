#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-4

import rsa
import os
import stat

def create_rsa_file(pubfile, prifile):
    pubkey, prikey = rsa.newkeys(1024)

    pub = pubkey.save_pkcs1()
    publicfile = open(pubfile, 'w+')
    publicfile.write(pub)
    publicfile.close()

    pri = prikey.save_pkcs1()
    privatefile = open(prifile, 'w+')
    privatefile.write(pri)
    privatefile.close()

    os.chmod(pubfile, stat.S_IREAD)
    os.chmod(prifile, stat.S_IREAD)

    return pubkey, prikey

class encoder(object):
    def __init__(self, PRIVATE_KEY_FILE, REMOTE_KEY_FILE):
        self.PRIVATE_KEY = self.__get_private_key_in_file__(PRIVATE_KEY_FILE)
        self.REMOTE_KEY  = self.__get_public_key_in_file__(REMOTE_KEY_FILE)
    def encode(self, MESSAGE):
        return rsa.encrypt(MESSAGE, self.REMOTE_KEY)
    def decode(self, MESSAGE):
        return rsa.decrypt(MESSAGE, self.PRIVATE_KEY)
    def __get_public_key_in_file__(self, pubfile):
        publicfile = open(pubfile)
        p = publicfile.read()
        pubkey = rsa.PublicKey.load_pkcs1(p)
        publicfile.close()
        return pubkey
    def __get_private_key_in_file__(self, prifile):
        privatefile = open(prifile, 'r')
        p = privatefile.read()
        prikey = rsa.PrivateKey.load_pkcs1(p)
        privatefile.close()
        return prikey