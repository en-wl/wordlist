#
# This script is my first attempt at a completely new approach to SCOWL.
# An approach that deals with words in terms of lemmas rather than raw
# words.
#
# Right now it just merges 2of12id (from alt12dicts) and varcon.txt.
#

use strict;
use warnings;

use Data::Dumper;
use IO::Handle;

autoflush STDOUT 1;
autoflush STDERR 1;

#use Carp;
#$SIG{ __WARN__ } = sub { Carp::cluck( @_ ) };
#$SIG{ __DIE__ } = sub { Carp::confess( @_ ) };

sub def_eq ( $$ ) {
  defined $_[0] && defined $_[1] && $_[0] eq $_[1];
}

package WithLevel;

sub new {
  my $self = shift;
  die unless $self eq 'WithLevel';
  die unless @_ == 2;
  if (defined $_[0] && $_[0] != 0) {
    return bless {level => $_[0], sps => $_[1]};
  } else {
    return $_[1];
  }
}

sub dump {
  my $self = shift;
  "[$self->{level}]: ".$self->{sps}->dump();
}

sub words {my $self = shift; $self->{sps}->words();}

sub level {my $self = shift; $self->{level};}
sub sps {my $self = shift; $self->{sps};}

package HeadWord;
#use fields qw(pos note level words);
# words is an array where the order is 
#   pos num meaing
#    *    1  <base>
#    N/?  2  <base> <plural>
#    N    3  <base> <possessive> <plural>
#    V    4  <base> <-ed> <-ing> <-s>
#    V    5  <base> <-ed> <p.p.> <-ing> <-s>
#    A    3  <base> <-er> <-est>
#    V    6+ <base> <other forms> ...
# NOTE: if a form doesn't exist for the word, the entry is undefined
sub new {
  my $self = shift;
  die unless $self eq 'HeadWord';
  #$self = fields::new($self);
  $self = bless {};
  if (@_ == 1) {
    $self->{pos} = '?';
    $self->{words}[0] = $_[0];
  } elsif (@_) {
    my ($pos, $note, $level, @words) = @_;
    $self->{pos} = $pos;
    $self->{note} = $note if $note;
    $self->{level} = $level if $level;
    my $num = @words;
    $self->{words} = [map {ref $_ eq 'ARRAY' ? new WithLevel @$_ : $_} @words];
    if    ($num == 2) {die unless $pos eq '?' || $pos eq 'N';}
    elsif ($num == 3) {die unless $pos eq 'N' || $pos eq 'A';}
    elsif ($num >= 4) {die unless $pos eq 'V';}
  } else {
    $self->{pos} = '?';
    $self->{words} = [];
  }
  return $self;
}

sub dump {
  my $self = shift;
  #use Data::Dumper;
  #print Dumper($self);
  my $res = '';
  $res .= "$self->{level}: " if defined $self->{level};
  $res .= $self->{pos};
  $res .= " {$self->{note}}" if defined $self->{note};
  $res .= " | ";
  $res .= join("\n    ", map {$_->dump()} @{$self->{words}});
  $res .= "\n";
  return $res;
}

sub words {
  my $self = shift;
  my %words;
  foreach (@{$self->{words}}) {
    my @wds = $_->words();
    foreach (@wds) {$words{$_}++}
  }
  return keys %words;
}

package Spellings;
# { <spelling>: word }

use overload
    '""' => \&dump,
    'eq' => sub {"$_[0]" eq "$_[1]"},
    'ne' => sub {"$_[0]" ne "$_[1]"};

sub new {
  my $self = shift;
  die unless $self eq 'Spellings';
  $self = bless {};
  if (@_ == 1) {
    if (ref $_[0] eq 'HASH') {
      %$self = %{$_[0]};
    } elsif (ref $_[0] eq 'ARRAY' || ref $_[0] eq 'SpellingsList') {
      foreach (@{$_[0]}) {
        my ($sps, $word) = @$_;
        die unless $sps && $word;
        foreach my $sp (split / /, $sps) {
          push @{$self->{$sp}}, $word;
        }
      }
    } elsif (ref $_[0]) {
      die "Unknown ref type.";
    } else {
      $self->{E} = [$_[0]];
    }
  } elsif (@_) {
    my ($sp, $main, $v0, $v1, $v2, $v3) = @_;
    die unless $sp =~ /^[EABCZ]$/;
    $self->{"$sp"} = [$main] if !ref $main;
    $self->{"$sp"} = $main   unless !ref $main;
    $self->{"${sp}0"} = $v0 if defined $v0 && @$v0;
    $self->{"${sp}1"} = $v1 if defined $v1 && @$v1;
    $self->{"${sp}2"} = $v2 if defined $v2 && @$v2;
    $self->{"${sp}3"} = $v3 if defined $v3 && @$v3;
   }
  return $self;
}

