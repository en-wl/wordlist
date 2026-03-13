## Word Sources and Tags

Tags are used to provide information on what source list the word came from.

The source for the majority of words is from lists that Alan Beale has a large
part in creating, which provide a level of consistency.  These lists are then
supplemented by a number of signature lists.  Most of these words are tagged
in `scowl-pre.txt` but removed by `combine.py` to reduce noise.  Select other
tags are also removed in `combine.py`.

All tags by convention are `[like this]`.  Tags that are removed by
`combine.py` are marked in `(as such)` in this documentation for ease of
reference.

Many of the source lists include lemmas or headwords only.  Those have been
expanded to include likely inflections by various means.

### Primary Source Tags

#### (12dicts)

Alan Beale "core" 12dict lists (2of12/6of12), from the Alternate 12 Dicts
Package created specifically for SCOWL, see
https://wordlist.aspell.net/12dicts/.

Size 35 includes lemmas found in at least 11 of the 12 source dictionaries,
size 50 from at least 5 sources, and size 60 from at least 2 sources.

The 12dicts lists are in the Public Domain but the author requests
acknowledgment of their use.

This tag is not included by default in the final database.

#### [ukfreq]

Brian Kelk's "UK English Wordlist with Frequency Classification".

Size 35 includes frequency classes 16-2, size 50 freq class 1, and size 70,
freq class 0, but only if the word would normally be in size 80.  Fixme note
about forms added...

His work is in the Public Domain:

    Date: Sat, 08 Jul 2000 20:27:21 +0100
    From: Brian Kelk <Brian.Kelk@cl.cam.ac.uk>

    > I was wondering what the copyright status of your "UK English
    > Wordlist With Frequency Classification" word list as it seems to
    > be lacking any copyright notice.

    There were many many sources in total, but any text marked
    "copyright" was avoided. Locally-written documentation was one
    source. An earlier version of the list resided in a filespace called
    PUBLIC on the University mainframe, because it was considered public
    domain.

    Date: Tue, 11 Jul 2000 19:31:34 +0100

    > So are you saying your word list is also in the public domain?

    That is the intention.

The quality of these words is questionable and this source may eventually be
removed.

#### (census)

The top 1000 male, female, and last names from the 1990 Census report.
Included at the 50 size level.

This tag is not included by default in the final database.

#### (3esl)

Lemmas from Alan Beale's 3esl list from the 12dicts package.  Included at the
40 size level.

This tag is not included by default in the final database.

#### [brif]

Words from Alan Beale's 2of4brif list found in his 12dicts package.
Included at the 60 size level.

#### [5d+2a]

Lemmas from Alan Beale's 5d+2a list found in his 12dicts package.  Included at
the 70 size level.

#### [3of6]

Words from Alan Beale's 3of6 list found in his 12dicts package.  Included at
the 70 size level.

#### [moby]

Lemmas sourced from the MWords package.  The 70 size level includes lemmas
from the 74,550 common dictionary words from the MWords package.  The 80 size
includes 10,196 places (A large selection of place names in the United States).

The MWords package was explicitly placed in the public domain:

    The Moby lexicon project is complete and has
    been place into the public domain. Use, sell,
    rework, excerpt and use in any way on any platform.

    Placing this material on internal or public servers is
    also encouraged. The compiler is not aware of any
    export restrictions so freely distribute world-wide.

    You can verify the public domain status by contacting

    Grady Ward
    3449 Martha Ct.
    Arcata, CA  95521-4884

    grady@netcom.com
    grady@northcoast.com

#### (enable)

Words from ENABLE2K by M\Cooper <thegrendel@theriver.com> not marked as stale
by the supplement file.

