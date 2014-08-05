#!/usr/bin/python27/bin/python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-4

import rsa
import os
import stat
from Crypto.Cipher import AES
from Crypto import Random
import base64


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
        with open(pubfile) as publicfile:
            p = publicfile.read()
            pubkey = rsa.PublicKey.load_pkcs1(p)
        return pubkey
    def __get_private_key_in_file__(self, prifile):
        with open(prifile) as privatefile:
            p = privatefile.read()
            prikey = rsa.PrivateKey.load_pkcs1(p)
        return prikey

class AES_encoder(object):
    def __init__(self, key=None):
        self.bs = 32
        if key is None:
            key = Random.new().read(self.bs)
        if len(key) >= 32:
            self.key = key[:32]
        else:
            self.key = self._pad(key)

    def encode(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decode(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]
