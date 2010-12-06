
open F, "<:crlf", "/home/kevina/wordlist-svn/trunk/12d5/2+2lemma.txt";

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

$_ = <F>;
while (defined $_) {
    chomp;
    s/ -> \[[^\]]+\]//g;
    s/\+//g;
    my $headword = $_;
    $_ = <F>;
    s/ -> \[[^\]]+\]//g;
    /^\s+(.+)/ or next;
    $_ = $1;
    my (@words) = ($headword, split /,\s*/, $_);
    #print ">>", join ('//', @words), "\n";
    @words = closure @words;
    #print join ('//', @words), "\n";
    $_ = <F>;
}

open F, "variant-plus.txt" or die;

#while (<F>) {
#    last if /^---/;
#}

sub proc ($) {
    local $_ = $_[0];
    ($note, $data, $info) = /^(b:|\?|-b |-|)\s*(\w.+?)\s*(\|.+)?$/ or die "?$_";
    local $_ = $data;
    my @v;
    s/^(\w\S+)\s*// or die "?$_";    push @v, [0, $1];
    while (s/^\/\s*(\w\S+)\s*//)    {push @v, [1, $1]}
    while (s/^\/\/\s*(\w\S+)\s*//)  {push @v, [1, $1]}
    while (s/^\((\w\S+)\)\s*//)     {push @v, [2, $1]}
    while (s/^\(\((\w\S+)\)\)\s*//) {push @v, [3, $1]}
    return @v;
}

while (<F>) {
    next if m/^NOTE:/;
    next if m/^\s*$/;
    chop;
    push @var_data, $_;
    next if m/^===/;
    @v = proc $_;
    my @d = map {$_->[1]} @v;
    foreach (@d) {
        push @d, $1 if /^(.+)\'s$/
    }
    @res = closure @d;
    #print join (' :: ', @res), "\n";
}

foreach (@var_data) {
    if (m/^=== (\S+)/) {
        push_uniq @{$words{$1}[1]}, $_;
    } else {
        @v = map {$_->[1]} proc $_;
        push_uniq @{$words{$v[0]}[1]}, $_;
    }
}

my %prev;
foreach my $w (sort keys %words) {
    my $d = $words{$w};
    next if $prev{scalar $d};
    $prev{scalar $d} = 1;
    next unless $d->[1];
    #use Data::Dumper;
    #print Dumper($_);
    local $_ = join ('', map {"$_\n"} @{$d->[1]});
    print $_;
    print "NOTE: ", join (' ', @{$d->[0]}), "\n" if m/^\?/m || m/^===/m || m/^-/m;
    print "\n";
}
