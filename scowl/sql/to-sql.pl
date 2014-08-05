
my %sp = (                 # A B Z C S  v
    'english'            => [1,1,1,1,0,-1],
    'american'           => [1,0,0,0,0,-1],
    'british'            => [0,1,0,0,0,-1],
    'british_z'          => [0,0,1,0,0,-1],
    'canadian'           => [0,0,0,1,0,-1],
    'special'            => [0,0,0,0,1,-1],
    'british_variant_0'  => [0,1,1,0,0, 0],
    'british_variant_1'  => [0,1,1,0,0, 1],
    'canadian_variant_0' => [0,0,0,1,0, 0],
    'canadian_variant_1' => [0,0,0,1,0, 1],
    'variant_0'          => [1,0,0,0,0, 0],
    'variant_1'          => [1,0,0,0,0, 1],
    'variant_2'          => [1,1,1,1,0, 2]
);

open W, ">working/words.tab";
open L, ">working/lists.tab";

chdir "final";

my $idx = 1;
foreach my $f (<*>) {
    my ($sp,$cat,$sz) = $f =~ /^(.+?)-(.+?)\.(\d\d)$/ or die;
    my @sp = @{$sp{$sp}};
    die unless @sp;
    my @row = ($idx, $sp, @sp, $cat, $sz);
    print L join("\t",@row),"\n";
    open F, "cat $f | iconv -fiso8859-1 -tutf-8 |" or die;
    while (<F>) {
        chomp;
        print W "$_\t$idx\n";
    }
    ++$idx;
}
