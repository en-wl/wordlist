use strict;
use warnings;

my %add_pos;

open F, "macro.80";
while (<F>) {
    chomp;
    next unless /^(.+)\'s/;
    $add_pos{$1} = $_;
}

while (<>) {
    chomp;
    print "$_\n";
    print $add_pos{$_}."\n" if exists $add_pos{$_};
}
