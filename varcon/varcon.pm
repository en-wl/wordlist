package varcon;

use strict;
use warnings;

use Exporter ();
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(readline flatten get_words %map);

our %map = qw(A american B british Z british_z C canadian _ other);
my %vmap = ('' => 0, 'v' => 1, 'V' => 2, '-' => 3,
            '0' => 0, '1' => 1, '2' => 2, '3' => 3);

sub readline_no_expand($;$) {
    local $_ = shift;
    my $n = shift;
    chomp;
    my ($d,@n) = split / *\| */;
    my (@d) = split / *\/ */, $d;
    my %r;
    foreach (@d) {
        my ($s, $w) = /^(.+?): (.+)$/ or die "Bad entry: $_";
        my @s = split / /, $s;
        foreach (@s) {
            my ($s, $v) = /^([ABZC_])([01234vV-]?)$/ or die "Bad category: $_";
            push @{$r{$s}[$vmap{$v}]}, $w;
        }
    }
    die if @n > 1;
    if (@n == 1 && defined $n) {
        local $_ = $n[0];
        $n->{_} = $_;
        $n->{uncommon} = 1 if s/^ *\(-\)//;
        $n->{pos} = $1 if s/^ *<(.+?)>//;
        s/^ *//;
        $n->{note} = $_;
    }
    return %r;
}

sub readline($;$) {
    my %r = &readline_no_expand(@_);
    $r{Z} = $r{B} if exists $r{B} and not exists $r{Z};
    $r{C} = $r{Z} if exists $r{Z} and not exists $r{C};
    return %r;
}

sub flatten(%) {
    my %p = @_;
    my %r;
    foreach my $k (keys %p) {
        next unless defined $p{$k};
        die "?$k" unless defined $p{$k}[0];
        my @d = @{$p{$k}[0]};
        $r{$k} = [shift @d];
        $r{"${k}0"} = [@d] if @d;
        foreach my $v (1..3) {
            next unless defined $p{$k}[$v];
            $r{"$k$v"} = $p{$k}[$v];
        }
    }
    return %r;
}

sub get_words_tally($) {
    my $r = shift;
    my %res;
    if (ref $r) {
        foreach (values %$r) {
            foreach (@$_) {
                if (ref $_) {
                    foreach (@$_) {
                        $res{$_} = 1;
                    }
                } elsif (defined $_) {
                    $res{$_} = 1;
                }
            }
        }
    } else {
        local $_ = $r;
        chomp;
        my ($d) = split / *\| */;
        my (@d) = split / *\/ */, $d;
        foreach (@d) {
            my ($s, $w) = /^(.+?): (.+)$/ or die "Bad entry: $_";
            $res{$w} = 1;
        }
    }
    return \%res;
}

sub get_words($) {
    my $res = &get_words_tally(@_);
    return sort keys %$res;
}
