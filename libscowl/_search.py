from ._core import *
from ._db import *
from ._misc import *

class SetFilter(set):
    def __init__(self, *members, noDefault = False):
        super().__init__(members)
        if noDefault:
            self._excludeDefault = True
    def _copy(self, newMembers):
        other = self.__class__(*newMembers)
        if hasattr(self, '_excludeDefault'):
            other._excludeDefault = True
        return other

class Include (SetFilter):
    pass

class Exclude (SetFilter):
    pass

Query = namedtuple('Query', 'select from_ where')

def queryString(
        *,
        size = None,
        spellings = None,
        regions = None,
        variantLevel = None,
        variantLevels = None,
        poses = None,
        posClasses = None,
        posCategories = None,
        categories = None,
        tags = None,
        usageNotes = None,
):
    clauses = []
    if size is not None:
        size = int(size)
        if size < 0 or size > 99:
            raise ValueError(size)
        clauses.append(f"size <= {size}")

    if variantLevel is not None:
        try:
            vl = int(variantLevel)
        except ValueError:
            vl = variantFromSymbol[variantLevel]
        clauses.append(f"variant_level <= {vl}")

    if variantLevels is not None:
        if variantLevel is not None:
            raise ValueError('both variantLevel and variantLevels can not be defined at the same time')
        clauses.append(f"variant_level in ({','.join(str(int(v)) for v in sorted(variantLevels))})")

    def addSetQueryClause(var, check, default, members):
        if members is None:
            return
        for member in members:
            if not check(member):
                raise ValueError(member)
        if isinstance(members, Exclude):
            if not members:
                raise ValueError
            clauses.append("{} not in ({})".format(var,
                                                   ','.join(f"'{v}'" for v in set(members))))
        else:
            m = set(members)
            if default is not None and not getattr(members, '_excludeDefault', False):
                m.add(default)
            if not m:
                raise ValueError
            clauses.append("{} in ({})".format(var,
                                               ','.join(f"'{v}'" for v in m)))

    addSetQueryClause('spelling', lambda sp: sp in SPELLINGS, '_', spellings)

    if regions is None and spellings is not None:
        regions = [spellingInfo[sp].region for sp in spellings]

    addSetQueryClause('region', lambda r: r in REGIONS, '', regions)

    if poses:
        if not isinstance(poses, SetFilter):
            poses = Include(*poses)
        basePoses = poses._copy(poses & basePosInfo.keys())
        poses.difference_update(basePosInfo.keys())
        wordPoses = poses._copy(poses & posInfo.keys())
        poses.difference_update(posInfo.keys())
        for p in poses:
            raise ValueError(p)
        if basePoses:
            if 'n_v' in basePoses:
                basePoses |= {'n', 'v'}
            elif 'n' in basePoses or 'v' in basePoses:
                basePoses.add('n_v')
            if 'aj_av' in basePoses:
                basePoses |= {'aj', 'av'}
            elif 'aj' in basePoses or 'av' in basePoses:
                basePoses.add('aj_av')
            addSetQueryClause('base_pos', lambda _: True, None, basePoses)
        if wordPoses:
            addSetQueryClause('pos', lambda _: True, None, wordPoses)

    elif poses is not None:
        raise ValueError("poses can't be empty")

    addSetQueryClause('pos_class', lambda _: True, '', posClasses)

    addSetQueryClause('pos_category', lambda p: p in POS_CATEGORIES, '', posCategories)

    addSetQueryClause('category', lambda _: True, '', categories)

    addSetQueryClause('tag', lambda _: True, '', tags)

    addSetQueryClause('usage_note', lambda _: True, '', usageNotes)

    if not clauses:
        clauses.append('true')

    return Query(
        "select distinct word",
        "from scowl_v0",
        "where {}".format(' and '.join(clauses)),
    )

def wordFilterRegEx(
        *,
        space = False,
        hyphen  = False,
        dot = 'strip',
        digits = False,
        special = False,
        apostrophe = 'middle',
):
        charSet = ''.join([_orderAlpha,
                           '0-9' if digits else '',
                           '.' if dot is True else '',
                           "'" if apostrophe is True else '',
                           '&/' if special else '',
                           ' ' if space else '',
                           '-' if hyphen else ''])
        charSetMiddle = ''.join(["'" if apostrophe == 'middle' else '',
                                 charSet])
        return ''.join([rf"([{charSet}](?:[{charSetMiddle}]*[{charSet}]|))",
                        r'\.?' if dot == 'strip' else ''])

