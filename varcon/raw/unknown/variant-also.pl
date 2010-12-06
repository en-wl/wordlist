
print "---\n";

sub push_uniq (\@$) {
    my $ref = shift;
    push @$ref, $_[0] unless grep {$_ eq $_[0]} @$ref;
}

sub closure (@)
{
    my @res = @_;
    my @todo = @_;
    while (@todo) {
        $word = shift @todo;
        my @w = @{$words{$word}[0]};
        foreach my $w (@w) {
            next if grep {$w eq $_} @res;
            push @res, $w;
            push @todo, $w;
        }
    }
    my $ref = [\@res];
    foreach (@res) {
        $words{$_} = $ref;
    }
    return @res;
}

open F, "variant-plus.txt";

sub proc ($) {
    local $_ = $_[0];
    ($note, $data, $info) = /^(b:|\?|-b |-|)\s*(\w.+?)\s*(\|.*)?$/ or die "?$_";
    local $_ = $data;
    my @v;
    s/^(\w\S+)\s*// or die "?$_";    push @v, $1;
    my $prev;
    while ($prev ne $_) {
        $prev = $_;
        while (s/^\/\s*(\w\S+)\s*//)     {push @v, $1}
        while (s/^\/\/\s*(\w\S+)\s*//)   {push @v, $1}
        while (s/^\((\w\S+)\)\s*//)      {push @v, $1}
        while (s/^\(\((\w\S+)\)\)\s*//)  {push @v, $1}
    }
    die "?$_" unless $_ eq '';
    return @v;
}

my @extra;

while (<F>) {
    next if m/^NOTE:/;
    next if m/^\s*$/;
    next if m/^===/;
    chop;
    @v = proc $_;
    closure @v;
    push @extra, [$v[0], "PLUS: $_\n"];
}

open F, "variant-infl.tab";
while (<F>) {
    chop;
    my @v = split /\t/;
    closure @v;
    push @extra, [$v[0], "INFL: ".join(' / ', @v)."\n"];
}


open F, "varcon.txt";

while (<F>) {
    my ($d) = split / *\| */;
    my (@d) = split / *\/ */, $d;
    @l = map {/^.+?: (.+)/; $1} @d;
    closure @l;
    push @extra, [$l[0], "VARCON: $_"];
}

foreach (@extra) {
    $words{$_->[0]}[1] .= $_->[1];
}

#my %prev;
#foreach my $w (sort keys %words) {
#    my $d = $words{$w};
#    next if $prev{scalar $d};
#    $prev{scalar $d} = 1;
#    print join('  ', @{$d->[0]}), "\n";
#}

open F, "variant-also.tab";
while (<F>) {
    chop;
    my @v = split /\t/;
    @v = grep {/\w/} @v;
    @v2 = grep {!defined $words{$_}} @v;
    if (@v2) {
        #print ">>@v -- @v2\n";
        push @new, [@v];
    }
    closure @v;
}

open F, "<:crlf", "/home/kevina/wordlist-svn/trunk/12d5/2+2lemma.txt";
$_ = <F>;
while (defined $_) {
    chomp;
    my $l = "LEMMA: $_:";
    s/ -> \[[^\]]+\]//g;
    s/\+//g;
    my $headword = $_;
    $_ = <F>;
    chomp;
    $l .= "$_\n";
    $l =~ s/:\s+/: /g;
    s/ -> \[[^\]]+\]//g;
    /^\s+(.+)/ or next;
    $_ = $1;
    my (@words) = ($headword, split /,\s*/, $_);
    #print ">>", join ('//', @words), "\n";
    @words = closure @words;
    push @extra, [$words[0], $l];
    #print join ('//', @words), "\n";
    $_ = <F>;
}

foreach (@extra) {
    $words{$_->[0]}[2] .= $_->[1];
}

foreach (@new) {
    push @{$words{$_->[0]}[1]}, $_;
}

my %prev;
foreach my $w (sort keys %words) {
    my $d = $words{$w};
    next if $prev{scalar $d};
    $prev{scalar $d} = 1;
    next unless defined @{$d->[1]};
    foreach (@{$d->[1]}) {
        print "?".join(' / ', @$_), "\n";
    }
    print $d->[2];
    print "\n";
}

