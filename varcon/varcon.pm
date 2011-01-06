package varcon;

use strict;
use warnings;
use Carp;

#$SIG{__DIE__} = sub {die $_[0] unless defined $^S;
#                     confess $_[0];};

use Exporter ();
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(readline flatten get_words filter %map MAX_VARIANT_LEVEL);

our %map = qw(A american B british Z british_z C canadian _ other);
my %vmap = ('' =>  -1, '.' => 0, 'v' => 1, 'V' => 2, '-' => 3, 'x' => 8,
                       '0' => 0, '1' => 1, '2' => 2, '3' => 3, '8' => 8);
my %rmap = ('' => '', 
            -1 => '', 0 => '.', 1 => 'v', 2 => 'V', 3 => '-', 8 => 'x');

our $MAX_VARIANT_LEVEL = 3; # can be up to 9

sub readline_no_expand($;$) {
    local $_ = shift;
    my $n = shift;
    chomp;
    my ($d,@n) = split / *\| */;
    my (@d) = split / *\/ */, $d;
    my %r;
    foreach (@d) {
        my ($s, $w) = /^(.+?): (.+)$/ or croak "Bad entry: $_";
        my @s = split / /, $s;
        foreach (@s) {
            my ($s, $v) = /^([ABZC_*Q])([.01234vVx-]?)$/ or croak "Bad category: $_";
            push @{$r{$s}[$vmap{$v}+1]}, $w;
        }
    }
    foreach my $s (keys %r) {
        if (defined $r{$s}[0] && @{$r{$s}[0]} > 1) {
            unshift @{$r{$s}[1]}, splice(@{$r{$s}[0]}, 1);
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
        #die "?$k" unless defined $p{$k}[0];
        #my @d = @{$p{$k}[0]};
        #$r{$k} = [shift @d];
        #$r{"${k}0"} = [@d] if @d;
        foreach my $v (-1..$MAX_VARIANT_LEVEL) {
            next unless defined $p{$k}[$v+1];
            my $vs = $v == -1 ? '' : $v;
            $r{"$k$vs"} = $p{$k}[$v+1];
        }
    }
    return %r;
}

sub reverse($) {
    my ($flattened) = @_;
    my %r;
    foreach my $tag (sort keys %$flattened) {
        my $words = $flattened->{$tag};
        foreach my $word (@$words) {
            push @{$r{$word}}, $tag;
        }
    }
    return bless \%r, 'varcon::revered';
}

sub format($) {
    my ($flattened) = @_;
    my $line = '';
    my $reversed = varcon::reverse($flattened);
    my %grouped;
    foreach (sort keys %$flattened) {
        /^(.)(.?)$/ or croak "Bad: $_";
        $grouped{$1} .= "$2:@{$flattened->{$_}} ";
    }
    my %kill;
    $kill{Z} = 1 if defined $grouped{Z} && defined $grouped{B} && $grouped{Z} eq $grouped{B};
    $kill{C} = 1 if defined $grouped{C} && defined $grouped{Z} && $grouped{C} eq $grouped{Z};
    foreach my $key (sort keys %$flattened) {
        my $words = $flattened->{$key};
        foreach my $word (@$words) {
            next unless exists $reversed->{$word};
            my @sps = grep {/^(.)(.?)$/; !$kill{$1}} @{$reversed->{$word}};
            $line .= ' / ' unless $line eq '';
            $line .= join(' ', map {/^(.)(.?)$/; "$1$rmap{$2}"} @sps);
            $line .= ": $word";
            delete $reversed->{$word};
        }
    }
    return $line;
}

sub get_words_set(\%$) {
    my ($res,$r) = @_;
    my $i = 0;
    if (ref $r) {
        foreach my $k (sort keys %$r) {
            local $_ = $r->{$k};
            foreach (@$_) {
                if (ref $_) {
                    foreach (@$_) {
                        $res->{$_} = $i unless exists $res->{$_};
                        $i++;
                    }
                } elsif (defined $_) {
                    $res->{$_} = $i unless exists $res->{$_};
                    $i++;
                }
            }
        }
    } else {
        local $_ = $r;
        chomp;
        my ($d) = split / *\| */;
        my (@d) = split / *\/ */, $d;
        foreach (@d) {
            my ($s, $w) = /^(.+?): (.+)$/ or croak "Bad entry: $_";
            $res->{$w} = $i unless exists $res->{$_};
            $i++;
        }
    }
}

sub get_words($) {
    my %res;
    &get_words_set(\%res, @_);
    return sort {$res{$a} <=> $res{$b}} keys %res;
}

sub filter(\$;$) {
    ${$_[0]} =~ s/^([^#\n]*)(.*)/$1/;
    ${$_[1]} = $2 if defined $_[1] && $2 ne '';
    ${$_[0]} =~ s/\s+$//;
    return 1 if ${$_[0]} eq '';
    return 0;
}
