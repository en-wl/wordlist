#!/usr/bin/perl

open F, "abbc.tab";

open A, ">american.lst.tmp";
open B, ">british.lst.tmp";
open Z, ">british_z.lst.tmp";
open V, ">british_variant.lst.tmp";
open C, ">canadian.lst.tmp";
open c, ">common.lst.tmp";

#my %variant_level = ('VV' => 3, 'V' => 2, 'V?' => 1, 'v' => 1);
my %variant_dir   = ('VV' => 'a', 'V' => 'a', 'V?' => 'a', 'v' => 'b');

die "Usage: $0\n" if (@ARGV > 0);

while (<F>) {
    ($a,$b,$z,$c,$s) = /(\S+)\t(\S+)\t(\S+)\t(\S+)\t(\S*)\n/ 
	or die "BadLine: $_";
    if ($s =~ /^(VV|V|V\?|v)$/) {
        die unless $b eq $z;
        if ($variant_dir{$s} eq 'a') {
            print V "$b\n";
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
        die "$b != $z" unless $b eq $z;
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
