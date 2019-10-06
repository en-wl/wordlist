package make_list;

use strict;
use warnings;

use utf8;

use DBI;

use Exporter ();
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(@standard %standard make_query get_wordlist make_hunspell_dict make_aspell_dict
                    dict_name dump_parms copyright);

our @standard = qw(en_US en_GB-ise en_GB-ize en_CA en_AU en_US-large en_GB-large en_CA-large en_AU-large);
our %standard = (
    'en_US' =>        {max_size => 60, spelling => ['US'], max_variant => 0, diacritic => 'strip'},
    'en_GB-ise' =>    {max_size => 60, spelling => ['GBs'], max_variant => 0, diacritic => 'strip'},
    'en_GB-ize' =>    {max_size => 60, spelling => ['GBz'], max_variant => 0, diacritic => 'strip'},
    'en_CA' =>        {max_size => 60, spelling => ['CA'], max_variant => 0, diacritic => 'strip'},
    'en_AU' =>        {max_size => 60, spelling => ['AU'], max_variant => 0, diacritic => 'strip'},
    'en_US-large' =>  {max_size => 70, spelling => ['US'], max_variant => 1, diacritic => 'both'},
    'en_GB-large' =>  {max_size => 70, spelling => ['GBs','GBz'], max_variant => 1, diacritic => 'both'},
    'en_CA-large' =>  {max_size => 70, spelling => ['CA'], max_variant => 1, diacritic => 'both'},
    'en_AU-large' =>  {max_size => 70, spelling => ['AU'], max_variant => 1, diacritic => 'both'});

sub dump_parms ( $;$ ) {
    my ($parms,$prefix) = (@_);
    $prefix = '' unless defined $prefix;
    my $res = '';
    foreach my $k (sort keys %$parms) {
        my $v = $parms->{$k};
        $res .= "$prefix$k: ";
        if (ref $v eq 'ARRAY') {
            if (@$v) {
                $res .= join (' ', @$v)."\n";
            } else {
                $res .= "<none>\n";
            }
        } else {
            $res .= "$v\n";
        }
    }
    return $res;
}

# sub to_name ( $ ) {
#     my ($parms) = (@_);
#     my @spelling = sort @$parms->{spelling};
#     my $name = 'en-' + join('+',@spelling);
#     $name = s/GBs+GBz/GB/;
#     my $v = $parms->{max_variant}
#     if ($v > 0) {$name .= "-v$v"}
#     $name .= "-$parms->{max_size}";
#     my $diacritic = $parms->{diacritic};
#     if ($diacritic eq 'strip') $name .= "-strip";
#     elsif ($diacritic eq 'both') $name .= "-both";
# }

sub make_query( $ ) {
    my ($parms) = (@_);
    my @where;
    my @parms;
    push @where, "size <= ?";
    push @parms, $parms->{max_size};
    push @where, "variant <= ?";
    push @parms, $parms->{max_variant};
    my @spellings;
    foreach (@{$parms->{spelling}}) {
        die "Unknown Spelling $_" unless $_ eq 'US' or $_ eq 'GBs' or $_ eq 'GBz' or $_ eq 'CA' or $_ eq 'AU';
        push @spellings, $_;
    }
    if (defined $parms->{special}) {
        my @special;
        foreach (@{$parms->{special}}) {
            push @special, "category = ?";
            push @parms, $_;
        }
        if (@special) {
            push @spellings, '(SP and ('.join(' or ', @special).'))';
        }
    } else {
        push @spellings, 'SP';
    }
    push @where, '('.join(' or ', @spellings).')';
    my $diacritic = $parms->{diacritic};
    $diacritic = 'only' unless defined $diacritic;
    if    ($diacritic eq 'strip') {push @where, "not accented"}
    elsif ($diacritic eq 'keep')  {push @where, "(accented or (not added and not accented))"}
    elsif ($diacritic eq 'both')  {}
    else {die "Unknown value for 'diacritic'"}
    my $where = join(' and ',@where);
    return ("select distinct word from speller_words join post using (pid) join info using (iid) where $where",
            @parms);
}

