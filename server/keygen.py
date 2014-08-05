#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-3-6


import sys
import encoder

PUBLIC_KEY_FILE = '/usr/local/whisper/etc/public.pem'
PRIVATE_KEY_FILE = '/usr/local/whisper/etc/private.pem'

encoder.create_rsa_file(PUBLIC_KEY_FILE, PRIVATE_KEY_FILE)

PUBLIC_KEY_FILE = '/usr/local/whisper/etc/spublic.pem'
PRIVATE_KEY_FILE = '/usr/local/whisper/etc/sprivate.pem'

encoder.create_rsa_file(PUBLIC_KEY_FILE, PRIVATE_KEY_FILE)