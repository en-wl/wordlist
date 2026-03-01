import io

from contextlib import suppress
from tempfile import NamedTemporaryFile

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
        if lemma and lemma != '...':
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

def sortFileInPlace(*, files, indent = False):
    destFile = Path(files[0]).resolve(strict=True)
    if not destFile.is_file():
        raise OSError(None, 'Not a normal file', str(destFile))
    infh = io.StringIO(destFile.read_text())
    outfh = io.StringIO()
    sortFile(infh = infh, inFiles = files[1:], outfh = outfh, indent=indent)
    inStr = infh.getvalue()
    outStr = outfh.getvalue()
    if inStr == outStr:
        return
    fp = NamedTemporaryFile(mode='wb', delete = False, prefix=".tmp", dir=destFile.parent)
    try:
        fp.write(outStr.encode('utf-8'))
        fp.close()
        os.replace(fp.name, destFile)
    except:
        fp.close()
        with suppress(FileNotFoundError):
            os.remove(fp.name)
        raise

def sortFile(*, infh = None, inFiles = (), outfh = None, indent = False):
    if outfh is None:
        outfh = sys.stdout
    out = StreamWrapper(outfh)

    groups = []
    commentsOnly = []
    gi = RoughGroupInfo()
    fileFormat = None
    header = None

    def readFile(fh):
        nonlocal fileFormat, header

        headerLine = next(fh)
        hdr = headerLine.split()
        if len(hdr) < 2 or hdr[0] != '#::':
            raise ValueError("invalid file format: file must start with a '#::' header line")
        if hdr[1] not in ('adjust', 'merge'):
            raise ValueError(f"unrecognized file format: {fileFormat}")
        if header and header[1] != hdr[1]:
            raise ValueError("can't merge files of a different type")
        else:
            fileFormat = hdr[1]
            header = hdr

        for origLine in fh:
            line = origLine.strip()
            if line == '':
                finishGroup()
                continue

            gi.lines.append(origLine)

            if fileFormat == 'adjust':
                if len(line) >= 2 and line[1] == ' ' and line[0] in ('+', '-', '=', '~', '?'):
                    line = line[2:].lstrip()

            if line.startswith('#'):
                continue

            gi.parseLine(line)

        finishGroup()

    def finishGroup():
        nonlocal gi
        if gi.headword:
            groups.append(gi)
        elif gi.lines:
            commentsOnly.append(gi)
        gi = RoughGroupInfo()

    if infh is None and not inFiles:
        readFile(sys.stdin)
    elif infh is not None:
        readFile(infh)

    for fn in inFiles:
        with open(fn) as fh:
            readFile(fh)

    clusters = _createClusters(groups)

    print(*header, file=out)
    out.write("\n")
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


