$/ = undef;

open POS, ">pos.txt";
open W  , ">base.txt";

foreach $f (<./*.html>) {
    open IN, $f;
    #next unless $f =~ /^[A-Za-z\']+$/;
    $_ = <IN>;
    close IN;
    ($w) = m~<title>(.+?)</title>~;
    s/<[^>]*>//g;
    %pos = ();
    while (m~ ([^ ]*\W)(pref|suff|n|pl|adj|adv|v|vt|vi|conj|imp|interj)\.~g) {
	my ($a,$b) = ($1,$2);
	next if $a =~ /q\.$/;
	$pos{$b} = 1;
    }
    $pos = "";
    $pos .= "N" if exists $pos{n};
    $pos .= "P" if exists $pos{pl};
    $pos .= "t" if exists $pos{vt};
    $pos .= "i" if exists $pos{vi};
    $pos .= "V" if (exists $pos{v} and not (exists $pos{vt} or exists $pos{vi}));
    $pos .= "V" if exists $pos{imp};
    $pos .= "A" if exists $pos{adj};
    $pos .= "v" if exists $pos{adj};
    $pos .= "C" if exists $pos{conj};
    $pos .= "!" if exists $pos{interj};
    $pos .= "p" if exists $pos{pre};
    $pos .= "s" if exists $pos{suff};
    print W "$w\n";
    print POS "$w\t$pos\n" unless $pos eq '';
}

#n adj vt vi conj adv interj