sub get_wordlist( $$ ) {
    my ($db,$parms) = (@_);
    my $dbh = DBI->connect("dbi:SQLite:dbname=$db","","");
    $dbh->{unicode} = 1;
    my ($query,@bind_values) = make_query($parms);
    #print "$query  w/ @bind_values\n";
    dump_parms($parms);
    my $sth = $dbh->prepare($query);
    $sth->execute(@bind_values);
    my $word;
    $sth->bind_columns(\$word);
    my @words;
    while ($sth->fetch) {push @words, $word}
    return \@words;
}

sub dict_name ( $ ) {
    my ($param) = (@_);
    my $sp;
    foreach (@{$param->{spelling}}) {
        s/^GB?$/GB/;
        if (defined $sp && $sp ne $_) {$sp = "";}
        else {$sp = $_;}
    }
    if ($sp) {return "en_$sp-custom";}
    else     {return "en-custom";}
}

sub make_hunspell_dict ( $$$ ) {
    use File::Temp 'tempdir';
    use POSIX 'getcwd';
    my ($name,$parms,$words) = (@_);
    my $dir = tempdir(CLEANUP => 1);
    my $cwd = getcwd();
    chdir $dir;
    open F, "> parms.txt";
    print F "With Parameters:\n";
    print F dump_parms($parms, '  ');
    close F;
    $ENV{SCOWL} = $cwd unless defined $ENV{SCOWL};
    undef $ENV{SCOWL_VERSION};
    open F, "| $ENV{SCOWL}/speller/make-hunspell-dict -one $name parms.txt > /dev/null" or die;
    binmode(F, ':encoding(iso88591)');
    foreach (@$words) {
        print F "$_\n";
    }
    close F or die "make-hunspell-dict failed";
    chdir $cwd;
    return "$dir/hunspell-$name.zip";
}

sub make_aspell_dict ( $$$ ) {
    use File::Temp 'tempdir';
    use POSIX 'getcwd';
    my ($git_ver,$parms,$words) = (@_);
    my $dir = tempdir(CLEANUP => 1);
    my $cwd = getcwd();
    chdir $dir;
    open F, "> parms.txt";
    print F dump_parms($parms, '  ');
    close F;
    $ENV{SCOWL} = $cwd unless defined $ENV{SCOWL};
    $git_ver =~ /^([^\']+)$/ or die;
    open F, "| $ENV{SCOWL}/speller/make-aspell-custom '$1' parms.txt > /dev/null" or die;
    binmode(F, ':encoding(iso88591)');
    foreach (@$words) {
        print F "$_\n";
    }
    close F or die "make-aspell-custom failed";
    chdir $cwd;
    return "$dir/aspell6-en-custom.tar.bz2";
}

sub copyright() {
    return <<'---';
Copyright 2000-2019 by Kevin Atkinson

  Permission to use, copy, modify, distribute and sell these word
  lists, the associated scripts, the output created from the scripts,
  and its documentation for any purpose is hereby granted without fee,
  provided that the above copyright notice appears in all copies and
  that both that copyright notice and this permission notice appear in
  supporting documentation. Kevin Atkinson makes no representations
  about the suitability of this array for any purpose. It is provided
  "as is" without express or implied warranty.

Copyright (c) J Ross Beresford 1993-1999. All Rights Reserved.

  The following restriction is placed on the use of this publication:
  if The UK Advanced Cryptics Dictionary is used in a software package
  or redistributed in any form, the copyright notice must be
  prominently displayed and the text of this document must be included
  verbatim.

  There are no other restrictions: I would like to see the list
  distributed as widely as possible.

Special credit also goes to Alan Beale <biljir@pobox.com> as he has
given me an incredible amount of feedback and created a number of
special lists (those found in the Supplement) in order to help improve
the overall quality of SCOWL.

Many sources were used in the creation of SCOWL, most of them were in
the public domain or used indirectly.  For a full list please see the
SCOWL readme.
---
}