sub level {undef;}
sub sps {$_[0];}

sub as_list {
  my $self = shift;
  my @res;
  my @order;
  my %by_word;
  foreach my $sp (sort keys %$self) {
    foreach my $w (@{$self->{$sp}}) {
      push @order, $w unless exists $by_word{$w};
      push @{$by_word{$w}}, $sp;
    }
  }
  foreach my $w (@order) {
    my @sps = @{$by_word{$w}};
    push @res, [join(' ', @sps), $w];
  }
  return @res;
}

sub dump {
  my $self = shift;
  return join (' / ', map {"$_->[0]: $_->[1]"} $self->as_list());
}

sub words {
  my $self = shift;
  my %words;
  foreach my $sp (sort keys %$self) {
    foreach my $w (@{$self->{$sp}}) {
      next unless defined $w;
      $words{$w}++;
    }
  }
  return keys %words;
}

sub have {
  my ($self, $word) = @_;
  foreach my $sp (sort keys %$self) {
    foreach my $w (@{$self->{$sp}}) {
      return 1 if $w eq $word;
    }
  }
  return 0;
}

sub main {
  my ($self) = @_;
  return $self->{E}[0] if exists $self->{E};
  return $self->{A}[0];
}

sub sanity {
  my ($self, $word) = @_;
  foreach (keys %$self) {
    next unless /^(.)\d$/;
    return 0 unless exists $self->{$1};
  }
  return 1;
}

sub myeq {
  my ($a, $b) = @_;
  
}

package SpellingsList;

sub new {
  my $self = shift;
  die unless $self eq 'SpellingsList';
  return bless [@_];
}

sub level {undef;}
sub sps {$_[0];}

package Dictionary;
# a collection of headwords

sub new {
  my $self = shift;
  die unless $self eq 'Dictionary';
  return bless [[], {}];
}

sub add {
  my ($self, @rest) = @_;
  my ($data, $idx) = @$self;
  my $headword = @rest == 1 && ref $rest[0] eq 'HeadWord' 
      ? $rest[0] : new HeadWord @rest;
  my $num = @$data;
  push @$data, $headword;
  $headword->{idx} = $num;
  foreach my $w ($headword->words()) {
    push @{$idx->{$w}}, $num;
  }
  return $headword;
}

sub remove {
  my ($self, $to_remove) = @_;
  my ($data, $idx) = @$self;
  my $ref = $data->[$to_remove->{idx}];
  return unless defined $ref;
  die unless $ref eq $to_remove;
  undef $data->[$to_remove->{idx}];
}

sub lookup {
  my $self = shift;
  my ($data, $idx) = @$self;
  my ($word, $pos, $note) = @_;
  my @res;
  foreach my $i (@{$idx->{$word}}) {
    my $entry = $data->[$i];
    next unless defined $entry;
    next unless !defined $word || $entry->{words}[0]->have($word);
    next unless !defined $pos  || $pos eq $entry->{pos};
    next unless !defined $note || (defined $entry->{note} && $entry->{note} eq $note);
    push @res, $entry;
  }
  return @res;
}

sub lookup_anywhere {
  my $self = shift;
  my ($data, $idx) = @$self;
  my ($word) = @_;
  return grep {defined} map {$data->[$_]} @{$idx->{$word}};
}

sub entries {
  my $self = shift;
  my ($data, $idx) = @$self;
  return $data;
}

sub by_idx {
  my $self = shift;
  my ($data, $idx) = @$self;
  my ($i) = @_;
  return $data->[$i];
}

sub last_idx {
  my $self = shift;
  my ($data, $idx) = @$self;
  return $#$data;
}

sub dump {
  my $self = shift;
  my ($data, $idx) = @$self;
  foreach (@$data) {
    next unless defined $_;
    print $_->dump();
  }
}


package TwoOfTwelveId;

sub split_note($) {
  local $_ = $_[0];
  my @res = /^(.+?)(?: {(.+)})?$/ or die;
  return @res;
}

sub proc_entry($$$$$@);

