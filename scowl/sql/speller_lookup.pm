package speller_lookup;

use strict;
use warnings;

use utf8;

use DBI;

use Exporter ();
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(lookup %notes to_html to_text);

sub lookup($$@) {
    my ($db,$dict,@words) = @_;

    my $dbh = DBI->connect("dbi:SQLite:dbname=$db","","");
    $dbh->{unicode} = 1;

    my %active_notes;
    my @table;

    my $try1 = $dbh->prepare("select * from lookup where dict = ? and word = ?");
    my $try2 = $dbh->prepare("select l.* from lookup l, dict_info d where d.dict = ? and word = ? and".
                             "(not d.US or l.US) and (not d.GBs or l.GBs) and (not d.GBz or l.GBz) and (not d.CA or l.CA)");
    my $try3 = $dbh->prepare("select * from lookup where word = ?");

    my $dis = $dbh->prepare("select * from dict_info where dict = ?");
    $dis->execute($dict);
    my $di = $dis->fetchrow_hashref;
    
    my $fetch = sub {
        my $sth = $_[0];
        my $first = $sth->fetchrow_hashref;
        return undef unless defined $first;
        my $res = [$first];
        my $onum = $first->{onum};
        while (my $row = $sth->fetchrow_hashref) {
            last if $row->{onum} != $onum;
            push @$res, $row;
        }
        return $res;
    };
    
    my $lookup = sub {
        my ($dict,$word) = @_;
        my $res;
        
        $try1->execute($dict,$word);
        $res = $fetch->($try1);
        return $res if $res;
        
        $try3->execute($word); # do this query first, as try2 is expensive
        my $res3 = $fetch->($try3);
	return $res3 unless $res3; 

        $try2->execute($dict,$word);
        $res = $fetch->($try2);
        return $res if $res;
	return $res3;
    };

    foreach (@words) {
	my ($word) = /^[ \r\n]*(.*?)[ \r\n]*$/;
	next if $word eq '';
        my $res = $lookup->($dict,$word);
        my $found = 0;
        my $found_in = "";
        my @notes;
        if ($res && defined $res->[0]{dict} && $res->[0]{dict} eq $dict) {
            $found = 1;
        } elsif ($res && defined $res->[0]{dict}) {
            $found_in = join(", ", map {$_->{dict}} @$res);
        } elsif ($res && $res->[0]{size} > $di->{max_size}) {
            $found_in = "larger (size $res->[0]{size}) SCOWL size [1]";
            $active_notes{1} = 1;
        } elsif ($res) {
            $found_in = "SCOWL [2]";
            $active_notes{2} = 1;
        }
        if ($res) {
            if ($res->[0]{variant} > $di->{max_variant}) {
                my $v = $res->[0]{variant} + 1;
                push @notes, "level $v variant [3]";
                $active_notes{3} = 1;
            }
            if ($res->[0]{SP}) {
                push @notes, "found in \"$res->[0]{category}\" list [4]";
                $active_notes{4} = 1;
            }
            if ($res->[0]{accented}) {
		unless ($found) {
		    push @notes, "word with diacritic marks [5]";
		    $active_notes{5} = 1;
		}
            } elsif ($res->[0]{added}) {
                push @notes, "word added by removing diacritic marks [6]";
                $active_notes{6} = 1;
            }
        }
        push @table, [$word, $found, $found_in, join("; ", @notes)];
    }

    return {dict => $dict, table => \@table, active_notes => \%active_notes}
}

my $notes_text = <<'---';

[1] The word was not in any of the speller dictionaries but was found
    in an larger SCOWL size.  The smaller dictionaries included words
    up to size 60, and the larger dictionary include words up to size
    70.

[2] This word not in any of the speller dictionaries but was found in
    SCOWL.  See the notes column for hints on why it was excluded.

[3] The word is considered a spelling variant.  To promote consistent
    spelling, only one spelling of a word is generally included in a
    the smaller dictionary.  The larger dictionary lets in common
    variants (level 1).

[4] This word was found in a special list and may not be considered a
    normal word.

[5] This word has diacritic marks (for example, café).  In the smaller
    dictionary diacritic marks are removed.  In the larger dictionary
    both forms, with and without diacritic marks, are included.

[6] This word was created by removing diacritic marks (for example,
    café becomes cafe)
---
our %notes;
foreach (split /\n\n/, $notes_text) {
    next unless /[^\n ]/;
    /\[(\d+)\] (.+)/s or die;
    $notes{$1} = $2;
}

sub to_html( $ ) {
    my $d = $_[0];
    print "<table border=1 cellpadding=2>\n";
    print "<tr><th>Word<th>In $d->{dict}<th>Found In<th>Notes</tr>\n";
    foreach my $row (@{$d->{table}}) {
        print "<tr>";
        my ($w,$f,$fin,$n) = @$row;
        print "<td>$w</td>";
        if ($f) {print "<td>YES</td>"}
        else    {print "<td><font color=\"ff0000\">NO</font></td>"}
        print "<td>$fin</td>";
        print "<td>$n</td>";
        print "</tr>\n";
    }
    print "<table>\n";
    print "<p>\n";
    foreach my $n (sort {$a <=> $b} keys %{$d->{active_notes}}) {
        print "[$n] $notes{$n}<br>\n";
    }
}

sub to_text( $ ) {
    my ($d) = @_;
    print "WORD\tIN $d->{dict}\tFOUND IN\tNOTES\n";
    foreach my $row (@{$d->{table}}) {
        my ($w,$f,$fin,$n) = @$row;
        print "$w\t";
        if ($f) {print "yes\t"}
        else    {print "NO\t"}
        print "$fin\t$n\n";
    }   
    print "---\n";
    foreach my $n (sort {$a <=> $b} keys %{$d->{active_notes}}) {
        print "[$n] $notes{$n}\n";
    }
}

return 1;
