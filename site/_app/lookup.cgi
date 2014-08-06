#!/usr/bin/perl -T

use CGI;
use strict;
use warnings;
use utf8;

use lib '/opt/app/wordlist/scowl/sql';
use speller_lookup qw(lookup to_html);

my $q = CGI->new;
my $dict= defined $q->param('dict') ? $q->param('dict') : 'en_US';
my $words= defined $q->param('words') ? $q->param('words') : '';
utf8::upgrade($words);

my $res;
if ($words ne '') {
    $res = lookup("/opt/app/wordlist/scowl/scowl.db",$dict,split /\n/,$words);
}

print $q->header();

my $dicts = '';
foreach my $d (qw(en_US en_GB-ise en_GB-ize en_CA en_US-large en_GB-large en_CA-large)) {
    my $sel = $d eq $dict ? " selected" : "";
    $dicts .= "<option value=\"$d\" $sel>$d</option>\n";
}

print <<"---";
<html>
<head>
<title>English Speller Word Lookup</title>
</head>
<body>
<p>
Use this utility to look up words in <a href="http://wordlist.aspell.net/">SCOWL</a>.
</p>
---
to_html($res) if defined $res;
print <<"---";
<form>
<select name="dict">
$dicts
</select>
<br>
Enter one word per line, entries are case sensitive:
<br>
<textarea rows="10" cols="20" name="words">
$words
</textarea>
<br>
<button type="submit">Submit</button>
<button type="reset">Reset</button>
</form>
</body>
---





