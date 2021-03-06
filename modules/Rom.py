import array
import os
import yaml

from copy import copy

class Rom:
    def __init__(self, romtypeFname=None):
        self._data = array.array('B')
        self._size = 0
        self._type = "Unknown"
        self._type_map = { }
        self._freeRanges = [ ]
        if (romtypeFname):
            with open(romtypeFname, 'r') as f:
                self._type_map = yaml.load(f, Loader=yaml.CSafeLoader)
    def copy(self):
        r = Rom()
        r._data = copy(self._data)
        r._size = self._size
        r._type = self._type
        r._type_map = self._type_map
        r._freeRanges = self._freeRanges
    def checkRomType(self):
        for t, d in self._type_map.iteritems():
            offset, data, platform = d['offset'], d['data'], d['platform']

            if (platform == "SNES"):
                # Validate the ROM and check if it's headered

                # Check for unheadered HiROM
                try:
                    if (~self[0xffdc] & 0xff == self[0xffde]) \
                            and (~self[0xffdd] & 0xff == self[0xffdf]) \
                            and (self[offset:offset+len(data)].tolist()==data):
                        return t
                except IndexError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x7fdc] & 0xff == self[0x7fde]) \
                            and (~self[0x7fdd] & 0xff == self[0x7fdf]) \
                            and (self[offset:offset+len(data)].tolist()==data):
                        return t
                except IndexError:
                    pass

                # Check for headered HiROM
                try:
                    if (~self[0x101dc] & 0xff == self[0x101de]) \
                            and (~self[0x101dd] & 0xff == self[0x101df]) \
                            and (self[
                                offset+0x200:offset+0x200+len(data)].tolist()
                                ==data):
                        # Remove header
                        self._data = self._data[0x200:]
                        self._size -= 0x200
                        return t
                except IndexError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x81dc] & 0xff == self[0x81de]) \
                            and (~self[0x81dd] & 0xff == self[0x81df]) \
                            and (self[
                                offset+0x200:offset+0x200+len(data)].tolist()
                                ==data):
                        # Remove header
                        self._data = self._data[0x200:]
                        self._size -= 0x200
                        return t
                except:
                    pass

            elif (self[offset:offset+len(data)].tolist() == data):
                return t
        else:
            return "Unknown"
    def load(self, f):
        if isinstance(f, basestring):
            f = open(f,'rb')
        self._size = int(os.path.getsize(f.name))
        self._data = array.array('B')
        self._data.fromfile(f, self._size)
        f.close()
        self._type = self.checkRomType()
        if (self._type != "Unknown" and
                self._type_map[self._type].has_key('free ranges')):
            #self._free_loc = self._type_map[self._type]['free space']
            self._freeRanges = map(
                    lambda y: tuple(map(lambda z: int(z, 0),
                        y[1:-1].split(','))),
                    self._type_map[self._type]['free ranges'])
            self._freeRanges = [(a,b) for (a,b)
                    in self._freeRanges if (b < self._size) ]
            self._freeRanges.sort()
        else:
            self._freeRanges = []
    def save(self, f):
        # Make the last byte 0xff to be compatible with Lunar IPS patcher
        self[self._size-1] = 0xff
        if (type(f) == str) or (type(f) == unicode):
            f = open(f, 'wb')
        self._data.tofile(f)
    def type(self):
        return self._type
    # Header stuff
    def addHeader(self):
        if self._type == 'Earthbound':
            for i in range(0x200):
                self._data.insert(0, 0)
            self._size += 0x200
        else:
            raise RuntimeError(
                    "Don't know how to add header to ROM of type \"" +
                    self._type + "\".")
    # Expansion
    def expand(self, newSize):
        if self._type == 'Earthbound':
            if (newSize != 0x400000) and (newSize != 0x600000):
                raise RuntimeError("Cannot expand an Earthbound ROM to " +
                        hex(newSize) + " bytes.")
            else:
                if len(self) == 0x300000:
                    self._data.fromlist([0] * 0x100000)
                    self._size += 0x100000
                    # For the super old text editor, heh
                    #for i in range(0,4096):
                    #    r[i*256 + 255 + 0x300000] = 2
                if (newSize == 0x600000) and (len(self) == 0x400000):
                    self[0x00ffd5] = 0x25
                    self[0x00ffd7] = 0x0d
                    self._data.fromlist([0] * 0x200000)
                    self._size += 0x200000
                    for i in range(0x8000, 0x8000 + 0x8000):
                        self[0x400000 + i] = self[i]
        else:
            raise RuntimeError("Don't know how to expand ROM of type \"" +
                    self._type + "\".")
    # Reading methods
    def read(self, i):
        if (i < 0) or (i >= self._size):
            raise ValueError("Reading outside of ROM range")
        return self._data[i]
    def readList(self, i, len):
        if (len < 0):
            raise ValueError("Can only read a list of non-negative length")
        elif (i < 0) or (i >= self._size) or (i+len > self._size):
            raise ValueError("Reading outside of ROM range")
        return self._data[i:i+len]
    def readMulti(self, i, len):
        # Note: reads in reverse endian
        if (len < 0):
            raise ValueError("Can only read an int of non-negative length")
        elif (i < 0) or (i >= self._size) or (i+len > self._size):
            raise ValueError("Reading outside of ROM range")
        d = self[i:i+len]
        d.reverse()
        return reduce(lambda x,y: (x<<8)|y, d)
    # Writing methods
    def write(self, i, data):
        if type(data) == int:
            if (i < 0) or (i >= self._size):
                raise ValueError("Writing outside of ROM range")
            self[i] = data
        elif type(data) == list:
            if (i < 0) or (i >= self._size) or (i+len(data) > self._size):
                raise ValueError("Writing outside of ROM range (" + hex(i) + "+"
                    + str(len(data)) + "/" + hex(self._size) + ")")
            self[i:i+len(data)] = data
        elif type(data) == array.array:
            if (i < 0) or (i >= self._size) or (i+len(data) > self._size):
                raise ValueError("Writing outside of ROM range")
            self[i:i+len(data)] = data
        else:
            raise ValueError("write(): data must be either a list, array, or int")
    def writeMulti(self, i, data, size):
        while size > 0:
            self.write(i, data & 0xff)
            data >>= 8
            size -= 1
            i += 1
    def addFreeRanges(self, ranges):
        # TODO do some check so that free ranges don't overlap
        self._freeRanges += ranges
        self._freeRanges.sort()
    def isRangeFree(self, searchRange):
        searchBegin, searchEnd = searchRange
        for begin, end in self._freeRanges:
            if (searchBegin >= begin) and (searchEnd <= end):
                return True
        return False
    def markRangeAsNotFree(self, usedRange):
        usedBegin, usedEnd = usedRange
        for i in range(len(self._freeRanges)):
            begin, end = self._freeRanges[i]
            if usedBegin == begin:
                if usedEnd < end:
                    self._freeRanges[i] = (usedEnd+1, end)
                elif usedEnd == end:
                    del(self._freeRanges[i])
                else: # usedEnd > end
                    del(self._freeRanges[i])
                    self.markRangeAsNotFree((end+1, usedEnd))
                break
            elif (usedBegin > begin) and (usedEnd <= end):
                self._freeRanges[i] = (begin, usedBegin-1)
                if usedEnd != end:
                    self._freeRanges.insert(i, (usedEnd+1, end))
                break
    # Find a free range starting at addr such that add & mask == 0
    def getFreeLoc(self, size, mask=0):
        ranges = filter(lambda (x,y): x & mask == 0, self._freeRanges)
        for i in range(0, len(self._freeRanges)):
            begin, end = self._freeRanges[i]
            if begin & mask != 0:
                continue
            if size <= end-begin+1:
                if begin+size == end:
                    # Used up the entire free range
                    del(self._freeRanges[i])
                else:
                    self._freeRanges[i] = (begin+size, end)
                return begin
        # TODO what if there is enough free space available, but not starting
        # with the mask?
        raise RuntimeError("Not enough free space left in the ROM."
            + " Try using an expanded ROM as your base ROM.")
    def writeToFree(self, data):
        loc = self.getFreeLoc(len(data))
        self.write(loc, data)
        return loc
    # Overloaded operators
    def __getitem__(self, key):
        if (type(key) == slice):
            return self._data[key]
        else:
            return self._data[key]
    def __setitem__(self, key, item):
        if (type(key) == slice):
            self._data[key] = array.array('B',item)
        else:
            self._data[key] = item
    def __len__(self):
        return self._size
    def __eq__(self, other):
        return (type(other) == type(self)) and (self._data == other._data)
    def __ne__(self, other):
        return not (self == other)