sub read() {
  open F, "r/alt12dicts/2of12id.txt" or die;

  my $dict = new Dictionary;
  
  while (<F>) {
    s/\r?\n$// or die;
    # (uncommon flag, base word, part of speach, note, inflected forms)
    my ($flag,$base,$pos,$note,$d) = /^([-@]?)(\w+) (.)\s*(?:{(.+?)})?: ?(.*?)$/ or die;
    my @d = split /  /, $d;
    my $need_split = 0;
    my @note;
    foreach (@d) {
      next unless ($a, $b) = /^(.+?) \| (.+?)$/;
      $need_split = 1;
      ($a, $note[0]) = split_note($a);
      ($b, $note[1]) = split_note($b);
      $_ = [$a,$b];
      if (!$note[0] && !$note[1]) {
        if ($a eq $base) {
          @note = ('collection', 'individuals')
        } elsif ($b eq $base) {
          @note = ('individuals', 'collection');
        }
      }
    }
    if ($need_split) {
      proc_entry($dict,$flag,$base,$pos,defined $note[0] ? $note[0] : $note,
                 map {ref $_ ? $_->[0] : $_} @d);
      proc_entry($dict,$flag,$base,$pos,defined $note[1] ? $note[1] : $note,
                 map {ref $_ ? $_->[1] : $_} @d);
    } else {
      proc_entry($dict,$flag,$base,$pos,$note,@d);
    }
  }
  return $dict;
}

