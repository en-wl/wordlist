from ._core import *

def exportAsText(clusters, conn = None, out = None, *, trimSpellings = True, showClusters = False, showExtraInfo = True):
    if out is None:
        out = sys.stdout
    out = StreamWrapper(out)

    dbVars = SimpleNamespace()
    if conn:
        for var, val in conn.execute('select var, val from _variables'):
            setattr(dbVars, var, val)

    if hasattr(dbVars, 'filter_type') and showExtraInfo:
        out.write("#: FILTERED VIEW OF SCOWL DATA:\n")
        out.write(f"#:   {dbVars.filter_type}\n")
        out.write(f"#:   {dbVars.filter_where_clause}\n")
        if hasattr(dbVars, "filter_simplifications"):
            out.write(f"#:   simplifications: {dbVars.filter_simplifications}\n")
        out.write("\n")

    for cluster in clusters:

        for group in cluster.groups:

            first = True
            for line in group.lines:
                try:
                    line.print(out, first, trimSpellings)
                except ValueError as err:
                    _warn(f'skipping line: {line.grp.headword}: {line.poses}: {err}')
                first = False
            for lemma in sorted(group.override.keys()):
                group.override[lemma].print(out)

            if not group._lemmaIncluded:
                l = Line(group, [ScowlInfo(99)])
                l.poses.add(basePosInfo[group.base_pos].lemma_pos)
                l.print(out, False, trimSpellings)

            for c in group.problems:
                out.write(f"#! {c}\n")
            group.commentLines.print(out)
            out.write('\n')

        for c in cluster.comments:
            c.print(out)

        if showClusters:
            out.write('\n')

    if conn and showExtraInfo:
        out.write('#: Part of Speech Codes:\n')
        for pos, descr, extra_info in conn.execute("select base_pos, descr, extra_info from base_poses where base_pos != '' order by order_num"):
            out.write(f"#:   {pos}: {descr}\n")
        out.write("#:\n")
        out.write('#: Part of Speech Classes:\n')
        for pos_class, in conn.execute("select pos_class from pos_classes where pos_class != '' order by pos_class"):
            out.write(f"#:   {pos_class}\n")
        out.write("#:\n")
        out.write('#: Annotations:\n')
        for symbol, descr in conn.execute("select rank_symbol, rank_descr from ranks where rank_symbol != '' order by order_num"):
            out.write(f"#:   {symbol}: {descr}\n")
        out.write('#:   †: ambiguous lemma\n')
        out.write("#:\n")
        out.write('#: Spelling/Region Codes:\n')
        for spelling, region, descr in conn.execute("select spelling, region, spelling_descr from spellings where spelling != '_' order by order_num"):
            out.write(f"#:   {spelling}: {region}: {descr}\n")
        out.write("#:   _:     Other\n")
        out.write('#:\n')
        out.write('#: Variant Levels:\n')
        for symbol, num, descr in conn.execute("select variant_symbol, variant_level, variant_descr from variant_levels where variant_symbol != '' order by variant_level"):
            out.write(f"#:   {symbol}: {num}: {descr}\n")
        out.write('#:\n')
        out.write('#: Usage Notes:\n')
        for usage_note, in conn.execute("select usage_note from usage_notes where usage_note != '' order by usage_note"):
            out.write(f'#:   {usage_note}\n')
        out.write('#:\n')
        out.write('#: Categories:\n')
        for category, in conn.execute("select category from categories where category != ''order by category"):
            out.write(f'#:   {category}\n')
        out.write('#:\n')
        out.write('#: Tags:\n')
        for tag, in conn.execute("select tag from tags where tag != '' order by tag"):
            out.write(f'#:   {tag}\n')

    out.finish()
