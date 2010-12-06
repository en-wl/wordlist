#
# This lovely script tries to derive variant information from several
# sources, the biggest source is variant-plus.txt. 
#
# Basically it takes the variant info in variant-plus.txt, adjusts the
# variant levels based on info in 2of12full.txt and them merges the
# info in varcon.txt, and performs all sorts of sanity checks.
#
# It is kind of hackish and as such requires 95 of varcon to run.
# It will need some adjusting to run on the new varcon.txt
#

use Data::Dumper;

$Data::Dumper::Indent = 0;
$Data::Dumper::Terse = 1;

use strict;
#use warnings;
use sort 'stable';

use varcon;


#
# config vars
#
my $print_extra = 0;
my $varcon_output = 1;

open F, "../alt12dicts/variant.txt" or die;

my %var;
while (<F>) {
    chop;
    my ($v, $w) = split /\t/;
    $var{$v} = "$v $w";
}

open F, "../alt12dicts/2of12full.txt" or die;

my %full;
while (<F>) {
    chop;
    my ($t,$n,$v,$b,$w) = /\s*(\d+):\s+(\d+|-)\s+(\d+|-)\#\s+(\d+|-)\&\s+(.+)/ or die "?$_";
    next if ($b > $n);
    $full{$w} = [$t, $n, $v, $b];
}