sub proc_entry($$$$$@) {
  my ($res,$flag,$base,$pos,$note,@d) = @_;
  no warnings;
  # print "$flag;$base;$pos;{$note}: ", join(';', @d), "\n";
  my @forms;
  foreach (@d) {
    my (@variant_1,@v2,@variant_2,@variant_3);
    while (s/ \/ (\S+)| \((.+?)\)//) {
      push @variant_1,$1 if defined $1;
      push @v2,split / /,$2 if defined $2;
    }
    my $word = $_;
    my $usage_flag = '';
    foreach ($word,@variant_1) {
      if (/^-$/) {
        # special case, form doesn't exist
        $_ = '-';
      } else {
        my ($f,$w) = /^([~\-]*)([A-Za-z']+)$/ or die "Bad entry \"$_\"";
        if ($f) {
          die if $usage_flag && $usage_flag ne $f;
          $usage_flag = $f;
        }
        $_ = $w;
      }
    }
    foreach (@v2) {
      my ($f,$w) = /^([~@\-]*)([A-Za-z']+)$/ or die "Bad entry \"$_\"";
      if ($f =~ s/~//) {
        die if $usage_flag && $usage_flag ne '~';
        $usage_flag = '~';
      }
      unless ($w) {push @variant_2, $w unless $f;} 
      else {       push @variant_3, $w if     $f;}
    }
    my $spellings = new Spellings 'E', $word, [], \@variant_1, \@variant_2, \@variant_3;
    if ($usage_flag) {
      push @forms, [80, $spellings];
    } else {
      push @forms, $spellings;
    }
  }
  my $level;
  $level = 80 if $flag;
  $res->add($pos, $note, $level, Spellings->new($base), @forms);
}

package Varcon;

require "r/varcon/varcon.pm";

sub read() {
  my $dict = new Dictionary;
  open F, "r/varcon/varcon.txt";
  while (<F>) {
    next if varcon::filter(\$_);
    my ($data, $notes) = /^(.+?)(?: \| (.+))?$/ or die;
    my %line = varcon::flatten(varcon::readline($data));
    my $spellings = new Spellings \%line;
    my $entry = $dict->add($spellings);
    #print "I got notes: $notes\n" if $notes;
    if ($notes) {
      local $_ = $notes;
      $entry->{level} = 70 if s/\s*\(-\)\s*//;
      $entry->{pos} = $1 if s/\s*<(.+?)>\s*//;
      $entry->{note} = $_ if /\S/;
    }
  }
  return $dict;
}

package main;

sub max($$) {
  no warnings 'uninitialized';
  $_[0] >= $_[1] ? $_[0] : $_[1];
}

my $tof12id = TwoOfTwelveId::read();
#print "yeah!\n";
#$tof12id->dump();
#print "---\n";
my $varcon = Varcon::read();
#$varcon->dump();

sub merge($$;$$);

sub pos_compatible ( $$ ) {
  return $_[0] eq $_[1]
      || ($_[0] eq '?' || $_[1] eq '?')
      || ($_[0] eq 'A' && $_[1] =~ /^A/)
      || ($_[1] eq 'A' && $_[0] =~ /^A/);
}

my @merged;

my $entries = $varcon->entries();
foreach my $variant_entry (@$entries) {
  my @variants = $variant_entry->{words}[0]->as_list();
  my $variant_note = $variant_entry->{note};
  next if defined $variant_note && $variant_note eq 'plural';
  #print ">>WORKING ON: ", $variant_entry->dump();
  # for each spelling look up all possible head words
  my $something = 0;
  my %by_key;
  my %by_key_note;
  foreach my $i (0 .. $#variants) {
    my ($sp, $word) = @{$variants[$i]};
    my @r = $tof12id->lookup($word);
    foreach (@r) {
      next unless pos_compatible($variant_entry->{pos}, $_->{pos});
      push @{$by_key{$_->{pos}}[$i]}, [$sp, $word, $_];
      push @{$by_key_note{$_->{pos}}{$_->{note}}[$i]}, [$sp, $word, $_] 
          if defined $_->{note} && !defined $variant_note;
    }
  }
  next unless %by_key; # i.e. something
  my $try;
  $try = sub {
    my $count = 0;
    my $by_key = $_[0];
    #print "ENTER TRY: $by_key\n";
    foreach my $key (keys %$by_key) {
      #print ">key>$key\n";
      my $fail = '';
      my @to_use;
      foreach my $i (0 .. $#variants) {
        #print ">>$i\n";
        my $r = $by_key->{$key}[$i];
        $r = [] unless defined $r;
        if (@$r > 1) {
        my @r2 = grep {def_eq($_->[2]->{note},$variant_note)} @$r;
        $r = \@r2 if @r2 == 1;
        }
        if (@$r == 1) {
          my ($sp, $word, $entry) = @{$r->[0]};
          push @to_use, [$sp, $entry];        
        } elsif (@$r == 0) {
          $fail = 'missed' unless $fail;
        } else {
          $fail = 'multi';
        }
      }
      if ($fail eq 'multi' && $by_key eq \%by_key && defined $by_key_note{$key}) {
        #print ">NOW TRYING MULTI on: ", $variant_entry->dump();
        my $c = $try->($by_key_note{$key});
        #print "<$c\n";
        next if $c > 1; # FIXME: Be more precise
      }
      $fail = 'sanity' unless $fail eq 'multi' || Spellings->new(\@to_use)->sanity;
      $fail = 'one' if $fail eq 'missed' && @variants > 1 && @to_use <= 1;
      my $dump_it = sub  {
        no warnings 'uninitialized';
        print $_[0];
        print "  Variants: ", $variant_entry->dump();
        foreach my $i (0 .. $#variants) {
          foreach (@{$by_key->{$key}[$i]}) {
            my ($sp, $word, $entry) = @$_;
            printf "  $i: $sp: $word: %s: %s\n", $entry->{pos}, $entry->{note};
          }
        }
      };
      $dump_it->("ERROR: Skipping Due to Multiple Headwords:\n") if $fail eq 'multi';
      #$dump_it->("ERROR: $fail\n") if $fail && $fail ne 'missed';
      
      next if $fail && $fail ne 'missed';

      # OK we have somethin, now determine which entry will be considered
      # the main one, this makes a diffrence becuase for the level the
      # main entry overriders all others, the main entry should be one the
      # with only one line in the variant table (see casino for an example
      # why). 
      my $main;
      foreach (@to_use) {
        my ($sp, $entry) = @$_;
        my @r = $varcon->lookup_anywhere($entry->{words}[0]{E}[0]);
        die unless @r > 0;
        $main = $entry if !defined $main && @r == 1;
      }
      $main = $to_use[0][1] unless defined $main;

      #print "MERGING:\n", Dumper($main, \@variants);
      my $headword = merge($main, \@to_use, $variant_note, $variant_entry->{level});
      die unless $headword;
      push @merged, $headword;
      $count++;
    }
    return $count;
  };
  $try->(\%by_key);
}

foreach my $entry (@merged) {
  foreach (@{$entry->{merged_from}}) {
    $tof12id->remove($_->[1])
  }
  my @dups = $tof12id->lookup($entry->{words}[0]->sps->main, $entry->{pos}, $entry->{note});
  @dups = grep {$_->{words}[0]->sps eq $entry->{words}[0]->sps} @dups;
  if (@dups) {
    print "DUP\n";
    foreach (@dups) {
      print $_->dump();
    }
    print $entry->dump();
  } else {
    $tof12id->add($entry);
  }
}

print "YEAH!\n";
$tof12id->dump();

#exit(0);
#
#
#my $last_idx = $tof12id->last_idx();
#for (my $i = 0; $i <= $last_idx; ++$i) {
#   my $entry = $tof12id->by_idx($i);
#   my $headword = $entry->{words}[0]{E}[0];
#   my @v = $varcon->lookup($headword);
#   foreach my $v (@v) {
#     merge($entry, $v);
#   }
#}

sub change_variants($$);
sub combine_forms(\@@);

sub merge($$;$$) {
  my ($entry, $v, $note, $level) = @_;
  #return if $entry->{merged};
  my @variants = @$v;
  my @headwords;
  foreach (@variants) {
    my ($sp, $word) = @$_;
    if (ref $word eq 'HeadWord') {
      push @headwords, [$sp, $word];
    } elsif ($word eq $entry->{words}[0]{E}[0]) {
      push @headwords, [$sp, $entry];
    } else {
      my @others = $tof12id->lookup($word, $entry->{pos});
      next unless @others == 1;
      push @headwords, [$sp, @others];
    }
  }
  return if @variants > 1 && @headwords <= 1;
  #foreach (@headwords) {
  #  $_->[1]{merged}++;
  #}
  #print "Will merge [$entry->{words}[0]{E}[0]]: ", (join ' ', map {$_->[1]{words}[0]{E}[0]} @headwords), "\n";
  # prep new_forms with info from main entry
  my @new_forms = map {new WithLevel ($_->level, new SpellingsList)} @{$entry->{words}};
  foreach (@headwords) {
    my ($sp, $entry) = @$_;
    combine_forms @new_forms, map {change_variants $_, $sp} @{$entry->{words}};
  }
  #print Dumper(\@new_forms);
  my $headword = new HeadWord($entry->{pos}, 
                              ($entry->{note} || $note), 
                              max($entry->{level}, $level), 
                              map {new WithLevel ($_->level, new Spellings $_->sps)} @new_forms);
  $headword->{merged_from} = \@headwords;
  return $headword;
}

sub zip_sp(&$$);
sub change_variant($$);
sub uniq(@);

sub change_variants($$) {
  my ($spellings, $level, $new_sp) = ($_[0]->sps, $_[0]->level, $_[1]);
  my @res;
  foreach ($spellings->as_list()) {
    my ($sp, $word) = @$_;
    my @sps = zip_sp {change_variant($a,$b)} $sp, $new_sp;
    @sps = uniq @sps;
    #print ">>$sp -> $new_sp = @sps: $word\n";
    push @res, [join(' ', @sps),$word];
  }
  return new WithLevel ($level, new SpellingsList @res);
}

sub zip_sp(&$$) {
  my $f = $_[0];
  my @a = split / /, $_[1];
  my @b = split / /, $_[2];
  local($a, $b);
  my @res;
  foreach $a (@a) {
    foreach $b (@b) {
      push @res, &$f;
    }
  }
  return @res;
}

sub sp_max($$) {
  return $_[0] if $_[0] eq $_[1];
  return $_[1] if $_[0] eq '';
  return $_[0] if $_[1] eq '';
  return $_[1] if $_[1] > $_[0];
  return $_[0] if $_[0] > $_[1];
  die;
}

sub change_variant($$) {
  my ($old, $new) = @_;
  my @old = $old =~ /^(.)(\d?)$/ or die "Bad sp: $old";
  my @new = $new =~ /^(.)(\d?)$/ or die "Bad sp: $new";
  return $new[0].sp_max($old[1],$new[1]);
}

sub uniq(@) {
  my %seen;
  my @res;
  foreach (@_) {
    push @res, $_ unless $seen{$_};
    $seen{$_}++;
  }
  return @res;
}

sub combine_forms(\@@) {
  my ($res) = shift;
  #printf "?? %d %d\n", 0+@$res, 0+@_;
  if (@$res == 0) {
    @$res = @_;
  } else {
    die unless @$res == 1 || @_ == 1 || @$res == @_;
    my $num = @$res == 1 || @_ == 1 ? 1 : 0+@$res;
    foreach my $i (0..$num-1) {
      no warnings 'uninitialized';
      #FIXME: reenable
      #die unless $res->[$i]->level == $_[$i]->level;
      push @{$res->[$i]->sps}, @{$_[$i]->sps}
    }
  }
}


#my $entries = $varcon->entries();
#foreach my $entry (@$entries) {
#  @to_try = $tof12id->lookup_anywhere(...);
#  next unless @to_try;
#  
#}

