#!/usr/bin/perl

open F, "abbc.tab";

open A, ">american.lst.tmp";
open B, ">british.lst.tmp";
open Z, ">british_z.lst.tmp";
open V, ">british_variant.lst.tmp";
open C, ">canadian.lst.tmp";
open c, ">common.lst.tmp";

my %VARIANT_MAP = ('VV' => 3, 'V' => 2, 'V?' => 1, 'v' => 0);

my $variant_level = 1;

if (@ARGV >= 1) {
    $variant_level = $VARIANT_MAP{$ARGV[0]};
}

if (!defined $variant_level || @ARGV > 1) {
    die "Usage: $0 VV|V|V?|v\n";
}

while (<F>) {
    ($a,$b,$z,$c,$s) = /(\S+)\t(\S+)\t(\S+)\t(\S+)\t(\S*)\n/ 
	or die "BadLine: $_";
    if ($s =~ /^(VV|V|V\?|v)$/) {
        die unless $b eq $z;
        if ($variant_level{$s} >= $variant_level) {
            $c = $a if $c eq $b;
            $b = $a;
            $z = $a;
        } else {
            print V "$a\n";
        }
        $s = '';
    }
    if ($s =~ /^!?$/) {
	print A "$a\n";
	print B "$b\n";
	print Z "$z\n";
	print C "$c\n";
    } else {
        die unless $b eq $z;
	print c "$a\n$b\n$c\n";
	if ($s eq 'A' || $s eq 'a') {
	    $al = "$a\n";
	    $bl = "$a\n$b\n";
	} elsif ($s eq 'B') {
	    $al = "$a\n$b\n";
	    $bl = "$b\n";
        } else {
            die "Unknown flag: $s\n";
        }
	print A $al;
	print B $bl;
	print Z $bl;
	if ($c eq $a) {
	    print C $al;
	} elsif ($c eq $b) {
	    print C $bl;
	} else {
	    die "$a $b $c";
	}
    }
}
