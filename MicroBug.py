# Fix invalid path to python interpreter on Kubas's ntb
import sys
_invalidPythonPath = 'C:\\Users\\kubas\\.platformio\\python27'
_validPythonPath = 'C:\\Program Files (x86)\\Python27'
for i in xrange(len(sys.path)):
    if _invalidPythonPath in sys.path[i]:
        sys.path[i] = _validPythonPath + sys.path[i][len(_invalidPythonPath):]

import struct
from collections import OrderedDict as odict
from math import *

# You can use terminal.clear() and terminal.appendText(string) to set term content
# You can use lorris.sendData(list) to send data to device.

# This function gets called on data received
# it should return string, which is automatically appended to terminal
def onDataChanged(data, dev, cmd, index):
    return microbug.parse(data, dev, cmd, index)

# This function is called on key press in terminal.
# Param is string
def onKeyPress(key):
    return

class MicroBug:
    
    ERR_RX_PACKET_NUM_INIT              = 1
    ERR_INVALID_RX_PACKET_NUM_INIT      = 2
    ERR_INVALID_RX_PACKET_NUM           = 3
    ERR_INVALID_CHECKSUM                = 4
    ERR_INVALID_LENGTH                  = 5
    
    def __init__(self):
        self.rxHeaderLen = 8
        self.txHeaderLen = 4
        self.bytesPerNumber = 4
        self.checksumLen = 2
        self.rxPacketNum = None
        self.txPacketNum = 0
        self.microbitRxBufferSize = 64
        
    @staticmethod
    def _tobyte(value):
        return value if value >= 0 else (256 + value)
        
    @staticmethod
    def _nextPacket(counter):
        return (counter + 1) & 0xFF
    
    def parse(self, data, dev, cmd, index):
        res = ''
        if data.length() < (self.rxHeaderLen + self.checksumLen):
            return 'Received invalid packet with too few data ({:2}): [{}].\n'.format(data.length(), \
                ', '.join('{:02X}'.format(MicroBug._tobyte(data.at(i))) for i in xrange(data.length())))
        bdata = bytes(bytearray(MicroBug._tobyte(data.at(i)) for i in xrange(data.length())))
        recPacketNum = struct.unpack('B', bdata[3])[0]
        recTimestamp = struct.unpack('<I', bdata[4:8])[0]
        recChecksum = struct.unpack('<H', bdata[-self.checksumLen:])[0]
        checksum = sum(struct.unpack('{}B'.format(len(bdata)-(1+self.checksumLen)), bdata[1:-self.checksumLen]))
        errors = odict()
        if self.rxPacketNum is None:
            if recChecksum == checksum:
                self.rxPacketNum = recPacketNum
                errors[MicroBug.ERR_RX_PACKET_NUM_INIT] = 'Rx packet counter initialized by packet {}.'.format(self.rxPacketNum)
            else:
                errors[MicroBug.ERR_INVALID_RX_PACKET_NUM_INIT] = 'Can not initialize Rx packet counter by invalid packet.'
        elif self.rxPacketNum != recPacketNum:
            errors[MicroBug.ERR_INVALID_RX_PACKET_NUM] = 'Invalid packet number: received {} but {} expected.'.format(recPacketNum, self.rxPacketNum)
        self.rxPacketNum = MicroBug._nextPacket(self.rxPacketNum)
        if recChecksum != checksum:
            errors[MicroBug.ERR_INVALID_CHECKSUM] = 'Invalid checksum: received {}, but {} computed.'.format(recChecksum, checksum)
        else:
            values = len(bdata) - self.rxHeaderLen - self.checksumLen
            if (values % self.bytesPerNumber) != 0:
                errors[MicroBug.ERR_INVALID_LENGTH] = 'Received packet contains {} bytes, which is not multiple of {} bytes.'.format(values, self.bytesPerNumber)
            else:
                values /= self.bytesPerNumber
                values = struct.unpack('<{}f'.format(values), bdata[self.rxHeaderLen:-self.checksumLen])
                if cmd == 0:
                    if len(values) == 0:
                        res = 'micro:bit reset\n'
                    else:
                        res = 'micro:bit reset with data: {}\n'.format(values)
                    self.rxPacketNum = 0
                    self.txPacketNum = 0
                    if MicroBug.ERR_INVALID_RX_PACKET_NUM in errors:
                        del errors[MicroBug.ERR_INVALID_RX_PACKET_NUM]
        if errors:
            res = 'Errors:' + '\n\t'.join(errors.values()) + '\n' + res
        return res
        
microbug = MicroBug()
