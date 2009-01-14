package varcon;

use strict;
use warnings;

use Exporter ();
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(readline flatten %map);

our %map = qw(A american B british Z british_z C canadian);
my %vmap = ('' => 0, 'v' => 1, 'V' => 2, '-' => 3);

sub readline($) {
    local $_ = shift;
    chomp;
    my ($d) = split / *\| */;
    my (@d) = split / *\/ */, $d;
    my %r;
    foreach (@d) {
        my ($s, $w) = /^(.+?): (.+)$/ or die "Bad entry: $_";
        my @s = split / /, $s;
        foreach (@s) {
            my ($s, $v) = /^([ABZC])([vV-]?)$/ or die;
            push @{$r{$s}[$vmap{$v}]}, $w;
        }
    }
    $r{Z} = $r{B} unless exists $r{Z};
    $r{C} = $r{Z} unless exists $r{C};
    return %r;
}

sub flatten(%) {
    my %p = @_;
    my %r;
    foreach my $k (keys %p) {
        foreach my $v (0..3) {
            next unless defined $p{$k}[$v];
            $r{"$k$v"} = $p{$k}[$v];
        }
    }
    return %r;
}


