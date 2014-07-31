#!/bin/perl

use strict;
use warnings;

use IO::File;
use List::Util qw(min minstr);

chdir "working";

sub slurp_list ($) {
    my ($fn) = @_;
    open F, $fn or die "Unable to open $fn.";
    my %words;
    while (<F>) {
        chomp;
        $words{$_} = []
    }
    return \%words;
}

my $marco = slurp_list "marco.txt";
my @marco = sort keys %$marco;
my $diff  = slurp_list "en_GB-only.txt";
my @diff = sort keys %$diff;
my $scowl = slurp_list "en_GB.txt";
my $base = slurp_list "../src/base.txt";

sub add_tag($$) {push @{$diff->{$_[0]}}, $_[1] unless have_tag($_[0], $_[1]);}
sub tags($) {$diff->{$_[0]}}
sub have_tag($$) {grep {$_ eq $_[1]} @{$diff->{$_[0]}}}

# Find words in special list

foreach (keys %{slurp_list "../../scowl/final/special-hacker.50"}) {
    next unless exists $diff->{$_};
    add_tag  $_, "hacker";
}

foreach (keys %{slurp_list "../../scowl/final/special-roman-numerals.35"}) {
    next unless exists $diff->{$_};
    add_tag $_, "roman-numeral";
}

# Find compound forms where the word exists but with a dash in marco list

open O, ">../varcon-compound.txt";
foreach (@marco) {
    my $orig = $_;
    next unless s/-//g;
    next unless exists $diff->{$_};
    add_tag $_, "compound";
    print O "SCOWL: $_ / D.M.: $orig\n";
}

# Find abbreviations
# FIMXE: Do a better job, use abbreviations category
#   but don't mark all uppercase ie UT AFAIK etc

my %aseen;
open O, ">../abbreviation.txt";
foreach (@marco) {
    my $orig = $_;
    next unless s/\.$//;
    next unless exists $diff->{$_};
    add_tag $_, "abbreviation";
    next if $aseen{$_};
    $aseen{$_} = 1;
    print O "SCOWL: $_ / D.M.: $orig\n";
}

open F, "cd ../../scowl; ./mk-list -f en_GB-ize en_GB-ise 60 | grep abbreviations | { cd final; xargs cat; } |";
while (<F>) {
    chomp;
    next if /^[A-Z]+$/;
    next unless exists $diff->{$_};
    add_tag $_, "abbreviation";
    next if $aseen{$_};
    $aseen{$_} = 1;
    print O "SCOWL: $_\n";
}

open F, "../../scowl/r/alt12dicts/abbr.lst" or die;
while (<F>) {
    chomp;
    next unless s/\.$//;
    next unless exists $diff->{$_};
    add_tag $_, "abbreviation";
    next if $aseen{$_};
    $aseen{$_} = 1;
    print O "SCOWL: $_\n";
}

# Find other variant problems

open F, "variant.tab";
my %variant;
while (<F>) {
    chomp;
    my $line = [split "\t", $_];
    foreach my $w (@$line) {
        $variant{$w} = $line;
    }
}
my %seen;
foreach my $mw (@marco) {
    my $variants = $variant{$mw};
    foreach my $w (@$variants) {
        next if $seen{$w};
        next unless exists $diff->{$w};
        #print ">variant> $w\n";
        add_tag $w, "variant";
        $seen{$w} = $mw;
    }
}

