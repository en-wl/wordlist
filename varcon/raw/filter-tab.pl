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

sub subset($$) {
    my ($a, $b) = @_;
    foreach my $w (@$a) {
        return 0 unless grep {$_ = $w} @$b;
    }
    return 1;
}

# return true if there exists an entry in data
# which contains all of the words
sub exists_all_in(@) {
    foreach (@_) {
        foreach (@{$data{$_}}) {
            return 1 if subset \@_, $_, 
        }
    }
}

while (<>) {
    chomp;
    my @words = sort split /\t/, $_;
    if (exists_all_in @words) {
        #print "WILL SKIP: @words\n";
    } else {
        print "$_\n";
    }
}