my %varcon;
my @varcon;
open F, "varcon.txt";
while (<F>) {
    my $line = $_;
    push @varcon, $line;
    foreach (varcon::get_words($line)) {
        push @{$varcon{$_}}, [$line, $#varcon];
    }
}

open F, "variant-plus.txt" or die;

#while (<F>) {
#    last if /^---/;
#}

sub proc ($) {
    local $_ = $_[0];
    chomp;
    my ($note, $data, $flag, $info) = /^(b:|\?|-b |-|)\s*(\w.+?)\s*(\*?)\s*(\|.*)?$/ or die "?$_";
    die "!$info" if $info =~ /\*\s*/;
    my $node;
    ($note) = $info =~ m/^\|\s*(.+)/ if $info;
    local $_ = $data;
    my @v;
    s/^(\w\S+)\s*// or die "?$_";    push @v, [$1, [0,1, 0]];
    while (s/^\/0\s*(\w\S+)\s*//)   {push @v, [$1, [0,1, 0]]}
    while (s/^\/\s*(\w\S+)\s*//)    {push @v, [$1, [0,1, 1]]}
    while (s/^\((\w\S+)\)\s*//)     {push @v, [$1, [1,2, 2]]}
    while (s/^\(\((\w\S+)\)\)\s*//) {push @v, [$1, [3,3, 3]]}
    die "?$_" unless $_ eq '';
    return (\@v, $note, $flag);
}

sub yank(\@$) {
    my ($a,$w) = @_;
    my $l = @$a;
    my $i;
    for ($i = 0; $i < @$a; $i++) {
        last if $a->[$i][0] eq $w;
    }
    die "Not found: $w" if $i == @$a;
    return splice @$a,$i,1;
}

sub min($$) {
    return $_[0] < $_[1] ? $_[0] : $_[1];
}

sub merge($$) {
    @_ = sort {$a->[0] <=> $b->[0]} @_;
    my ($a0,$b0,$p0) = @{$_[0]};
    my ($a1,$b1,$p1) = @{$_[1]};
    my $p = 9;
    $p = $p0 if (defined $p0 && !defined $p1);
    $p = $p1 if (defined $p1 && !defined $p0);
    die "No Intersection [$a0,$b0]i[$a1,$b1]!\n" if $b0 < $a1;
    my $a = $a1;
    my $b = min($b0, $b1);
    my $r;
    $r = $a if $a == $b;
    $r = $p if $a != $b && $a <= $p && $p <= $b;
    die "More Than One [$a0,$b0]i[$a1,$b1]p$p = [$a,$b]!\n" unless defined $r;
    return $r;
}

sub find_affix($$;$) {
    my ($w,$root,$hint) = @_;
    my $i = 0;
    if (defined $hint && substr($w, -length($hint)) eq $hint) {
        $i = length($w) - length($hint);
    } else {
        while (substr($w, 0, $i) eq substr($root, 0, $i) && $i < length($w)) {$i++}
        $i--;
    }
    my $common = substr($w, 0, $i);
    my $suffix = substr($w, $i);
    my $orig_suffix = $suffix;
    my $extra =  substr($root, $i);
    #print "--== ($w,$root) => $common/$suffix /$extra\n";
    if ($common eq '') {
        return (undef);
    } elsif ($extra eq '' && $suffix eq 'es' && $common =~ /[sxzh]$/) {
        my ($l) = $common =~ /(.)$/;
        return ('s', "$l$extra", "$l$orig_suffix");
    } elsif ($extra eq '' ) {
        my ($l) = $common =~ /(..)$/;
        return ($suffix, "$l$extra", "$l$orig_suffix");
    } elsif (($extra eq 'y' || $extra eq 'ey') && $suffix =~ /^i/) {
        my ($l) = $common =~ /(..)$/;
        $suffix =~ s/^i//;
        return ($suffix, "$l$extra", "$l$orig_suffix");
    } elsif ($extra eq 'e' && $suffix =~ /^[aeiouy]/) {
        my ($l) = $common =~ /(..)$/;
        return ($suffix, "$l$extra", "$l$orig_suffix");
    } else {
        #print "---- $common/$suffix /$extra\n" if $extra;
        return (undef);
    }
}

sub num_syllables($) {
    local ($_) = @_;
    return 1 if length($_) <= 3;
    s/(es|ed|e)$//;
    my @res = m/([aeiouy]+)/gi;
    return @res + 0;
}

sub apply_affix($$;$$) {
    my ($w, $suffix, $strip, $add) = @_;
    if (defined $strip && defined $add && $w =~ s/$strip$/$add/) {
        return $w;
    } elsif ($w =~ m/[^aeiou]y$/ && $suffix !~ m/^i\'/) {
        $w =~ s/y$/i$suffix/;
        return $w;
    } elsif ($w =~ m/e$/ && $suffix !~ m/^[aeiou]/i) {
        return "$w$suffix";
    } elsif ($w =~ m/[sxzh]$/ && $suffix eq 's') {
        return "${w}es";
    } elsif ($w !~ m/[ey]$/i && $suffix !~ m/^[aeiou]/i) {
        return "$w$suffix";
    } elsif ($w !~ m/[ey]$/i && num_syllables($w) > 1) {
        return "$w$suffix";
    } else {
        return undef;
    }
}

sub push_nodup(\@@) {
    my $res = shift;
    foreach (@_) {
        next if grep {$_ eq $_} @$res;
        push @$res, $_;
    }
}

sub read_varcon($;\@) {
    my ($line,$n) = @_;
    my %r = varcon::readline_no_expand($line,@$n);
    foreach my $k (keys %r) {
        my @r;
        foreach my $v (0..3) {
            next unless defined $r{$k}[$v];
            foreach my $v0 (@{$r{$k}[$v]}) {
                push @r, [$v0, $v];
            }
        }
        $r{$k} = [@r];
    }
    return %r;
}


my @clusters;

my $i = 0;

my %tally;

while (<F>) {
    #print;
    if (m/^\s+$/) {$i++; next;}
    my $d = {'line' => $_};
    push @{$clusters[$i]}, $d;
    if (/^=== (\w+) noun/) {
        my $w = $1;
        my @r;
        foreach my $s ("s", "'s") {
            my $r = apply_affix($w, $s);
            last unless defined $r;
            #print "$w $s $r\n";
            push @r, $r;
        }
        if (@r == 2) {
            push @{$clusters[$i]}, {'line' => "=== $r[0] n\n"};
            push @{$clusters[$i]}, {'line' => "=== $r[1] n\n"};
        }
    }
    next if m/^\w+:/;
    next if m/^\s*$/;
    next unless m/^\w/;
    next if m/\/\//; #FIXME split...
    my ($v, $note, $flag) = proc $_;
    my @v = @$v;
    foreach (@v) {
        $tally{$_->[0]}++;
        push_nodup @{$d->{varcon}}, @{$varcon{$_->[0]}} if exists $varcon{$_->[0]};
    }
    $d->{orig} = [@v];
    #print "--- $note :: $d->{line}";
    my @notes = split /\s*\|\s*/, $note;
    $d->{orig_note} = $note if $note ne '';
    if ($varcon_output) {
        @notes = grep !/^[?!]/, @notes;
    }
    @{$d->{notes}} = @notes if @notes;
    $d->{ignore_full} = 1 if $flag eq '*';
    #print "\n";
    #print join(' / ',map {'A'.$_->[0].": ".($var{$_->[1]} ? $var{$_->[1]} : $_->[1])} @v);
}

#outer:

# if the same word is listed as different variant levels in the same
# cluster ignore 2of12full
foreach my $cluster (@clusters) {
    my %tally;
    foreach my $d (@$cluster) {     
        next unless $d->{orig};
        my @v = @{$d->{orig}};
        foreach (@v) {
            push @{$tally{$_->[0]}{$_->[1][2]}}, $d; 
        }
    }
    my $ignored_full = 0;
    foreach my $k (keys %tally) {
        my @d = values %{$tally{$k}};
        next unless @d > 1;
        @d = map @$_, @d;
        foreach my $d (@d) {
            $ignored_full = 1;
            $d->{ignore_full} = 1;
        }
    }
    # to avoid inconsistencies force the variant level found in
    # variant-plus ...
    if ($ignored_full) {
        foreach my $d (@$cluster) {     
            next unless $d->{orig};
            my @v = @{$d->{orig}};
            foreach (@v) {
                die unless defined $_->[1][2];
                $_->[1][0] = $_->[1][1] = $_->[1][2];
            }
        }
    }
}


foreach my $cluster (@clusters) {foreach my $d (@$cluster) {
    next unless $d->{orig};
    next if $d->{ignore_full};
    my @v = @{$d->{orig}};
    foreach (@v) {
        # FIXME: Why?
        #if ($tally{$_->[0]} > 1) {
        #    print "XXX $_->[0] @{$_->[1]}\n";
        #    $_->[1] = [$_->[1][2],$_->[1][2],$_->[1][2]];
        #}
    }
    my @v1;
    my $max = 0;
    foreach (@v) {
        my ($w, $l) = @$_;
        my $d = $full{$w};
        #next outer if !$d && $l->[2] < 3;
        $d = [0,0] if !$d;
        $max = $d->[0] if $d->[0] > $max;
        push @v1, [$w, $d->[1]];
    }
    next if $max == 0;
    #print ">1>", Dumper(\@v1), "\n";
    next if @v1 <= 0;
    # @v1 now contains [<word>, <non-variant count>]
    @v1 = map {[$_->[0], (($_->[1]-($max-$_->[1]))/$max)]} @v1;
    # @v1 now contains [<word>, <variant ratio/rank>]
    #   variant ratio is between 1 to -1 with 1 meaning that all
    #   sources considered the word a non-variant, and -1 meaning
    #   that all sources consider the word a variant, while 0
    #   means a equal split.  Note that if a word is not listed
    #   in some sources than it counts as a variant.
    #print ">2>", Dumper(\@v1), "\n";
    @v1 = sort {$b->[1] <=> $a->[1]} @v1;
    $d->{rank} = \@v1;
    my @v2;
    push @v2, [$v1[0][0], [0,0]];
    my $fl = $v1[0][1];
    foreach (@v1[1..$#v1]) {
        my ($w, $l) = @$_;
        my $r;
        if    ($l >  0.32)                 {$r = [0,0]}
        elsif ($l == -1)                   {$r = [1,3]}
        elsif ($fl >= -0.32 && $l < -0.32) {$r = [1,2]}
        elsif ($fl - $l <= 0.65)           {$r = [0,0]}
        #elsif ($l < -0.32)                 {$r = [1,2]}
        else                               {$r = [1,1]}
        #printf ">>%s [%d,%d] %g %g %g\n", $w, @$r, $fl, $l, $fl - $l;
        push @v2, [$w,$r];
    }
    # @v2 not contains [<word>, <acceptable variant level range>]
    #print join(' / ',map {'A'.$_->[0].": ".$_->[1]." ".sprintf("%.2g",)} @v1), "\n";
    #print "    ".join(' / ', map {"$_->[1][2]: $_->[0]"} @v), (defined $note ? " $note" : ""), "\n";
    #print "    ".join(' / ', map {"$_->[1][0]: $_->[0]"} @v2), "\n";
    #print "??? ".join(' / ', map {sprintf("%s %.2g", $_->[0], $_->[1])} @v1), "\n";

    # merge @v @v2
    my @vf;
    eval {
        foreach (@v2) {
            my ($w, $l1) = @$_;
            my $other = yank @v, $w;
            die unless $other;
            my $l2 = $other->[1];
            my $new = [$w, merge $l1, $l2];
            push @vf, $new;
        }
        #foreach (@v) {
        #    my ($w, $l) = @$_;
        #    push @vf, [$w, 3];
        #}
        @vf = sort {$a->[1] <=> $b->[1]} @vf;
        #print "::: ".join(' / ', map {"$_->[1]: $_->[0]"} @vf), "\n";
        $d->{final} = \@vf;
    };
    $d->{error} = $@ if $@;
    #print "*** $@" if $@;
}}

my @suffex = (
    "s", "ed", "ing", "'s",
    "er", "ers", "er's",
    "est",
    "ness", "nesses", "ness's",
    "ly",
    "ment", "ments", "ment's",
    "ity", "ities", "ity's",
    "ion", "ions", "ion's",
    "age", "ages", "age's", "aged", "ageing",
    "al", "als", "al's",
    );

# my @affix_rules = (
#     ["s",   [["y", "ies", "[^aeiou]y"],
#              ["", "s", "[aeiou]y"],
#              ["", "es","[sxzh]"],
#              ["", "s", "[^sxzhy]"]]],
#     ["ed",  [["", "d", "e"],
#              ["y", "ied", "[^aeiou]y"],
#              ["", "ed","[^ey]"],
#              ["", "ed","[aeiou]y"]]],
#     ["ing", [["e", "ing", "e"],
#              ["", "ing", "[^e]"]]],
#     ["'s", [["", "'s", ""]]],
#     ["er", [["","r","e"],
#             ["y", "ier", "[^aeiou]y"],
#             ["","er","[aeiou]y"],
#             ["","er","[^ey]"]]],
#     ["ers", [["","rs","e"],
#             ["y", "iers", "[^aeiou]y"],
#             ["","ers","[aeiou]y"],
#             ["","ers","[^ey]"]]],
#     ["er's", [["","r's","e"],
#             ["y", "ier's", "[^aeiou]y"],
#             ["","er's","[aeiou]y"],
#             ["","er's","[^ey]"]]],
#     ["est", [["","st","e"],
#              ["y","iest","[^aeiou]y"],
#              ["","est","[aeiou]y"],
#              ["","est"."[^ey]"]]],
#     ["ness", [["y","iness","[^aeiou]y"],
#               ["","ness","[aeiou]y"],
#               ["","ness","[^y]"]]],
#     ["nesses", [["y","ineses","[^aeiou]y"],
#                 ["","nesses","[aeiou]y"],
#                 ["","nesses","[^y]"]]],
#     ["ness's", [["y","iness's","[^aeiou]y"],
#                 ["","ness's","[aeiou]y"],
#                 ["","ness's","[^y]"]]],
#     ["ment", [["y","iment","[^aeiou]y"],
#               ["","ment","[aeiou]y"],
#               ["","ment","[^y]"]]],
#     ["mentes", [["y","ineses","[^aeiou]y"],
#                 ["","mentes","[aeiou]y"],
#                 ["","mentes","[^y]"]]],
#     ["ment's", [["y","iment's","[^aeiou]y"],
#                 ["","ment's","[aeiou]y"],
#                 ["","ment's","[^y]"]]],
#     );

# sub find_affix($$) {
#     my ($w,$root) = @_;
#     foreach my $r (@affix_rules) {
#         foreach my $q (@{$r->[1]}) {
#             local $_ = $root;
#             m/$q->[2]$/ or next;
#             s/$q->[0]$/$q->[1]/ or die;
#             return $r->[0] if $_ eq $w;
#         }
#     }
#     return;
# }

# sub find_affix($$) {
#     my ($w,$root) = @_;
#     foreach my $s (@suffex) {
#         local $_ = $root;
#         if ("$root$s" eq $w) {
#             $_ = "$root$s";
#         } elsif (/[^aeiou]y$/) {
#             s/y$/i$s/;
#         } elsif (/e$/ && $s =~ /[aeiou]$/) {
#             s/e$/$s/;
#         }
#         return $s if $_ eq $w;
#     }
#     return;
# }

foreach my $cluster (@clusters) {
    my $main_d = $cluster->[0]{orig};
    my $main = $main_d ? $main_d->[0][0] : undef;
    my $last;
    foreach my $d (@$cluster) {
        #print $d->{line};
        if ($d->{line} =~ /^=== (\w+)/) {
            my $w = $1;
            my $pos = $2;
            my ($aff,$strip,$add) = find_affix($1, $main);
            if ($aff) {
                #print "<<$main/$aff (-$strip,+$add) = $w\n";
                my @n;
                my %prev;
                foreach (@$main_d) {
                    my ($w, @r) = @$_;
                    my $n = apply_affix($w, $aff, $strip, $add);
                    #print ".. $w $n\n";
                    last unless $n;
                    next if $prev{$n};
                    $prev{$n} = 1;
                    push @n, [$n, @r];
                }
                if (@n + 0 == @$main_d + 0) {
                    #print "YES $w\n";
                    $d->{orig} = \@n;
                }
            } else {
                #print "WARNING on $w\n";
            }
        }
        #print Dumper($d), "\n";
        if ($d->{error}) {
            $d->{final} = [map {[$_->[0], $_->[1][2]]} @{$d->{orig}}];
            push @{$d->{notes}}, "! error";
        }
        if ($d->{rank}) {
            die unless $d->{final};
            $last = $d;
        } elsif (defined $last && $d->{orig}) {
            my $num = @{$last->{orig}} + 0;
            my $i;
            my %map;
            my $aff;
            my $f = sub {
                my ($hint) = @_;
                undef $aff;
                foreach ($i = 0; $i < $num; $i++) {
                    last unless $i < @{$d->{orig}};
                    my $w = $d->{orig}[$i][0];
                    my $root = $last->{orig}[$i][0];
                    last unless defined $w && defined $root;
                    my ($a) = find_affix($d->{orig}[$i][0], $last->{orig}[$i][0], $hint);
                    last unless defined $a;
                    #print ">>$root/$a = $w\n";
                    $aff = $a unless defined $aff;
                    last unless $aff eq $a;
                    $map{$root} = $w;
                }
            };
            &$f;
            &$f("e$aff") if $i != $num;
            if ($i == $num) {
                #print ">0>", Dumper($last->{final}), "\n";
                $d->{final} = [map {[$map{$_->[0]}, $_->[1]]} @{$last->{final}}];
                push @{$d->{notes}}, "! error" if $last->{error};
                #print ">1>", Dumper($d->{final}), "\n";
            }
        }
        if (!$d->{final} && $d->{orig}) {
            $d->{final} = [map {[$_->[0], $_->[1][2]]} @{$d->{orig}}];
            #$d->{final} = [grep {$_->[0]} @{$d->{final}}];
            push @{$d->{notes}}, "! nl full" unless $varcon_output || $d->{ignore_full};
        }
        if ($d->{varcon}) {
            die if @{$d->{varcon}} > 1;
            my $line = $d->{varcon}[0][0];
            undef $varcon[$d->{varcon}[0][1]];
            my @n;
            my %r = read_varcon($line,@n);
            die if @n;
            die unless @{$r{A}} == 1;
            my $any = 0;
            foreach (@{$d->{final}}) {
                last if $_->[1] > 1;
                $any = 1 if $_->[0] == $r{A}[0][0];
            }
            die unless $any;
            delete $r{A};
            $d->{bysp} = {A => $d->{final}, %r}
        } elsif ($d->{final}) {
            $d->{bysp} = {A => $d->{final}};
        }
    }
}

my %rmap;
if ($varcon_output) {
    %rmap = ('' => '', '0' => '', '1' => 'v', '2' => 'V', '3' => '-');
} else {
    %rmap = ('' => '', '0' => '0', '1' => '1', '2' => '2', '3' => '3');
}

sub pretify($) {
    my $res;
    foreach (split / /, $_[0]) {
        my ($s,$n) = /^(.)(.?)$/ or die "?>$_<\n"; 
        $res .= $s.$rmap{$n}.' ';
    }
    chop $res;
    return $res;
}

my @varcon_cluster;
foreach my $line (@varcon) {
    next unless defined $line;
    my @n;
    my %r = read_varcon($line,@n);
    my %d;
    $d{bysp} = \%r;
    $d{notes} = \@n if @n;
    push @varcon_cluster, \%d, 
}
push @clusters, \@varcon_cluster;

foreach my $cluster (@clusters) {
    foreach my $d (@$cluster) {
        my $note = $d->{notes} ? " | ".join(' | ', @{$d->{notes}}) : "";
        #print Dumper($d), "\n";
        if ($d->{bysp}) {
            my %r;
            my @r;
            foreach my $sp (keys %{$d->{bysp}}) {
                my $f = $d->{bysp}{$sp};
                $f->[0][1] = '';
                foreach (@$f) {
                    #print ">>$_>$sp$_->[1]: $_->[0]<\n";
                    push @{$r{$_->[0]}}, "$sp$_->[1]";
                }
            }
            #print "<<\n";
            #print "XXX " if (keys %r == 1 && @{$r{(keys %r)[0]}} > 1);
            foreach my $w (keys %r) {
                push @r, [join (' ',sort @{$r{$w}}),$w];
            }
            @r = sort {$a->[0] cmp $b->[0]} @r;
            #push @r, map {"$sp$_->[1]: $_->[0]"} @$f;
            print join(' / ', map {pretify($_->[0]).": $_->[1]"} @r), $note, "\n";
            #print "?? ".join(' / ', map {sprintf("%s %.2g", $_->[0], $_->[1])} @{$d->{rank}}), "\n";
            if ($print_extra && $d->{error}) {
                print "  #? $d->{line}";
                print "  ?? ".join(' / ', map {sprintf("%s %.2g", $_->[0], $_->[1])} @{$d->{rank}}), "\n";
                print "  ** ", $d->{error};
            }
        } elsif ($d->{orig}) {
            print "#? $d->{line}" if $print_extra;
        } else {
            print "## $d->{line}" if $print_extra;
        }
    }
    print "\n" if $print_extra;
}
