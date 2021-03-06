#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyBDM - Library for the Motorola/Freescale Background Debugging Mode.

   (C) 2010-2016 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

   All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import serialport
from bdm import BDMBase

# Elektonikladen Commands.
RESET           = 0x80 # Reset
WRITE_AREA      = 0x82 # FILL_AREA ADDR_HI ADDR_LO CNT DATA
READ_AREA       = 0x83 # READ_AREA ADDR_HI ADDR_LO CNT (0==0xff)
VERSION         = 0xFF


class NoResponseError(Exception): pass
class InvalidResponseError(Exception): pass

def com(v):
    return 0xff & ~v

class ComPod12(BDMBase, serialport.Port):

    MAX_WRITE_PAYLOAD = 0xff
    MAX_READ_PAYLOAD = 16 # 0xff
    DEVICE_NAME = "Elektronik-Laden ComPOD12"
    VARIABLE_BUS_FREQUENCY = False

    def writeCommand(self, cmd):
        self.write(cmd)
        data = self.read(1)
        self.port.flush() # ?
        if data == bytearray():
            raise NoResponseError
        if data[0] != com(cmd):
            raise InvalidResponseError
        if len(data) > 1:
            return data[1:]
        else:
            return None

    def readCommand(self, cmd, responseLen, addr = None):
        self.write(cmd)
        if addr:
            self.write((addr >> 8) & 0xff)
            self.write(addr & 0xff)
        data = self.read(responseLen)
        self.port.flush() # ?
        if data == bytearray():
            raise NoResponseError
        if len(data) != responseLen:
            raise InvalidResponseError
        return data

    def readWord(self, cmd, addr = None):
        data = self.readCommand(cmd, 2, addr)
        self.port.flush() # ?
        if data == bytearray():
            raise NoResponseError
        if len(data) != 2:
            raise InvalidResponseError
        return data[0] << 8 | data[1]

    def writeWord(self, cmd, data0, data1 = None):
        self.write(cmd)
        self.write((data0 >> 8) & 0xff)
        self.write(data0 & 0xff)
        if data1:
            self.write((data1 >> 8) & 0xff)
            self.write(data1 & 0xff)
        d = self.read(1)
        self.port.flush() # ?
        if d == bytearray():
            raise NoResponseError
        if (d[0] != com(cmd)):
            raise InvalidResponseError

    def writeByte(self, cmd, addr, data):
        self.write(cmd)
        self.write((addr >> 8) & 0xff)
        self.write(addr & 0xff)
        self.write(data)
        d = self.read(1)
        self.port.flush() # ?
        if d == bytearray():
            raise NoResponseError
        if (d[0] != com(cmd)):
            raise InvalidResponseError

    def reset(self):
        self.logger.debug("RESET")
        self.writeCommand(RESET)

    def getPODVersion(self):
        data = self.readCommand(VERSION, 2)
        return "{0!s} v{1:02d}.{2:02d}".format(self.DEVICE_NAME, data[0], data[1])

    def readArea(self, addr, length):
        self.write(READ_AREA)
        self.write((addr >> 8) & 0xff)
        self.write(addr & 0xff)
        self.write(length)
        data = self.read(length)
        self.port.flush() # ?
        if len(data) == 0:
            raise NoResponseError
        if len(data) != length:
            #print "Expected: %u Actual %u" % (length, len(data))
            raise InvalidResponseError("Expected {0:d} bytes got {1:d}.".format(length, len(data)))
        return data

    def writeArea(self, addr, length, data):
        self.write(WRITE_AREA)
        self.write((addr >> 8) & 0xff)
        self.write(addr & 0xff)
        self.write(length)
        self.write(tuple(data))
        d = self.read(1)
        self.port.flush() # ?
        if d == bytearray():
            raise NoResponseError
        if (d[0] != com(WRITE_AREA)):
            raise InvalidResponseError

