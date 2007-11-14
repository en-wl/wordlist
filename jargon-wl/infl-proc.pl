@dontuse = qw(blammoes brainoes functinoes kibozoes mousoes nanoes scannoes thinkoes wangoes);
foreach (@dontuse) {
    $dontuse{$_} = 1;
}

open W, ">extra.lst";

while (<STDIN>) {
    s~/\?~/~g;
    next if /A:/ && /\?/;
    s/\(.+?\~.*?\)//g;
    s/^hang V:.+/hang V: hung  hanging  hangs/;
    print;
    $line = $_;
    foreach (split /[^A-Za-z\']+/, $line) {
	next if /^(N|V|A)$/;
	next if exists $dontuse{$_};
	print W "$_\n";
    }
}
