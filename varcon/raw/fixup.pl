
# Change entries with just A to +

while (<>) {
    my $orig_line = $_;
    chomp;
    @entries = split / \/ /;
    my $amer_only = 1;
    foreach (@entries) {
        s/^A(.?:)/\_$1/ or $amer_only = 0;
    }
    if ($amer_only) {
        print join(' / ', @entries), "\n";
    } else {
        print $orig_line;
    }
}
