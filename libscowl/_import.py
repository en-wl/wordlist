from ._core import *

def _mergeText(f, groups, clusterComments):
    grp = None
    lines = []
    override = []
    entriesBySpellings = {}
    commentLines = []
    for lineStr in chain(f, ['']):
        lineStr = lineStr.strip()
        if lineStr == '':
            if lines:
                grp.lines = lines
                grp.entries = list(entriesBySpellings.values())
                have = addMissingSpellings(grp.entries)
                for le in grp.entries:
                    for wes in le.words.values():
                        addMissingSpellings(wes, have)
                groups.append(grp)
                if commentLines:
                    grp.commentLines = GroupComment.parse(*commentLines)
                grp.override = {}
                for ov in override:
                    grp.override[ov.lemma] = ov
            elif commentLines:
                c = ClusterComment.parse(*commentLines)
                clusterComments[clusterKey(c.word)] = c
            grp = None
            lines = []
            override.clear()
            entriesBySpellings.clear()
            commentLines.clear()
            continue

        if grp is None:
            grp = Group()
            grp.commentLines = GroupComment('')

        try:
            l = Line.parse(lineStr, grp, entriesBySpellings)
        except ValueError as err:
            raise ValueError(f'invalid line: {lineStr}') from err

        if l is None:
            if lineStr.startswith('##'):
                commentLines.append(lineStr)
                continue
            elif lineStr.startswith(('# ', '#!', '#:')):
                continue

        if l is None:
            raise ValueError(f'invalid line: {lineStr}')

        if isinstance(l, Override):
            override.append(l)
        else:
            lines.append(l)

def importText(f = None):
    groups = []
    clusterComments = {}
    _mergeText(sys.stdin if f is None else f, groups, clusterComments)
    groups = _finalizeGroups(groups)
    return _createClusters(groups, clusterComments)

BasicInfo = namedtuple('BasicInfo', 'base_pos pos_class word is_lemma')

def roughParse(f = None):
    if f is None:
        f = sys.stdin

    for line in f:
        line = line.strip()
        if line == '' or line.startswith('#'):
            continue

        m = _matchLine(line)
        if m is None:
            raise ValueError(f"bad line: {line}")
        try:
            (group_rank, lemma, entry_rank) = parseLemmaPart(m['lemma'])
            if lemma:
                base_pos = m['base_pos']
                pos_class = m['pos_class']
                yield BasicInfo(base_pos, pos_class, lemma, True)

            words = _splitWords(m['words'])
        except Exception:
            raise ValueError(f"bad line: {line}")

        for ws in words:
            for we in ws:
                yield BasicInfo(base_pos, pos_class, we.word, False)

__all__ = [sym for sym in globals().keys() if not sym.startswith('__')]
