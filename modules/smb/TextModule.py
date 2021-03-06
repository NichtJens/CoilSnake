import SmbModule
from modules.Progress import updateProgress

import yaml

class TextModule(SmbModule.SmbModule):
    _name = "Text"
    ENTRY_LOCS = [
            ( "Title Screen", [
                ( "Copyright", 0x09fb5, 0x0e ),
                ( "Choice 1", 0x09fc6, 0x0d ),
                ( "Choice 2", 0x09fd6, 0x0d ),
                ( "Top", 0x09fe6, 0x04 )]),
            ( "HUD", [
                ( "Player 1", 0x00765, 5 ),
                ( "World (Top)", 0x0076D, 5 ),
                ( "Time", 0x00774, 4 ),
                ( "Coins", 0x0077e, 2 ),
                ( "World (Black Screen)", 0x00796, 5 ),
                ( "Time Up", 0x007b3, 7 ),
                ( "Game Over", 0x007c6, 9 ),
                ( "Warp Zone Welcome", 0x007d3, 0x15 ),
                ( "Player 2", 0x007fd, 5 ) ])
            ]
    def __init__(self):
        self._data = {}
        self._pct = 50.0/len(self.ENTRY_LOCS)
    def readFromRom(self, rom):
        for (cat, items) in self.ENTRY_LOCS:
            catDict = {}
            for (desc, loc, size) in items:
                catDict[desc] = SmbModule.readText(rom, loc, size)
            self._data[cat] = catDict
            updateProgress(self._pct)
    def writeToRom(self, rom):
        for (cat, items) in self.ENTRY_LOCS:
            catDict = self._data[cat]
            for (desc, loc, size) in items:
                SmbModule.writeText(rom, loc, catDict[desc], size)
            updateProgress(self._pct)
    def writeToProject(self, resourceOpener):
        with resourceOpener("text", "yml") as f:
            yaml.dump(self._data, f, default_flow_style=False,
                    Dumper=yaml.CSafeDumper)
        updateProgress(50.0)
    def readFromProject(self, resourceOpener):
        with resourceOpener("text", "yml") as f:
            self._data = yaml.load(f, Loader=yaml.CSafeLoader)
        updateProgress(50.0)
