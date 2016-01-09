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

    $dbh->do("create temporary table to_lookup (word, word_lower)");
    my $add_word = $dbh->prepare("insert into to_lookup values (?,?)");
    foreach (@words) {
	my ($word) = /^[ \r\n]*(.*?)[ \r\n]*$/;
        $add_word->execute($word, lc($word));
    }
    $dbh->do("create index to_lookup_idx1 on to_lookup (word)");
    $dbh->do("create index to_lookup_idx2 on to_lookup (word_lower)");

    $dbh->do("insert into to_lookup select distinct l.word, l.word_lower from speller_words l join to_lookup t using (word_lower) where l.word <> t.word");

    $dbh->do("create temporary table res as select *,'f' as note from lookup where dict = ? and word in (select word from to_lookup)", undef, $dict);
    $dbh->do("delete from to_lookup where word in (select word from res)");
    $dbh->do("insert into res ".
             "select l.*,'l' from lookup l, dict_info d where d.dict = ? and word in (select word from to_lookup) and".
             "(not d.US or l.US) and (not d.GBs or l.GBs) and (not d.GBz or l.GBz) and (not d.CA or l.CA) and size < 95", undef, $dict);
    $dbh->do("delete from to_lookup where word in (select word from res)");
    $dbh->do("insert into res ".
             "select *,'o' from lookup where word in (select word from to_lookup) and size < 95");
    $dbh->do("delete from to_lookup where word in (select word from res)");

    $dbh->do("create index res_idx1 on res (word)");
    $dbh->do("create index res_idx2 on res (word_lower)");

    my %active_notes;
    my @table;

    my $get_res = $dbh->prepare("select * from res where word = ?");

    my $other_case = $dbh->prepare("select distinct word from res where word_lower = ? and word <> ?");
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
        my ($word) = @_;
        my $res;

        $get_res->execute($word);
        return $fetch->($get_res);
    };

    my $to_table_row = sub {
        my ($word,$res) = @_;
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
                my $v = $res->[0]{variant};
                push @notes, "level $v variant [v]";
                $active_notes{v} = 1;
            } elsif ($res->[0]{note} eq 'o' && $res->[0]{onum} == $di->{onum}) {
		push @notes, "alternative spelling [va]";
                $active_notes{va} = 1;
	    }
            if ($res->[0]{SP}) {
                push @notes, "found in \"$res->[0]{category}\" list [sl]";
                $active_notes{sl} = 1;
            }
            if ($res->[0]{accented}) {
		unless ($found) {
		    push @notes, "word with diacritic marks [d]";
		    $active_notes{d} = 1;
		}
            } elsif ($res->[0]{added}) {
                push @notes, "word added by removing diacritic marks [dr]";
                $active_notes{dr} = 1;
            }
        }
        return [$word, $found, $found_in, join("; ", @notes)];
    };

    foreach (@words) {
        
	my ($word) = /^[ \r\n]*(.*?)[ \r\n]*$/;
	next if $word eq '';
        $get_res->execute($word);
        my $res = $fetch->($get_res);
        my $row = $to_table_row->($word,$res);
        push @table, $row;
        next if $row->[1];
        $other_case->execute(lc($word),$word);
        my $res2 = $other_case->fetchall_arrayref;
        my @other_cases = map {$_->[0]} @$res2;
        # If all uppercase except all otherwise lowercase the first
        # character and see if that is in the list
        my @others;
        if ($word =~ /^[[:upper:]]/) {
            @others = @other_cases;
        } else {
            my $lower = lcfirst($word);
            @others = grep {$_ eq $lower} @other_cases;
        }
        my $lookup_others = sub {
            my ($others, $notenum) = @_;
            foreach my $w (@$others) {
                $get_res->execute($w);
                my $res = $fetch->($get_res);
                my $row = $to_table_row->($w.($notenum eq '!' ? ' [!]' : ''),$res);
                $row->[3] .= '; ' unless $row->[3] eq '';
                $row->[3] .= "case changed from original word \"$word\"".($notenum eq 'c' ? ' [c]' : '');
                push @table, $row;
                $active_notes{$notenum} = 1;
            }
        };
        $lookup_others->(\@others, 'c');
        $lookup_others->([grep {my $w = $_; not grep {$w eq $_} @others} @other_cases], '!');
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

[v] The word is considered a spelling variant.  To promote consistent
    spelling, only one spelling of a word is generally included in a
    the smaller dictionary.  The larger dictionary lets in common
    variants (level 1).

[va] The word is considered an alternative spelling.  For example
    if the dictionary was "en_US" the word "colour" is an alternative
    spelling for "color".

[sl] This word was found in a special list and may not be considered a
    normal word.

[d] This word has diacritic marks (for example, café).  In the smaller
    dictionary diacritic marks are removed.  In the larger dictionary
    both forms, with and without diacritic marks, are included.

[dr] This word was created by removing diacritic marks (for example,
    café becomes cafe)

[c] The case of the word was changed in a similar manor as if the
    word was looked up in a spellchecker (for example, Swim -> swim,
    IPAD -> iPad, IPad -> iPad).

[!] The case of the word was changed.  The original word was not found
    in the dictionary. 

---
our %notes;
foreach (split /\n\n/, $notes_text) {
    next unless /[^\n ]/;
    /\[([a-z0-9\!]+)\] (.+)/s or die;
    $notes{$1} = $2;
}

sub to_html( $ ; &) {
    my ($d,$header_mod) = (@_);
    print "<table border=1 cellpadding=2>\n";
    {
	local $_ = "<tr><th>Word<th>In $d->{dict}<th>Found In<th>Notes</tr>\n";
	$header_mod->() if defined $header_mod;
	print;
    }
    foreach my $row (@{$d->{table}}) {
        print "<tr>";
        my ($w,$f,$fin,$n,@extra) = @$row;
        print "<td>$w</td>";
        if ($f) {print "<td>YES</td>"}
        else    {print "<td><font color=\"ff0000\">NO</font></td>"}
        print "<td>$fin</td>";
        print "<td>$n</td>";
	foreach my $cell (@extra) {
	    if (ref $cell) {print "<td $cell->[0]>$cell->[1]</td>"}
	    else           {print "<td>$cell</td>"}
	}
        print "</tr>\n";
    }
    print "</table>\n";
    print "<p>\n";
    foreach my $n (sort keys %{$d->{active_notes}}) {
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
    foreach my $n (sort keys %{$d->{active_notes}}) {
        print "[$n] $notes{$n}\n";
    }
}

return 1;
