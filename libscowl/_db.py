from ._core import *

def openDB(dbfile, create = False, copyFrom = None):

    if not dbfile:
        dbfile = ':memory:'

    if copyFrom:
        create = True

    if dbfile == ':memory:':
        create = True
    elif os.path.exists(dbfile):
        if create is True:
            raise FileExistsError(dbfile)
        create = False
    else: # file doesn't exist
        if create is False:
            raise FileNotFoundError(dbfile)
        create = True

    conn = sqlite3.connect(dbfile, isolation_level = 'DEFERRED')

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON");
    conn.execute("PRAGMA synchronous = OFF");
    conn.execute("PRAGMA temp_store = MEMORY");

    if isinstance(copyFrom, str):
        with openDB(copyFrom) as conn0:
            conn0.backup(conn)
    elif copyFrom:
        copyFrom.backup(conn)
    elif create:
        conn.executescript((_dir / 'schema.sql').read_text())
        conn.executescript((_dir / 'constdata.sql').read_text())
        conn.executescript((_dir / 'fix_pos.sql').read_text())
        conn.executescript((_dir / 'views.sql').read_text())
        conn.executescript((_dir / 'scowl.sql').read_text())

    return conn

def importFromDB(conn, *, filterTable = None, filterQuery = None):
    groups, clusterComments = _importFromDB(conn, filterTable, filterQuery)
    groups = _finalizeGroups(groups, conn)
    return _createClusters(groups, clusterComments)

