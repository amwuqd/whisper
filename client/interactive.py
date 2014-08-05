#!/usr/bin/env python
#--*-- coding: utf-8 --*--
# Liszt 2014-4-4

import socket
import sys
from paramiko.py3compat import u

# windows does not have termios...


class CaseEOF(Exception):
    pass

try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)


def posix_shell(chan):
    import select
    import fcntl
    import os
    
    fd = sys.stdin.fileno()
    chan_fd = chan.fileno()
    oldtty = termios.tcgetattr(sys.stdin)
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    chan_oldflags = fcntl.fcntl(chan_fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    fcntl.fcntl(chan_fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    try:
        tty.setraw(fd)
        tty.setcbreak(fd)
        chan.settimeout(0.0)

        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    while True:
                        x = chan.recv(1024)
                        if len(x) == 0:
                        #sys.stdout.write('\r\n*** EOF\r\n')
                            raise CaseEOF
                        sys.stdout.write(x)
                        sys.stdout.flush()
                except socket.timeout:
                    pass
                except IOError:
                    continue
                except CaseEOF:
                    break
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                try:
                    while True:
                        x += sys.stdin.read(1)
                except IOError:
                    pass
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
        fcntl.fcntl(chan_fd, fcntl.F_SETFL, chan_oldflags)

    
# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")
        
    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()
        
    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()
        
    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass