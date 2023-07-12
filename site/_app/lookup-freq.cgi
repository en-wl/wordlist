#!/usr/bin/perl -T

use CGI qw(escapeHTML);
use strict;
use warnings;
use utf8;
use IPC::Open2;
use IO::Handle;

delete @ENV{qw(IFS CDPATH ENV BASH_ENV)};
$ENV{PATH} = "/usr/local/bin:/bin:/usr/bin";

my $q = CGI->new;

my $parm  = defined $q->param('parm') && $q->param('parm') eq 'full' ? 'full' : 'normal';
my $words = defined $q->param('words') ? $q->param('words') : '';
my $also = defined $q->param('also') && $q->param('also') =~ /^(similar|original|neither)$/ ? $1 : 'similar';
my $similar_checked = $also eq 'similar' ? 'checked' : '';
my $original_checked = $also eq 'original' ? 'checked' : '';
my $neither_checked = $also eq 'neither' ? 'checked' : '';

my $pid;
if ($words ne '') {
    chdir '/opt/ngrams-lookup';
    $pid = open2(\*RDR,\*WTR,'./lookup', $parm, $also);
    binmode(RDR, ":utf8");
    binmode(WTR, ":utf8");
    foreach (split /\n/,$words) {
	my ($word) = /^[ \r\n]*(.*?)[ \r\n]*$/;
	next if $word eq '';
	print WTR "$word\n";
    }
    close(WTR);
}


my $url = $q->url(-query=>1);
my $link = $words ne '' && length $url < 2000 ? qq'<p><small><i><a href="$url">Shareable Link</a></i></small></p>' : '';

print $q->header();

print <<"---";
<html>
<head>
<title>Google Books Freq Lookup</title>
</head>
<body>
<p>

Use this tool to determine if a word should be added to <a href="http://wordlist.aspell.net/">SCOWL</a> based
on the frequency in the <a
href="https://books.google.com/ngrams">Google Book's corpus</a> (1980-2008).

</p>
<pre>
---
if ($words ne '') {
    while (<RDR>) {
	print escapeHTML($_);
    }
}
print "</pre>\n";
print "$link\n" if $link ne '';
my $orig_extra = $parm eq 'normal' ? <<'---'
For reference the original words found in the corpus are shown after
the representative version along with its relative frequency.
---
: <<'---';
<i>[Note: To see the original words found in the corpus unclick
"Show Similar Words" and resubmit the form.]</i>
---
my $similar_extra = $parm eq 'normal-similar' ? <<'---'
<p>
For reference similar words are shown after the main word provided
that they have a frequency greater than 0.5 times the main word.  Less
common words that are very similar to more common words are less
likely to be accepted in a speller dictionary as they can easily 
mask an incorrect spelling of the more common word.
---
: <<'---';
<p>
The acceptance of less common words in a speller dictionary can also
depend on if they are any similar words that can mask an incorrect
spelling of the more common word.  To see a list of these words click
on "Show Similar Words" and resubmit the form.
---
my $normal_footer = <<"---";
<p>
These stats are based on the counts from the 1-grams in <a
href="http://storage.googleapis.com/books/ngrams/books/datasetsv2.html">Google's
Books Ngram dataset</a> for books between 1980 and 2008.  The
frequency count is without regard to case or dialect marks and does
not include words with non-alphabetic characters.  The word shown in
this report is the best guess at the correct form of the word.
$orig_extra
<p>
The frequency count is adjusted
to give more weight to newer words.  It is defined as the normal
frequency times the newness score when the latter is greater than 1.
(When the newness score is less than 1 no adjustment is made).  The
Newness score is defined as the frequency the word appears between the
5Hyears 2006 and 2008 divided by the frequency the word appears between
1980 and 2008.
<p>
The "should incl" score indicates if a word should or should not be
considered for inclusion in the given dictionary based on the
frequency of the word in the corpus.  A word that is already included
is labeled as "incl.".  A word with 5 stars should most likely be
included unless there is a good reason not to.  A word with 3 stars
(***) is still worth considering and a word with 1 star (*) should
most likely not be considered.
$similar_extra
<p>
A partial version of the complete list is also available to download
at the bottom of this page.  It includes all words found in the corpus
with a "should incl" score of 3 stars or more for the large
dictionary.  A version that only includes words not already in the
normal size dictionary is also available.  Additional reports can
fairly easily be generated.  Please email me at kevina\@gnu.org if
interested.
</p>
---
if ($parm=~/^normal/ and  $words ne '') {print $normal_footer}
print <<"---";
<form action="$ENV{SCRIPT_NAME}" method="post">
Enter one word per line
<br>
<textarea rows="10" cols="20" name="words">$words</textarea>
<br>
Also Report: 
<label for="similar"><input id="similar" type="radio" name="also" value="similar" $similar_checked>Similar Words</label>
<label for="original"><input id="original" type="radio" name="also" value="original" $original_checked>Original Words</label>
<label for="neither"><input id="neither" type="radio" name="also" value="neither" $neither_checked>Neither</label><br>
<button type="submit" name="parm" value="normal">Normal Report</button>
<button type="submit" name="parm" value="full">Detailed Report</button><br>
<button type="reset">Reset</button>
</form>
---
print qq'<a href="$ENV{SCRIPT_NAME}">Start Over</a>' if defined $words ne '';
print <<"---";
<p>
<a href="d/scowl-googlebooks-report-strong.txt">Full List (strong candidates)</a><br>
<a href="d/scowl-googlebooks-report.zip">Full List (3 - 5 star words)</a><br>
<a href="d/scowl-googlebooks-report-wo-incl.zip">Full List (3 - 5 star words, not already in normal dictionary)</a>
</p>

</body>
---

close(RDR);
waitpid $pid, 0 if defined $pid;
