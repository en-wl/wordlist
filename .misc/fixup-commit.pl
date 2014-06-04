#!/usr/bin/perl

my %bug_map = qw(3378332 50
                 3025072 37
                 2749732 23
                 3576342 57
                 3012183 36
                 3067528 41
                 2444247 18
                 1882591 10
                 1840667 8
                 );




$/ = undef;
$_ = <>;

s~[ \n]+git-svn-id: .+/trunk\@(\d+) [^\n]+~~;
my $rev = $1;

open F, ">>/tmp/possibe-bugs";
my %bugs;
my @bugs;
while (m~(\d\d\d\d\d+)~g) {
    next unless exists $bug_map{$1};
    next if exists $bugs{$1};
    push @bugs, $1;
    $bugs{$1} = 1;
}

$_.="\n[svn rev $rev]\n";

if (@bugs) {
    $_ .= "\nNOTE: ".join(' ', (map {"Issue $_ now \#$bug_map{$_}. "} @bugs))."\n";
}

print;


