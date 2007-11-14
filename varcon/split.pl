#!/usr/bin/perl

open F, "abbc.tab";

open A, ">american.lst.tmp";
open B, ">british.lst.tmp";
open Z, ">british_z.lst.tmp";
open C, ">canadian.lst.tmp";
open c, ">common.lst.tmp";

while (<F>) {
    ($a,$b,$z,$c,$s) = /(\S+)\t(\S+)\t(\S+)\t(\S+)\t(\S*)\n/ 
	or die "BadLine: $_";
    if ($s eq "") {
	print A "$a\n";
	print B "$b\n";
	print Z "$z\n";
	print C "$c\n";
    } else {
        die unless $b eq $z;
	print c "$a\n$b\n$c\n";
	if ($s eq 'A') {
	    $al = "$a\n";
	    $bl = "$a\n$b\n";
	} elsif ($s eq 'B') {
	    $al = "$a\n$b\n";
	    $bl = "$b\n";
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