ENABLE2K is in the public domain:

    The ENABLE master word list, WORD.LST, is herewith formally released
    into the Public Domain. Anyone is free to use it or distribute it in
    any manner they see fit. No fee or registration is required for its
    use nor are "contributions" solicited (if you feel you absolutely
    must contribute something for your own peace of mind, the authors of
    the ENABLE list ask that you make a donation on their behalf to your
    favorite charity). This word list is our gift to the Scrabble
    community, as an alternate to "official" word lists. Game designers
    may feel free to incorporate the WORD.LST into their games. Please
    mention the source and credit us as originators of the list. Note
    that if you, as a game designer, use the WORD.LST in your product,
    you may still copyright and protect your product, but you may *not*
    legally copyright or in any way restrict redistribution of the
    WORD.LST portion of your product. This *may* under law restrict your
    rights to restrict your users' rights, but that is only fair.

This tag is not included by default in the final database.

#### (nopos), (2dicts), (ospdadd)

Additional words from the ENABLE2K supplement files.

Words found in _nopos_ (words with no part of speech) are added at 35 size level.

Words found in _2dicts_ (words confirmed by 2 dictionaries) and _ospdadd_
(additional OSPD(r) words) are added at the 80 level.

These tags are not included by default in the final database.

#### [lcacr], [ucacr], [upper]

Additional words from the ENABLE2K supplement files.  These are all included at
the 80 size level.  The lists are:

  * _lcacr_: lower-case acronyms
  * _ucacr_: upper-case acronyms
  * _upper_: upper-case words (not proper names)

#### [plurals]

Additional plurals from the ENABLE2K supplement files.  Included at the 85
size level.

#### [stale]

Stale OSPD words from the ENABLE2K supplement files.  These words have been
removed from the main ENABLE list and are instead included at the 85 size
level.

#### [ukacd]

Words from the "UK Advanced Cryptics Dictionary" by J Ross Beresford.
Included at the 85 size level.

The "UK Advanced Cryptics Dictionary" is under the following copyright:

    Copyright (c) J Ross Beresford 1993-1999. All Rights Reserved.

    The following restriction is placed on the use of this publication:
    if The UK Advanced Cryptics Dictionary is used in a software package
    or redistributed in any form, the copyright notice must be
    prominently displayed and the text of this document must be included
    verbatim.

    There are no other restrictions: I would like to see the list
    distributed as widely as possible.

### Additional Tags

#### [extra]

Extra words, often suggested by others, not from any particular source.

#### [+]

Signature words and neologisms.  The choice between `[extra]` and `[+]` can be
somewhat arbitrary.

#### [-]

A special tag when a word was bumped up to a higher size level due to typo or
other concerns.

#### [cs]

The ___cs___ lists from `r/special` in SCOWLv1 that include common words found in
software development and computer science contexts.

#### [name]

Proper names, currently from two lists from `r/special` in SCOWLv1.

  * __names.from_alan_beale__: A list of names (version 5.2) sent to me by Alan Beale:
    > I have a large list of proper names, whose origins are in the
    > linux-words proper names, but which both removes a lot of (what I
    > considered to be) junk entries, and adds a lot of names of various
    > sorts, notably names of commercial products and noteworthy
    >  historical personages.
  * __proper-names__: A list of additional proper names.

#### [town]

Populated places included at various levels, currently from three lists from
`r/special` in SCOWLv1.

  * __urban-areas__ _(region US)_: U.S Urban areas as defined by the U.S. Census Bureau.
    Source <https://www2.census.gov/geo/docs/reference/ua/ua_list_ua.txt> (2019-08).
  * __australian-towns__ _(region AU)_: List of cities in Australia from
    <https://en.wikipedia.org/wiki/List_of_cities_in_Australia_by_population>
    (2019-09-24).
  * __chinese-names__: A list of Chinese places from <https://github.com/en-wl/wordlist/issues/203>.

#### [coca]

Hand-chosen, high-frequency lemmas found in the Corpus of Contemporary
American English (COCA).  This data comes from frequency lists generated from
3-gram data purchased in 2011 and is within the terms of the NDA signed.
<https://www.english-corpora.org/coca/>.

#### [coca-llm]

