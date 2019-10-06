#!/usr/bin/perl -T

use CGI qw(escapeHTML);
use strict;
use warnings;
use utf8;
use IPC::Open2;
use IO::Handle;

use lib '/opt/app/wordlist/scowl/sql';
use speller_lookup qw(lookup to_html);

delete @ENV{qw(IFS CDPATH ENV BASH_ENV)};
$ENV{PATH} = "/usr/local/bin:/bin:/usr/bin";

my $q = CGI->new;
my $dict= defined $q->param('dict') ? $q->param('dict') : 'en_US';
my $words= defined $q->param('words') ? $q->param('words') : '';
utf8::upgrade($words);

my $res;
my $url = $q->url(-query=>1);
if ($words ne '') {
   my @words = split /[\r\n]+/,$words;
   if (@words <= 12 && length $url < 2000 && $q->request_method() eq 'POST') {
       print $q->redirect($url);
       exit 0;
   }
   $res = lookup("/opt/app/wordlist/scowl/scowl.db",$dict,split /[\r\n]+/,$words);
   eval {
    chdir '/opt/ngrams-lookup';
    my $pid = open2(\*RDR,\*WTR,'./lookup', 'brief');
    foreach my $row (@{$res->{table}}) {
	next if $row->[3] =~ /case changed/;
	print WTR "$row->[0]\n";
	my $line = <RDR>;
	die "readline failed: $!" unless defined $line;
	my ($lower,$freq,$newness,$normal,$large) = split / *\| */, $line;
	push @$row, "&nbsp;".($dict =~ /-large$/ ? $large : $normal);
	push @$row, ['align="right"',"$freq&nbsp;"];
	push @$row, ['align="right"',"$newness&nbsp;"];
    }
    close(WTR);
    close(RDR);
    waitpid $pid, 0
  };
  warn $@ if $@;
}

print $q->header();

my $dicts = '';
foreach my $d (qw(en_US en_GB-ise en_GB-ize en_CA en_AU en_US-large en_GB-large en_CA-large en_AU-large)) {
    my $sel = $d eq $dict ? " selected" : "";
    $dicts .= "<option value=\"$d\" $sel>$d</option>\n";
}

chdir '/opt/app/wordlist';
my $git_ver = `git log --pretty=format:'%cd [%h]' -n 1`;

my $words_url = CGI::escape($words);
my $freq_link = length $words_url < 8000 ? "lookup-freq?words=$words_url" : "lookup-freq";
my $words_html = escapeHTML($words);

my $header = $res ? '' : 'Use this utility to look up words in <a href="http://wordlist.aspell.net/">SCOWL</a>.';

print <<"---";
<html>
<head>
<title>English Speller Word Lookup</title>
</head>
<body>
<p>
$header
</p>
---
if (defined $res) {
    my $link = $words ne '' && length $url < 2000 && $q->request_method() eq 'POST' ? qq'<p><small><i><a href="$url">Shareable Link</a></i></small></p>' : '';
    to_html($res,sub {
	s~<th>~<th rowspan=2>~g;
	s~(</tr>)~<th colspan=3>Google Books Stats [*]</tr>~;
	$_ .= qq'<tr><th>Should<br>Include<th>Frequency<br>(per million)<th>Newness</th>\n';});
    print <<"---";

[*] The "Google Book Stats" are stats based on the counts from the
1-grams in <a
href="http://storage.googleapis.com/books/ngrams/books/datasetsv2.html">Google's
Books Ngram dataset</a> for books between 1980 and 2008.  The
frequency count is without regard to case or dialect marks and does
not include words with non-alphabetic characters.  The newness figure
is a rough approximation of how new a word is, the larger the number
the newer the word.  The "Should Include" score indicates if a word
should or should not be considered for inclusion in the dictionary
based on the frequency of the word in the corpus (1980-2008).  A word
with 5 stars (*****), that is not already in the dictionary, should
most likely be included unless there is a good reason not to.  A word
with 3 stars (***) is still worth considering and a word with 1 star
(*) should most likely not be considered.  A report sorted by
frequency is <a href="$freq_link">also
available</a>.
$link
<hr>
---
}
print <<"---";
<form action="$ENV{SCRIPT_NAME}" method="post">
<select name="dict">
$dicts
</select>
<br>
Enter one word per line, entries are case sensitive:
<br>
<textarea rows="10" cols="20" name="words">$words_html</textarea>
<br>
<button type="submit">Lookup</button>
<button type="reset">Reset</button>
</form>
---
print qq'<a href="$ENV{SCRIPT_NAME}">Start Over</a>' if defined $res;
print <<"---";
<pre>
$git_ver
</pre>
</body>
---