def getWords(conn, size, spellings, variantLevel,
             *, deaccent = False, useWordFilter = True, nosuggest = None, nosuggestSuffix = '/!', **args):
    """Returns a generator of words based on the arguments.

    Many arguments can filter by either including or excluding a set of
    values.  If the argument is a sequence then it will included the given
    along with the default value.  To not include the default use the Include
    class with the the noDefault parameter set to True.  To exclude values
    instead, use the Exclude class.  If _regions_ is None then it depends on
    _spellings_.  If any other argument is None it means to not filter based
    on that argument.

    """

    queryArgs = {**{p.name: args.pop(p.name, p.default) for p in signature(queryString).parameters.values()},
                 'size': size, 'spellings': spellings, 'variantLevel': variantLevel}
    print(queryArgs, file=sys.stderr)
    query = ' '.join(queryString(**queryArgs))
    print(query, file=sys.stderr)

    filterArgs = {p.name: args.pop(p.name, p.default) for p in signature(wordFilterRegEx).parameters.values()}
    if useWordFilter:
        wordFilter = re.compile(wordFilterRegEx(**filterArgs))
        print(wordFilter.pattern, file=sys.stderr)

    if args:
        raise TypeError("unexpected args: {}".format(', '.join(args.keys())))

    if deaccent:
        deaccent = globals()['deaccent']
    else:
        deaccent = None

    nosuggestWords = set()
    if nosuggest is not None:
        if nosuggest:
            nosuggest = set(nosuggest)
        else:
            nosuggest = {'vulgar-1', 'vulgar-2', 'offensive-1', 'offensive-2'}
        possibleValues = {'vulgar-1', 'vulgar-2', 'vulgar-3', 'offensive-1', 'offensive-2', 'offensive-3'}
        leftover = nosuggest - possibleValues
        if leftover:
            raise ValueError(leftover) # fixme
        choices = ','.join(f"'{c}'" for c in nosuggest)
        nosuggestQuery = f"select word from words join groups using (group_id) where usage_note in ({choices})"
        print(nosuggestQuery, file=sys.stderr)
        nosuggestWords.update(w for w, in conn.execute(nosuggestQuery))

    for w, in conn.execute(query):
        orig = w
        if useWordFilter:
            m = wordFilter.fullmatch(w)
            if not m:
                continue
            w = m[1]
        if deaccent:
            w = deaccent(w)
        if orig in nosuggestWords:
            w = f"{w}{nosuggestSuffix}"
        yield w

import inspect
from inspect import signature,Signature,Parameter

getWords.__signature__ = Signature([
    *(p for p in signature(getWords).parameters.values() if p.kind == Parameter.POSITIONAL_OR_KEYWORD),
    *(p for p in signature(queryString).parameters.values() if p.name not in ('size', 'spellings', 'variantLevel')),
    *signature(wordFilterRegEx).parameters.values(),
    *(p for p in signature(getWords).parameters.values() if p.kind == Parameter.KEYWORD_ONLY),
])