Lemmas found in the Corpus of Contemporary American English (COCA).  These
words come from the same frequency lists as those with the `[coca]` tag.
However, all lemmas with a frequency of at least 0.05 words per million (wpm)
were considered with the help of LLMs.

More specifically, several LLMs were asked to evaluate the lemmas using a
prompt similar to the one used to evaluate GitHub issues.  Lemmas were
considered if a majority of the LLMs agreed that the lemma belonged in the 60
size level.  Of those considered, lemmas already present in SCOWL at the 70
level were promoted after applying additional filters.  Lemmas from the 80
level were also promoted to the 60 level if the frequency was around 0.1 wpm.
The rest were manually reviewed for addition.

Note that the frequency count is the combined frequency for all possible
inflections of the lemma for a given part-of-speech.

## Other sources

### VarCon

Variant information originally comes from VarCon.  VarCon was originally
maintained as a separate project, but is now part of SCOWL.  VarCon was under
the following copyright:

    Copyright 2000-2016 by Kevin Atkinson

    Permission to use, copy, modify, distribute and sell this array, the
    associated software, and its documentation for any purpose is hereby
    granted without fee, provided that the above copyright notice appears
    in all copies and that both that copyright notice and this permission
    notice appear in supporting documentation. Kevin Atkinson makes no
    representations about the suitability of this array for any
    purpose. It is provided "as is" without express or implied warranty.

    Copyright 2016 by Benjamin Titze

    Permission to use, copy, modify, distribute and sell this array, the
    associated software, and its documentation for any purpose is hereby
    granted without fee, provided that the above copyright notice appears
    in all copies and that both that copyright notice and this permission
    notice appear in supporting documentation. Benjamin Titze makes no
    representations about the suitability of this array for any
    purpose. It is provided "as is" without express or implied warranty.

    Since the original words lists come from the Ispell distribution:

    Copyright 1993, Geoff Kuenning, Granada Hills, CA
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    1. Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.
    3. All modifications to the source code must be clearly marked as
       such.  Binary redistributions based on modified source code
       must be clearly marked as modified versions in the documentation
       and/or other materials provided with the distribution.
    (clause 4 removed with permission from Geoff Kuenning)
    5. The name of Geoff Kuenning may not be used to endorse or promote
       products derived from this software without specific prior
       written permission.

    THIS SOFTWARE IS PROVIDED BY GEOFF KUENNING AND CONTRIBUTORS ``AS IS'' AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED.  IN NO EVENT SHALL GEOFF KUENNING OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
    OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
    OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
    SUCH DAMAGE.

### WordNet

The WordNet database was used to help with POS assignment.  It is under the
following copyright:

    This software and database is being provided to you, the LICENSEE,
    by Princeton University under the following license.  By obtaining,
    using and/or copying this software and database, you agree that you
    have read, understood, and will comply with these terms and
    conditions.:

    Permission to use, copy, modify and distribute this software and
    database and its documentation for any purpose and without fee or
    royalty is hereby granted, provided that you agree to comply with
    the following copyright notice and statements, including the
    disclaimer, and that the same appear on ALL copies of the software,
    database and documentation, including modifications that you make
    for internal use or for distribution.

    WordNet 1.6 Copyright 1997 by Princeton University.  All rights
    reserved.

    THIS SOFTWARE AND DATABASE IS PROVIDED "AS IS" AND PRINCETON
    UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
    IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PRINCETON
    UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES OF MERCHANT-
    ABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE
    LICENSED SOFTWARE, DATABASE OR DOCUMENTATION WILL NOT INFRINGE ANY
    THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.

    The name of Princeton University or Princeton may not be used in
    advertising or publicity pertaining to distribution of the software
    and/or database.  Title to copyright in this software, database and
    any associated documentation shall at all times remain with
    Princeton University and LICENSEE agrees to preserve same.

### COCA

Data from the Corpus of Contemporary American English (COCA) was used in
various ways beyond simply adding new words.  All usage is within the 
terms of the NDA.  <https://www.english-corpora.org/coca/>.
