use strict;
use warnings;

use varcon;

open F, "varcon.txt" or die;

my %data;

while (<F>) {
    my $line = $_;
    my @words = varcon::get_words($line);
    foreach (@words) {
        push @{$data{$_}}, \@words;
    }
}

while (<>) {
    chomp;
    my @words = sort split /\t/, $_;
    my %tocheck;    
    foreach (@words) {
        foreach (@{$data{$_}}) {
            $tocheck{$_} = $_;
        }
    }
    print ">>@words\n";
    foreach (keys %tocheck) {
        print "@{$tocheck{$_}}\n";
    }
    print "---\n";
}

