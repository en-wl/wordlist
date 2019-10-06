#!/usr/bin/perl -T

use CGI;
use strict;
use warnings;
use utf8;
use File::Basename;

use lib '/opt/app/wordlist/scowl/sql';
#use speller_lookup qw(lookup to_html);
use make_list qw(@standard %standard get_wordlist make_hunspell_dict make_aspell_dict
                 dict_name dump_parms copyright); 

delete @ENV{qw(IFS CDPATH ENV BASH_ENV)};
$ENV{PATH} = "/usr/local/bin:/bin:/usr/bin";
$ENV{PERL5LIB}="/opt/app/perl-lib/lib/perl5/5.8.8/:/opt/app/perl-lib/lib/perl5/site_perl/5.8.8/";

my $q = CGI->new;

my $defaults = defined $q->param('defaults') ? $q->param('defaults') : 'en_US';
die unless defined $standard{$defaults};
my %param = %{$standard{$defaults}};

my @dicts = @standard;
my $dicts_html = join('',map {qq`<a href="?defaults=$_">$_</a> \n`} @dicts);

sub make_option_list ($$$$) {
    my ($name,$default,$keys,$values) = @_;
    my $res = qq`<select name="$name">`;
    foreach (@$keys) {
        my $selected = $_ eq $default ? "selected" : "";
        $res .= qq`  <option value="$_" $selected>$values->{$_}</option>\n`;
    }   
    $res .= "</select>";
    return $res;
}
sub make_check_list ($$$$) {
    my ($name,$default,$keys,$values) = @_;
    my $res = '';
    foreach my $k (@$keys) {
        my $checked = (grep {$k eq $_} @$default) ? "checked" : "";
        $res .= qq ` <label for="$name-$k"><input type="checkbox" id="$name-$k" name="$name" value="$k" $checked>$values->{$k}</label>`
    }
    return $res;
}
my $use_parms = defined $q->param('download');
sub set_param_from_form ($$;$) {
    my ($name,$keys,$multi) = @_;
    if ($use_parms) {
        my @values = $q->param($name);
        die if @values != 1 && !$multi;
        my @v;
        foreach my $v (@values) {
            my @v0 = grep {$_ eq $v} @$keys;
            die unless @v0;
            push @v, @v0;
        }
        $param{$name} = [@v] if  $multi;
        $param{$name} = $v[0] if !$multi;
    } 
}

my %sizes = (10 => "10", 
             20 => "20",
             35 => "35 (small)",
             40 => "40",
             50 => "50 (medium)",
             55 => "55",
             60 => "60 (default)",
             70 => "70 (large)",
             80 => "80 (huge)",
             95 => "95 (insane)");
set_param_from_form('max_size', [keys %sizes]);
my $sizes_html = make_option_list("max_size",$param{max_size},[sort keys %sizes],\%sizes);

my %spellings = ("US" => "American",
                 "GBs" => "British (-ise spelling)",
                 "GBz" => "British (-ize/OED spelling)",
                 "CA" => "Canadian",
                 "AU" => "Australian");
my @spellings = qw(US GBs GBz CA AU);
set_param_from_form('spelling', \@spellings, 1);
my $spellings_html = make_check_list("spelling",$param{spelling},\@spellings,\%spellings);

my %variant = (0 => "0 (none)",
               1 => "1 (common)",
               2 => "2 (acceptable)",
               3 => "3 (seldom-used)");
set_param_from_form('max_variant', [keys %variant]);
my $variant_html = make_option_list("max_variant",$param{max_variant},[sort keys %variant],\%variant);

my %accents = ('strip' => "Strip (café becomes cafe)",
               'keep' => "Keep",
               'both' => "Include Both (cafe &amp; café)");
my @accents = qw(strip keep both);
set_param_from_form('diacritic', \@accents);
my $accents_html = make_option_list("diacritic",$param{diacritic},\@accents,\%accents);

my %special = ('hacker' => "Hacker (for example grepped)",
               'roman-numerals' => "Roman Numerals");
$param{special} = [keys %special] unless defined $param{special};
set_param_from_form('special', [keys %special], 1);
my $special_html = make_check_list("special",$param{special},[keys %special],\%special);

