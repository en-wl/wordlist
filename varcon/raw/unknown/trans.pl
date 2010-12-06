use strict;
use warnings;

open F, "abbc.tab" or die;

while (<F>) {
    my ($a,$b,$z,$c,$s) = /(\S+)\t(\S+)\t(\S+)\t(\S+)\t(\S*)\n/ 
	or die "BadLine: $_";
    my $note;
    if ($s eq '!') {
        $note = '!';
        $s = '';
    } elsif ($s eq 'V?') {
        $note = '?';
        $s = 'V';
    }
    if ($s ne '') {
        die "?$_" unless $b eq $z;
        print STDERR "?$_" unless $b eq $c;
    }
    #print unless $s eq '';
    my %v;
    my @w = ($a, $b, $z, $c);
    push @{$v{$a}}, 'A';
    push @{$v{$b}}, 'A' if $s eq 'B';
    push @{$v{$a}}, 'B' if $s eq 'A' || $s =~ /^V/;
    push @{$v{$a}}, 'Bv?' if $s eq 'a';
    push @{$v{$b}}, 'B' unless $s =~ /^V/;
    push @{$v{$b}}, 'Bv' if $s eq 'V';
    push @{$v{$b}}, 'B-' if $s eq 'VV';
    push @{$v{$a}}, 'Bv' if $s eq 'v';
    push @{$v{$z}}, 'Z' unless $z eq $b;
    push @{$v{$c}}, 'C' unless $c eq $b || $c eq $z;
    my @r;
    foreach (@w) {
        next unless defined $v{$_};
        push @r, join(' ', @{$v{$_}}).": ".$_;
        undef $v{$_};
    }
    push @r, $note if defined $note;
    print join(' / ', @r), "\n";
}
