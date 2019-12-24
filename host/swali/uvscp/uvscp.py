import errno
import re
import socket
import sys
from uvscp_event import event
from uvscp_guid import guid
from uvscp_filter import event_filter
import time
import struct

__all__ = ["vscp","error_proto"]

class error_proto(Exception): pass

# Standard port
VSCP_PORT = 8598

# Line terminators
CR = b'\r'
LF = b'\n'
CRLF = CR+LF

# maximal line length when calling readline()
_MAXLINE = 2048

class vscp:
    """This class supports blablabla"""

    encoding = 'UTF-8'

    def __init__(self, host = '127.0.0.1', port=VSCP_PORT,
            timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.sock = self._create_socket(timeout)
        self.file = self.sock.makefile('rb')
        self._debugging = 0
        self.welcome = self._getlongresp()

    def _create_socket(self, timeout):
        return socket.create_connection((self.host, self.port), timeout)

    def _putline(self, line):
        if self._debugging > 1: print('*put*', repr(line))
        self.sock.sendall(line + CRLF)

    def _putcmd(self, line):
        if self._debugging: print('*cmd*', repr(line))
        line = bytes(line, self.encoding)
        self._putline(line)

    def _getline(self):
        line = self.file.readline(_MAXLINE + 1)
        if len(line) > _MAXLINE:
            raise error_proto('line too long')

        if self._debugging > 1: print('*get*', repr(line))
        if not line: raise error_proto('-ERR EOF')
        octets = len(line)
        # server can send any combination of CR & LF
        # however, 'readline()' returns lines ending in LF
        # so only possibilities are ...LF, ...CRLF, CR...LF
        if line[-2:] == CRLF:
            return line[:-2], octets
        if line[:1] == CR:
            return line[1:-1], octets
        return line[:-1], octets


    # Internal: get a response from the server.
    # Raise 'error_proto' if the response doesn't start with '+'.

    def _getresp(self):
        resp, o = self._getline()
        if self._debugging > 1: print('*resp*', repr(resp))
        if not resp.startswith(b'+'):
            raise error_proto(resp)
        return resp

    def _getlongresp(self, neg_resp = False):
        list = []; octets = 0
        line, o = self._getline()
        while not line.startswith(b'+') and not (line.startswith(b'-') and neg_resp):
            list.append(line)
            octets += o
            line, o = self._getline()
        return line, list, octets

    def _shortcmd(self, line):
        self._putcmd(line)
        return self._getresp()

    def _longcmd(self, line, neg_resp = False):
        self._putcmd(line)
        return self._getlongresp(neg_resp)

    #convenience functions
    def getwelcome(self):
        return self.welcome[1]

    def set_debuglevel(self, level):
        self._debugging = level

    #api functions
    def noop(self):
        """Does nothing.
        One supposes the response indicates the server is alive.
        """
        return self._shortcmd('NOOP')

    def send(self, event_l):
        """Send event to the daemon"""
        if not isinstance(event_l, event):
            raise error_proto('event should be of class event')
        return self._shortcmd('SEND ' + repr(event_l))

    def retr(self, num=1):
        """Get events from the buffer"""
        resp = self._longcmd('RETR ' + str(num), neg_resp=True)
        return (resp[0], event.fromstringlist([x.decode() for x in resp[1]]), resp[2])

    def user(self, user):
        return self._shortcmd('USER ' + user)

    def password(self, password):
        return self._shortcmd('PASS ' + password)

    def chkdata(self):
        resp = self._longcmd('CDTA')
        return (resp[0], int(resp[1][0].decode()), resp[2])

    def setfilter(self, filter):
        return self._shortcmd('SFLT ' + filter.filter_str())

    def setmask(self, filter):
        return self._shortcmd('SMSK ' + filter.filter_mask_str())

    def clrall(self):
        return self._shortcmd('CLRA')

    def quit(self):
        """Signoff"""
        resp = self._shortcmd('QUIT')
        self.close()
        return resp

    def close(self):
        """Close the connection without assuming anything about it."""
        try:
            file = self.file
            self.file = None
            if file is not None:
                file.close()
        finally:
            sock = self.sock
            self.sock = None
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError as exc:
                    # The server might already have closed the connection.
                    # On Windows, this may result in WSAEINVAL (error 10022):
                    # An invalid operation was attempted.
                    if (exc.errno != errno.ENOTCONN
                       and getattr(exc, 'winerror', 0) != 10022):
                        raise
                finally:
                    sock.close()



if __name__ == "__main__":
    v = vscp()
    #v.set_debuglevel(1)
    print(v.getwelcome())
    print(v.noop())
    flt = event_filter(0,0,0,0x3ff,0x0A,0xFF)
    v.setmask(flt)
    v.setfilter(flt)
    for i in range(0,2**8):
        v.send(event(vscp_class = 0, vscp_type=0x09, data=struct.pack('BB', 2, i)))
        time.sleep(.01)
        print(f'{i}, {v.retr(5)[1][0].data[1]}')
    v.quit()