{
  use lib '../varcon';
  use varcon;
  my %used;
  open F, "../../varcon/varcon.txt";
  open O1, ">../varcon-lookinto.txt";
  #open O2, ">../varcon-davidbad.txt";
  local $/ = "\n\n";
  while (my $cluster = <F>) {
      chomp $cluster;
      my @words;
      foreach my $line (split "\n", $cluster) {
          next if varcon::filter $line;
          next if $line =~ /\(-\)/;
          push @words, varcon::get_words($line)
      }
      my $use = 0;
      my $ize_only = 1;
      foreach my $w (@words) {
          if ($seen{$w} && grep {$_ eq $seen{$w}} @words) {
              $ize_only = 0 unless (($w =~ /iz(a|e|i)/ && $seen{$w} =~ /is(a|e|i)/)
                                    || ($seen{$w} =~ /iz(a|e|i)/ && $w =~ /is(a|e|i)/));
              $use = 1;
          }
      }
      if ($use) {
          my @found;
          foreach my $w (@words) {
              if    ($$diff{$w})  {$found[0]{$w} = 1}
              elsif ($$scowl{$w}) {$found[2]{$w} = 1}
              elsif ($$marco{$w}) {$found[1]{$w} = 1}
          }
          my @found_desc = ('SCOWL', 'D./M.', 'Both ');
          my $extra = '';
          foreach my $i (0,1,2) {
              my @words = sort keys %{$found[$i]};
              next unless @words;
              $extra .= "## NOTE, in $found_desc[$i]: @words\n";
          }
          if ($ize_only && $cluster =~ "<verified>") {
              #print O2 "$cluster\n$extra\n";
          } else {
              print O1 "$cluster\n$extra\n";
          }
      }
  }
  open O, ">../varcon-notin.txt";
  foreach my $w (sort keys %seen) {
      next if $used{$w};
      print O "SCOWL: $w / D.M.: $seen{$w}\n";
  }
}


# Determine if it is a new word from the approximate point where en_GB
# was forked