def _importFromDB(conn, filterTable, filterQuery):
    words = {}

    if filterTable:
        filterQuery = f"select * from {filterTable}"
        filterTable = None
    if filterQuery:
        groupIdFilter = f"(group_id in ({filterQuery}))"
        lemmaIdFilter = f"(lemma_id in (select lemma_id from words where {groupIdFilter}))"
        wordIdFilter = f"(word_id in (select word_id from words where {groupIdFilter}))"
        headwordFilter = f"(headword in (select word from words where {groupIdFilter}))"
    else:
        groupIdFilter = 'true'
        lemmaIdFilter = 'true'
        wordIdFilter = 'true'
        headwordFilter = 'true'

    cur = conn.cursor()

    groups = {}
    for r in cur.execute(f"select * from groups where {groupIdFilter}"):
        grp = Group()
        grp.base_pos = r['base_pos']
        grp.defn_note = r['defn_note']
        grp.usage_note = r['usage_note']
        grp.pos_class = r['pos_class']
        grp.lemma_rank = r['lemma_rank']
        grp._group_id = r['group_id']
        grp.entries = []
        grp.lines = []
        grp.override = {}
        grp.commentLines = GroupComment()
        groups[r['group_id']] = grp

    for r in cur.execute(f"select * from group_comments where {groupIdFilter}"):
        groups[r['group_id']].commentLines = GroupComment(r['comment']);

    wordsById = {}
    lemmasById = {}

    for r in cur.execute(f"select * from lemma_variant_info where {lemmaIdFilter}"):
        lemma_id = r['lemma_id']
        le = lemmasById.get(lemma_id)
        if le is None:
            lemmasById[lemma_id] = le = LemmaEntry()
            le.spellings = Spellings()
        le.spellings.add(r['spelling'],r['variant_level'])

    for r in cur.execute(f"select * from derived_variant_info where {wordIdFilter}"):
        word_id = r['word_id']
        we = wordsById.get(word_id)
        if we is None:
            wordsById[word_id] = we = WordEntry()
            we.spellings = Spellings()
        we.spellings.add(r['spelling'],r['variant_level'])

    for r in cur.execute(f"select * from lemma_comments where {lemmaIdFilter} order by lemma_id, order_num"):
        lemma_id = r['lemma_id']
        le = lemmasById.get(lemma_id)
        if le is None:
            lemmasById[lemma_id] = le = LemmaEntry()
            le.spellings = Spellings()
        le.comments.append(r['comment'])

    lemma_id = -1
    le = None
    for r in cur.execute("select *, dup.word is not null as dup "
                         "from words left join duplicate_derived dup using (group_id, word) "
                         f"where {groupIdFilter} "
                         "order by lemma_id"):
        grp = groups[r['group_id']]
        if r['lemma_id'] != lemma_id:
            lemma_id = r['lemma_id']
            le = lemmasById.pop(lemma_id, None)
            if le is None:
                le = LemmaEntry()
                le.spellings = Spellings()
            le.grp = grp
            grp.entries.append(le)
        word_id = r['word_id']
        we = wordsById.pop(word_id, None)
        if we is None:
            we = WordEntry()
        we.word = r['word']
        we.entry_rank = r['entry_rank']
        we.duplicate = bool(r['dup'])
        le.words.setdefault(r['pos'], []).append(we)
        if r['word_id'] == lemma_id:
            le.lemma = r['word']

    scowlInfoByGroupPos = defaultdict(lambda: defaultdict(list))
    linesByGroup = defaultdict(lambda: defaultdict(set))

    for r in cur.execute("select group_id, level, category, region, pos, group_concat(tag) as tags "
                         "from scowl_data "
                         f"where {groupIdFilter} "
                         "group by group_id, level, category, region, pos"):
        level = r['level']
        category = r['category']
        region = r['region']
        tags = sorted(r['tags'].split(','))
        key = (level, category, region, *tags)
        linesByGroup[r['group_id']][key,].add(r['pos'])
        #scowlInfoByGroupPos[r['group_id']][r['pos']].append(key)

    #for group_id, byPos in scowlInfoByGroupPos.items():
    #    for pos, key in byPos.items():
    #        key.sort()
    #        linesByGroup[group_id][tuple(key)].add(pos)

    for group_id, lines in linesByGroup.items():
        grp = groups[group_id]
        for si, poses in lines.items():
            grp.lines.append(Line(grp, [ScowlInfo(level, category, region, tags) for (level, category, region, *tags) in si], poses))

    overrideByGroup = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in cur.execute("select group_id, level, category, region, lemma, word, group_concat(tag) as tags "
                         "from scowl_override join entries using (word_id) "
                         f"where {wordIdFilter} "
                         "group by group_id, level, category, region, lemma, word"):
        override = overrideByGroup[r['group_id']]
        level = r['level']
        category = r['category']
        region = r['region']
        tags = sorted(r['tags'].split(','))
        key = (level, category, region, *tags)
        override[key][r['lemma']].append(r['word'])

    for group_id, override in overrideByGroup.items():
        grp = groups[group_id]
        for (level, category, region, *tags), ov in override.items():
            for lemma, words in ov.items():
                grp.override[lemma] = Override(grp, [ScowlInfo(level, category, region, tags)], lemma, sorted(w for w in words if w != lemma))

    clusterComments = {}
    for r in cur.execute(f"select * from cluster_comments where {headwordFilter}"):
        clusterComments[clusterKey(r['headword'])] = ClusterComment(r['headword'], r['other_words'], r['comment'])

    for k in list(clusterComments.keys()):
        c = clusterComments[k]
        m = re.match(r'^see note( for | )"?([\w]+)"?', c.comment, re.IGNORECASE)
        if m:
            other = clusterComments[b'koran' if m[2] == 'Quran' else clusterKey(m[2])]
            other.other_words += f' {c.word} {c.other_words}'
            del clusterComments[k]

    return (groups.values(), clusterComments)

def searchDB(conn, words, byCluster):
    conn.execute("create temp table group_id_filter (group_id integer primary key)")
    for w in words:
        conn.execute("insert or ignore into group_id_filter select group_id from words where word = ?", (w,))
    conn.execute("analyze group_id_filter")
    if byCluster:
        conn.execute("insert or ignore into group_id_filter "
                     "select b.group_id from group_id_filter join cluster_map a using (group_id) join cluster_map b using (cluster_id)")
        conn.execute("analyze group_id_filter")
    clusters = importFromDB(conn, filterTable = "group_id_filter")
    conn.execute("drop table group_id_filter")
    return clusters

class BasicGroupInfo(SlotsDataClass):
    __slots__ = ('lemmas', 'group_id')
    def __init__(self, lemmas, group_id):
        self.lemmas = lemmas
        self.group_id = group_id
    @property
    def headword(self):
        return self.lemmas[0]
    def sortKey(self):
        return self.group_id