def _filterDB(filterType, conn, orig, *, simplify = (), **args):
    queryArgs = {p.name: args.pop(p.name, p.default) for p in signature(queryString).parameters.values()}
    whereClause = queryString(**queryArgs).where
    if 'variantsOnly' in args:
        del args['variantsOnly']
        whereClause = f"{whereClause} and group_id in (select group_id from orig.words group by group_id, pos having count(*) > 1)"
    print(whereClause, file=sys.stderr)
    if args:
        raise TypeError("unexpected args: {}".format(', '.join(args.keys())))

    conn.execute('attach database ? as orig', (orig,))

    if filterType == 'by-line':
        simplify = set(simplify)
        _filterByLine(conn, simplify, queryArgs, whereClause)
    elif filterType == 'by-group':
        simplify = ()
        _filterByGroup(conn, whereClause)
    elif filterType == 'by-cluster':
        simplify = ()
        _filterByGroup(conn, whereClause, includeCluster = True)
    else:
        raise ValueError(f"invalid filter type: {filterType}")

    conn.execute("insert into cluster_comments select * from orig.cluster_comments where headword in (select word from words)")
    conn.execute("insert into group_comments select * from orig.group_comments where group_id in (select group_id from groups)")
    conn.execute("insert into lemma_comments select * from orig.lemma_comments where lemma_id in (select lemma_id from words)")

    conn.execute("insert into fuzzy select * from orig.fuzzy where word in (select word from words)")
    conn.execute("insert into cluster_map select * from orig.cluster_map where group_id in (select group_id from groups)")

    conn.execute("insert into _combined select * from orig._combined where group_id in (select group_id from groups)")

    conn.execute("insert into _variables values(?, ?)", ('filter_type', filterType))
    conn.execute("insert into _variables values(?, ?)", ('filter_where_clause', whereClause))
    if simplify:
        conn.execute("insert into _variables values(?, ?)", ('filter_simplifications', ', '.join(sorted(simplify))))

def _filterByLine(conn, simplify, queryArgs, whereClause):
    conn.execute(f"create temp table filtered as select group_id, lemma_id, word_id from orig.scowl_ {whereClause}")
    conn.execute("insert into groups select * from orig.groups where group_id in (select group_id from filtered)")
    conn.execute("insert into words select * from orig.words where word_id in (select word_id from filtered union select lemma_id from filtered)")

    if queryArgs['size'] is None:
        simplify.discard('size')
    leftover = simplify - {'size', 'category', 'region', 'tag', 'tags'}
    if leftover:
        raise ValueError(f"invalid values for simplify: {', '.join(sorted(leftover))}")

    _size_ = queryArgs['size'] if 'size' in simplify else 'size'
    _category_ = "''" if 'category' in simplify else 'category'
    _region_ = "''" if 'region' in simplify else 'region'
    _tag_ = "''" if 'tag' in simplify or 'tags' in simplify else 'tag'
    conn.execute(f"insert or ignore into scowl_data select {_size_}, {_category_}, {_region_}, {_tag_}, group_id, pos from orig._scowl_main {whereClause}")
    conn.execute(f"insert or ignore into scowl_override select {_size_}, {_category_}, {_region_}, {_tag_}, word_id from orig._scowl_override {whereClause}")
    if simplify:
        cleanupScowlData(conn)

    conn.execute("create temp table filtered_variant_info as select lemma_id, word_id, spelling, lemma_variant_level, derived_variant_level "
                 "from orig._scowl_main "
                 f"{whereClause} and (lemma_variant_level is not null or derived_variant_level is not null)")
    spellings = queryArgs['spellings']
    if spellings and len(spellings) == 1:
        conn.execute("insert into lemma_variant_info "
                     "select lemma_id, '_', min(lemma_variant_level) from filtered_variant_info where lemma_variant_level is not null group by lemma_id")
        conn.execute("insert into derived_variant_info "
                     "select word_id, '_', min(derived_variant_level) from filtered_variant_info where derived_variant_level is not null group by word_id")
        conn.execute("analyze")
        conn.execute("delete from lemma_variant_info "
                     "where lemma_id in (select lemma_id from lemmas where group_id in ("
                     "  select group_id from lemma_variant_info join lemmas using (lemma_id) group by group_id having min(variant_level = 0) is True))")
        conn.execute("delete from derived_variant_info "
                     "where word_id in (select word_id from words where (lemma_id, pos) in ("
                     "  select lemma_id, pos from derived_variant_info join words using (word_id) group by lemma_id, pos having min(variant_level = 0) is True))")
        simplify.add('spellings')
    else:
        conn.execute("insert into lemma_variant_info "
                     "select distinct lemma_id, spelling, lemma_variant_level from filtered_variant_info where lemma_variant_level is not null")
        conn.execute("insert into derived_variant_info "
                     "select distinct word_id, spelling, derived_variant_level from filtered_variant_info where derived_variant_level is not null")
        conn.execute("analyze")

    pruneConstTables(conn)