foreach (@diff) {
    next if exists $base->{$_};
    my ($b) = /^(.+?)(\'s)?$/;
    next if exists $base->{$b};
    add_tag $_, "new";
}

# Munched list
# Add tags to derivied forms when it is reasonable to do so

my %munched;
open F, "cat en_GB-only.munched | aspell expand --local-data-dir=../src/ -l en2 |" or die;
while (<F>) {
    chomp;
    my ($base, @others) = split ' ';
    $munched{$base} = [@others];
}

sub tags_compatible($$) {
    my ($base,$other) = @_;
    foreach my $tag (@$other) {
        return 0 if not grep {$_ eq $tag} @$other
    }
    return 1;
}

foreach my $base (keys %munched) {
    my @others = @{$munched{$base}};
    my $all_same = 1;
    next unless @others && @{tags $base};
    foreach (@others) {
        next if tags_compatible(tags $base, tags $_);
        $all_same = 0;
    }
    next unless $all_same;
    foreach (@others) {
        @{tags $_} = @{tags $base}
    }
}

# Find new possive forms

foreach (@diff) {
    my ($base) = /^(.+?)\'s$/ or next;
    next unless exists $marco->{$base};
    add_tag $_, "possessive";
}

#
# Determine the source
#

my %srcRaw;
foreach my $f (<../../scowl/debug/*>) {
    die unless $f =~ /\/(\d\d)\.(.+)$/;
    my $level = $1;
    my $category = $2;
    next unless $level <= 60;
    open F, $f or die;
    foreach my $word (<F>) {
        chomp $word;
        next if exists $srcRaw{$word}{$category} && $srcRaw{$word}{$category} <= $level;
        $srcRaw{$word}{$category} = $level;
    }
}

my %srcList;
my %srcInfo;
foreach my $w (@diff) {
    my $s = $srcRaw{$w};
    my %tally;
    while (my ($k,$level) = each %$s) {
        my ($type,$category) = $k =~ /^(.)\.(.+)/ or die;
        push @{$tally{$type}{$level}}, $category;
    }
    my $level = minstr('99', keys %{$tally{'l'}});
    my $plus = minstr('99', keys %{$tally{'+'}});
    if ($level < $plus) {
        push @{$srcList{$w}}, $level; 
        $srcInfo{$w}{level} = $level;
        $srcInfo{$w}{first} = $level;
    } else {
        if (defined $tally{'+'}{$plus}) {
            foreach (@{$tally{'+'}{$plus}}) {$srcInfo{$w}{'+'}{$_} = $plus}
            delete $srcInfo{$w}{'+'}{affixes} if defined $srcInfo{$w}{'+'}{possessive};
            push @{$srcList{$w}},map {"$plus.$_"} (sort keys %{$srcInfo{$w}{'+'}})
        }
        if ($level != '99') {
            push  @{$srcList{$w}}, $level; 
            $srcInfo{$w}{level} = $level
        }
        $srcInfo{$w}{first} = $plus
    }
}

#
# find possible 2of12id problems
#

open F, "../../alt12dicts/2of12id.txt" or die;
my %root;

while (<F>) {
  s/\r?\n$// or die;
  # (flags, base word, part of speach, infl forms)
  my ($d,$w,$p,$a) = /^([-@]?)(\w+) (.).*: ?(.*)$/ or die;
  my @a = $a =~ /([-~@\w]+)/g;
  @a = map {"$d$_"} @a if ($d);
  foreach (@a) {
      next unless /^\w+$/;
      $root{$_}{$w} = 1;
  }
}
foreach (keys %root) {
    $root{$_} = [sort keys %{$root{$_}}]
}

outer:
foreach my $w (@diff) {
    next unless $srcInfo{$w}{'+'};
    #next if exists $srcInfo{$w}{level} && $srcInfo{$w}{level} < 55;
    next if $w =~ /\'s$/;
    next if have_tag $w, "variant";
    next unless defined $root{$w} && @{$root{$w}} > 0;
    foreach (@{$root{$w}}) {next outer unless exists $marco->{$_}}
    add_tag $w, "2of12id"
}

open F, "../../alt12dicts/2of12id.txt" or die;
open O, ">../2of12id-lookinto.txt" or die;
while (<F>) {
  s/\r?\n$// or die;
  my ($w,$p) = /^([-@]?\w+) (.).*: ?.*$/ or die;
  my ($a,$b) = /^(.+):(.*)$/ or die;
  if (exists $marco->{$w}) {
      $b =~ s/([-~@\w]+)/(have_tag($1, '2of12id') ? (have_tag($1, 'new') || !$srcInfo{$1}{'+'}{affixes} || exists $srcInfo{$1}{level} ? '?'.$1 : '??'.$1) : $1)/ge;
      print O "$a:$b\n" if $b =~ /\?/;
  } 
}

#
#
#

open O, ">res";

foreach (sort @diff) {
    my @tags = @{$diff->{$_}};
    #next unless @tags == 0;
    print O "$_";
    print O ": @tags" if (@tags);
    print O ": <ok>" if !@tags || (@tags == 1 && $tags[0] eq 'new');
    print O " [" . join(' ', @{$srcList{$_}}) . "]" if defined $srcList{$_};
    print O "\n";
}

# Lists to make

# From tags:
# possessive, variant, compound, 2of12id problems
my @tags = qw(possessive variant abbreviation compound hacker roman-numeral 2of12id);
# sizes
my @sizes = qw(40 50 60);

my %fh;
foreach (@tags) {$fh{$_} = new IO::File ">$_.lst"}
foreach (@sizes) {$fh{$_} = new IO::File ">$_.lst"}

outer:
foreach my $w (sort @diff) {
    foreach my $tag (@tags) {
        if (have_tag $w, $tag) {print {$fh{$tag}} "$w\n"; next outer;}
    }
    foreach my $size (@sizes) {
        if ($srcInfo{$w}{first} <= $size) {print {$fh{$size}} "$w\n"; next outer;}
    }
    die "What do I do with: $w?";
}
foreach (values %fh) {close $_;}

foreach my $size (@sizes) {
    system("cat $size.lst | aspell --local-data-dir=../src -l en2 munch-list | LC_COLLATE=C sort -u | aspell --local-data-dir=../src -l en2 expand > $size.tmp");
    open F, "$size.tmp";
    open O, ">../$size.txt";
    while (<F>) {
        chomp;
        my @words = split ' ';
        if (have_tag $words[0],'new') {print O "+ $_\n";}
        else                          {print O "- $_\n";}
    }
}

open O, ">../possessive.txt";
foreach my $w (sort @diff) {
    next unless have_tag $w, 'possessive';
    if (have_tag $w,'new') {print O "+ $w\n";}
    else                   {print O "- $w\n";}
}