def createClusterMap(conn):
    groups = []
    for group_id, in conn.execute("select group_id from groups"):
        lemmas = []
        for word, in conn.execute("select word from words where group_id = ? and word_id = lemma_id order by word_id", (group_id,)):
            lemmas.append(word)
        if lemmas:
            groups.append(BasicGroupInfo(lemmas, group_id))
    clusters = _createClusters(groups)
    conn.execute("delete from cluster_map")
    for cls in clusters:
        cluster_id = cls.groups[0].group_id
        for grp in cls.groups:
            conn.execute("insert into cluster_map (group_id, cluster_id) values (?, ?)", (grp.group_id, cluster_id))
    conn.execute("analyze cluster_map")

def finalizeDB(conn):
    createClusterMap(conn)
    conn.commit()
    conn.executescript((_dir / 'post.sql').read_text())

def exportToDB(clusters, conn):
    group_id = 1
    word_id = 1

    conn.execute("delete from scowl_override")
    conn.execute("delete from scowl_data")
    conn.execute("delete from cluster_comments")
    conn.execute("delete from group_comments")
    conn.execute("delete from cluster_comments")
    conn.execute("delete from derived_variant_info")
    conn.execute("delete from lemma_variant_info")
    conn.execute("delete from words")
    conn.execute("delete from groups")

    for cluster in clusters:
        cluster_id = group_id

        for group in cluster.groups:
            conn.execute("insert into cluster_map (group_id, cluster_id) values (?, ?)", (group_id,cluster_id))

            group_id, word_id = _exportGroup(conn, group, group_id, word_id)

        for c in cluster.comments:
            conn.execute("insert into cluster_comments (headword, other_words, comment) values (?, ?, ?)",
                         (c.word, c.other_words, c.comment))

    conn.execute("analyze")
    conn.commit()

    conn.executescript((_dir / 'post.sql').read_text())

def _exportGroup(conn, group, group_id, word_id):
    conn.execute("insert into groups (group_id, base_pos, pos_class, defn_note, usage_note, lemma_rank) values (?, ?, ?, ?, ?, ?)",
                 (group_id, group.base_pos, group.pos_class, group.defn_note, group.usage_note, group.lemma_rank))

    for le in group.entries:
        lemma_id = word_id
        for pos in posmap(group.base_pos, le.words.keys()):
            for we in le.words.get(pos, []):
                conn.execute("insert into words (word_id, group_id, lemma_id, pos, word, entry_rank) values (?, ?, ?, ?, ?, ?)",
                             (word_id, group_id, lemma_id, pos, we.word, we.entry_rank))
                if we.spellings is not None and '' in we.spellings:
                    variant_level = we.spellings['']
                    spellings = le.spellings.keys() if le.spellings else ['_']
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, variant_level) for sp in spellings))
                elif we.spellings is not None:
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, vl) for sp, vl in we.spellings.items()))
                word_id += 1

        conn.executemany("insert into lemma_variant_info (lemma_id, spelling, variant_level) values (?, ?, ?)",
                         ((lemma_id, sp, vl) for sp, vl in le.spellings.items()))

        conn.executemany("insert into lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                         ((lemma_id, i, c) for i, c in enumerate(le.comments)))

        ov = group.override.get(le.lemma, None)
        if ov:
            for si in ov.si:
                for tag in si.tags:
                    conn.execute("insert into scowl_override (level, category, region, tag, word_id) values (?, ?, ?, ?, ?)",
                                 (si.level, si.category, si.region, tag, lemma_id))
                    for word in ov.words:
                        conn.execute("insert into scowl_override "
                                     "select ?, ?, ?, ?, word_id from words where lemma_id = ? and word = ?",
                                     (si.level, si.category, si.region, tag, lemma_id, word))

    for l in group.lines:
        for pos in l.poses:
            for si in l.si:
                for tag in si.tags:
                    conn.execute("insert into scowl_data (level, category, region, tag, group_id, pos) values (?, ?, ?, ?, ?, ?)",
                                 (si.level, si.category, si.region, tag, group_id, pos))

    if group.commentLines:
        conn.execute("insert into group_comments (group_id, comment) values (?, ?)",
                     (group_id, str(group.commentLines)))

    group_id += 2 if group.base_pos in ('n_v', 'aj_av') else 1
    return (group_id, word_id)

__all__ = [sym for sym in globals().keys() if not sym.startswith('__')]
