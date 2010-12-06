use varcon;

my %touse;
foreach my $f (</home/kevina/wordlist-svn/trunk/scowl/final/*.??>) {
    my ($num) = $f =~ /\.\d\d$/ or die;
    next unless $num <= 70;
    open F, $f;
    while (<F>) {
        chop;
        $touse{$_} = 1;
    }
}

my %varcon;
open F, "varcon.txt";
while (<F>) {
    my $line = $_;
    my @w = varcon::get_words($line);
    my $touse = 0;
    foreach (@w) {
        $touse = 1 if $touse{$_};
    }
    next unless $touse;
    foreach (@w) {
        push @{$varcon{$_}}, $line;
    }
}

foreach (sort keys %varcon) {
    my @d = @{$varcon{$_}};
    next unless @d > 1;
    my $i = 0;
    foreach (@d) {
        next if / \| /;
        $i++;
    }
    next unless $i > 0;
    print "$_:\n";
    foreach (@d) {
        print "  $_";
    }
}

foreach (sort keys %varcon) {
    next unless /^(.+)\'s/;
    next if exists $varcon{$1};
    print "$_:\n";
    foreach (@d) {
        print "  $_";
    }
}