def _filterByGroup(conn, whereClause, includeCluster = False):
    conn.execute("create temp table filtered (group_id integer primary key)")
    conn.execute(f"insert or ignore into filtered select group_id from orig.scowl_ {whereClause}")

    if includeCluster:
        conn.execute("insert or ignore into filtered "
                     "select b.group_id from cluster_map a join filtered using (group_id) join cluster_map b using (cluster_id)")

    conn.execute("insert into groups select * from orig.groups where group_id in (select group_id from filtered)")
    conn.execute("insert into words select * from orig.words where group_id in (select group_id from filtered)")

    conn.execute("insert into scowl_data select * from orig.scowl_data where group_id in (select group_id from filtered)")
    conn.execute("insert or ignore into scowl_override select size, category, region, tag, word_id "
                 "from orig._scowl_override where group_id in (select group_id from filtered)")

    conn.execute("insert into lemma_variant_info "
                 "select v.* from orig.lemma_variant_info v join lemmas using (lemma_id) where group_id in (select group_id from filtered)")
    conn.execute("insert into derived_variant_info "
                 "select v.* from orig.derived_variant_info v join words using (word_id) where group_id in (select group_id from filtered)")

def cleanupScowlData(conn):
    cleanupWhereClause = ("where a.size <= b.size "
                          "and (a.category = b.category or a.category = '' and b.category != '') "
                          "and (a.region = b.region or a.region = '' and b.region != '') "
                          "and (a.tag = b.tag or a.tag = '' and b.tag != '') "
                          "and (a.category != b.category or a.region != b.region or a.tag != b.tag) ")
    conn.execute("delete from scowl_data "
                 "where (size, category, region, tag, group_id, pos) "
                 f"in (select b.* from scowl_data a join scowl_data b using(group_id,pos) {cleanupWhereClause})")
    conn.execute("delete from scowl_override "
                 "where (size, category, region, tag, word_id) "
                 f"in (select b.* from scowl_override a join scowl_override b using(word_id) {cleanupWhereClause})")

def pruneConstTables(conn):
    conn.execute('create temp table used_variant_info as '
                 'select spelling, variant_level from lemma_variant_info '
                 'union '
                 'select spelling, variant_level from derived_variant_info')
    conn.execute("delete from spellings where spelling not in (select spelling from used_variant_info)")
    conn.execute("delete from variant_levels where variant_level not in (select variant_level from used_variant_info)")

def filterDB(orig, new, filterType, **args):

    conn = openDB(new, create=True)
    _filterDB(filterType, conn, orig, **args)
    conn.commit()
    if filterType == 'by-line' and conn.execute("select true from orig.groups where base_pos in ('n_v','aj_av') limit 1").fetchone():
        conn.executescript((_dir / 'combine_pos.sql').read_text())

    conn.executescript((_dir / 'post.sql').read_text())
    return conn

def searchDB(conn, words, byCluster, exact = False, **args):
    queryArgs = {p.name: args.pop(p.name, p.default) for p in signature(queryString).parameters.values()}
    whereClause = queryString(**queryArgs).where

    conn.execute("create temp table filtered (word_id integer primary key, group_id integer not null)")
    if exact:
        for w in words:
            conn.execute("insert or ignore into filtered select word_id, group_id from words where word = ?", (w,))
    else:
        for w in words:
            w = clusterKey(w).decode('ascii')
            conn.execute("insert or ignore into filtered select word_id, group_id from words join fuzzy using (word) where word_key = ?", (w,))

    conn.execute("create temp table group_id_filter (group_id integer not null)")
    if whereClause == 'where true':
        conn.execute("insert or ignore into group_id_filter select group_id from filtered")
    else:
        print(whereClause, file=sys.stderr)
        conn.execute("analyze filtered")
        conn.execute(f"insert or ignore into group_id_filter select group_id from filtered join scowl_ using (group_id, word_id) {whereClause}")
    conn.execute("drop table filtered")
    conn.execute("analyze group_id_filter")

    if byCluster:
        conn.execute("insert or ignore into group_id_filter "
                     "select b.group_id from group_id_filter join cluster_map a using (group_id) join cluster_map b using (cluster_id)")
        conn.execute("analyze group_id_filter")

    clusters = importFromDB(conn, filterTable = "group_id_filter")
    conn.execute("drop table group_id_filter")
    return clusters