if (defined $q->param("download")) {
    $ENV{SCOWL}="/opt/app/wordlist/scowl";
    my $words = get_wordlist("$ENV{SCOWL}/scowl.db",\%param);
    if ($q->param("download") eq 'hunspell') {
        my $file = make_hunspell_dict (dict_name(\%param),\%param,$words);
        print $q->header(-type => 'application/zip',
                         -attachment => basename $file,
                         -Content_length  => -s $file);
        $/ = undef;
        open F, $file or die;
        binmode(F);
        binmode(STDOUT);
        print <F>;
        exit 1;
    } elsif ($q->param("download") eq 'aspell') {
        chdir $ENV{SCOWL};
        my $git_ver = `git log --pretty=format:'%cd [%h]' -n 1`;
        my $file = make_aspell_dict ($git_ver,\%param,$words);
        print $q->header(-type => 'application/octet-stream',
                         -attachment => basename $file,
                         -Content_length  => -s $file);
        $/ = undef;
        open F, $file or die;
        binmode(F);
        binmode(STDOUT);
        print <F>;
        exit 1;
    } elsif ($q->param("download") eq 'wordlist') {
        use IO::Handle;
        chdir $ENV{SCOWL};
        my $git_ver = `git log --pretty=format:'%cd [%h]' -n 1`;
        my $dir;
        my $fh = \*STDOUT;
        my $charset = $q->param('encoding') eq 'utf-8' ? 'UTF-8' : 'ISO-8859-1';
        my $format = $q->param('format');
        if ($format eq 'inline') {
            print $q->header(-type => 'text/plain', -charset => $charset);
        } else {
            use File::Temp 'tempdir';
            $dir = tempdir(CLEANUP => 1);
            $dir .= "/SCOWL-wl";
            mkdir $dir;
            $fh = new IO::Handle;
            open $fh, '>', "$dir/README";
        }
        print $fh "Custom wordlist generated from http://app.aspell.net/create using SCOWL\n";
        print $fh "with parameters:\n";
        print $fh dump_parms(\%param, '  ')."\n";
        print $fh "Using Git Commit From: $git_ver\n";
        print $fh "\n";
        print $fh copyright();
        print $fh "\n";
        print $fh "http://wordlist.aspell.net/\n";
        print $fh "\n";
        if ($format eq 'inline') {
            print "---\n";
        } else {
            open $fh, '>', "$dir/words.txt";
        }
        binmode($fh, ":encoding($charset)");
        foreach my $w (sort @$words) {
            print $fh "$w\n";
        }
        if ($format eq 'inline') {
            exit 1;
        } else {
            system('cp', '-a', 'README', "$dir/README_SCOWL");
            chdir($dir);
            my $file;
            if ($format eq "tar.gz") {
                chdir("..");
                system('tar cfz SCOWL-wl.tar.gz SCOWL-wl/');
                $file = "SCOWL-wl.tar.gz";
                print $q->header(-type => 'application/octet-stream',
                                 -attachment => $file,
                                 -Content_length  => -s $file);
            } elsif ($format eq "zip") {
                system('zip -9 -l ../SCOWL-wl.zip *');
                chdir("..");
                $file = "SCOWL-wl.zip";
                print $q->header(-type => 'application/zip',
                                 -attachment => $file,
                                 -Content_length  => -s $file);
            }
            $/ = undef;
            open F, $file or die;
            binmode(F);
            binmode(STDOUT);
            print <F>;
            exit 1;
        }
    }
}

print $q->header();
print <<"---";
<html>
<head>
<title>SCOWL Custom List/Dictionary Creator</title>
</head>
<body>
<p>
Use this tool to create and download custimized Word Lists or Hunspell
dictionaries from <a href="http://wordlist.aspell.net/">SCOWL</a>.
</p>
<p>
Using defaults for <b>$defaults</b> dictionary.
<p>
Reload with defaults from: $dicts_html dictionary.
</p>
<form>
SCOWL Size: $sizes_html
<p>
Spelling(s): $spellings_html
<p>
Include Spelling Variants up to Level: $variant_html
<p>
Diacritic Handling (for example café): $accents_html
<p>
Special Lists to Include: $special_html
<p style="line-height: 2">
<button type="submit" name="download" value="wordlist">Download as Word List</button> Encoding: <select name="encoding">
  <option value="utf-8">UTF-8
  <option value="iso-8859-1">ISO-8859-1
</select>
Format: <select name="format">
  <option value="inline">Inline
  <option value="tar.gz">tar.gz (Unix EOL)
  <option value="zip">zip (Windows EOL)
</select>
<br>
<button type="submit" name="download" value="hunspell">Download as Hunspell Dictionary</button>
<button type="submit" name="download" value="aspell">Download as Aspell Dictionary</button>
<p>
<button type="reset">Reset to Defaults</button>
<p>
<i>
For additional help on the meaning of any of these options please see the <a href="http://wordlist.aspell.net/scowl-readme/">SCOWL Readme</a>.
</i>
</form>
</body>
---
