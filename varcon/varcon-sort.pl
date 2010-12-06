#!/usr/bin/perl

use strict;
use warnings;

use varcon;

my %data;

my $infile;
my $outfile;
my $rename = 0;

if (@ARGV == 1) {
    $infile = $ARGV[0];
    $outfile = "$ARGV[0].new";
    $rename = 1;
} elsif (@ARGV == 2) {
    $infile = $ARGV[0];
    $outfile = $ARGV[0];
} else {
    $infile = "/dev/stdin";
    $outfile = "/dev/stdout";
}

open F, $infile or die;

while (<F>) {
    my $line = $_;
    my %d = varcon::readline($line);
    push @{$data{"$d{'A'}[0][0]"}}, $line if     exists $d{A};
    push @{$data{"$d{'_'}[0][0]"}}, $line unless exists $d{A};
}

open F, ">$outfile" or die;

foreach my $key (sort keys %data) {
    foreach (@{$data{$key}}) {
        print F $_;
    }
}

if ($rename) {
    unlink $infile;
    rename $outfile, $infile;
}
