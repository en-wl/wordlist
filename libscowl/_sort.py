from ._core import *

class RoughGroupInfo(SlotsDataClass):
    __slots__ = ('headword', 'base_pos', 'defn_note', 'lemmas', 'lines')

    def __init__(self):
        self.headword = None
        self.base_pos = None
        self.defn_note = None
        self.lemmas = set()
        self.lines = []

    def parseLine(self, line):
        m = _matchLine(line)
        if m is None:
            raise ValueError(f"bad line: {line}")

        try:
            lemma = parseLemmaPart(m['lemma'].strip()).lemma
        except ValueError:
            raise ValueError(f"bad line: {line}")
        if lemma:
            self.lemmas.add(lemma)

        if self.headword is None:
            self.headword = lemma

        if not self.base_pos:
            base_pos = ifNone(m['base_pos'], '')
            (base_pos, sep, new_base_pos) = base_pos.partition('→')
            if sep:
                self.base_pos = new_base_pos.strip()
            else:
                self.base_pos = base_pos.strip()

        if not self.defn_note:
            defn_note = ifNone(m['defn_note'], '')
            (defn_note, sep, new_defn_note) = defn_note.partition('→')
            if sep:
                self.defn_note = new_defn_note.strip()
            else:
                self.defn_note = defn_note.strip()


    def sortKey(self):
        return (wordOrderKey(self.headword), self.defn_note, basePosInfo[self.base_pos].order_num)

def sortFile(*, infh = None, inFiles = None, outfh = None, fileFormat, indent = True):

    assert fileFormat in ('adjust', 'merge')

    if outfh is None:
        outfh = sys.stdout
    out = StreamWrapper(outfh)

    groups = []
    commentsOnly = []
    gi = RoughGroupInfo()

    def readFile(fh):
        for origLine in fh:
            line = origLine.strip()
            if line == '':
                finishGroup()
                continue

            gi.lines.append(origLine)

            if line.startswith('#'):
                continue

            if fileFormat == 'adjust':
                if line.startswith('+ ') or line.startswith('- ') or line.startswith('= '):
                    line = line[2:]

            gi.parseLine(line)

        finishGroup()

    def finishGroup():
        nonlocal gi
        if gi.headword:
            groups.append(gi)
        elif gi.lines:
            commentsOnly.append(gi)
        gi = RoughGroupInfo()

    if inFiles:
        for fn in inFiles:
            with open(fn) as fh:
                readFile(fh)
    else:
        readFile(sys.stdin if infh is None else infh)


    clusters = _createClusters(groups)

    for cls in clusters:
        for grp in cls.groups:
            for line in grp.lines:
                if indent and fileFormat == 'adjust':
                    line = line.strip()
                    sp = '' if line[0] in ('+', '-', '=') else '  '
                    out.write(f"{sp}{line}\n")
                else:
                    out.write(line)
            out.write("\n")
    for grp in commentsOnly:
        for line in grp.lines:
            out.write(line)
        out.write("\n")

    out.finish()


