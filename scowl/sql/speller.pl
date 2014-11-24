use utf8;
use DBI;

sub deaccent($) {
    local $_ = $_[0];
    # from deaccent-toperl.cc
    tr/ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöøùúûüýÿ/AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuyy/;
    return $_;
}

my $dbh = DBI->connect("dbi:SQLite:dbname=scowl.db","","");
$dbh->{unicode} = 1;
$dbh->{RaiseError} = 1;
$dbh->{AutoCommit} = 0;

$dbh->do("create temp table words_pre as select word,iid,added,accented from speller_words join post using (pid) limit 0");
my $sth = $dbh->prepare("select * from words");
$sth->execute;
my $ins = $dbh->prepare("insert into words_pre (word,iid,added,accented) values (?,?,?,?)");
while (my ($word,$iid) = $sth->fetchrow_array) {
    my $deaccented = deaccent($word);
    if ($word eq $deaccented) {
        $ins->execute($word,$iid,0,0);
    } else {
        $ins->execute($word,$iid,0,1);
        $ins->execute($deaccented,$iid,1,0);
    }
}
$dbh->do("delete from post");
$dbh->do("insert into post (iid,added,accented) select distinct iid,added,accented from words_pre");
$dbh->do("delete from speller_words");

$sth = $dbh->prepare("select word,pid from words_pre join post using(iid,added,accented)");
$sth->execute;
$ins = $dbh->prepare("insert into speller_words (word,word_lower,pid) values (?,?,?)");

while (my ($word,$pid) = $sth->fetchrow_array) {
    $ins->execute($word,lc($word),$pid)
}

$dbh->commit;
$dbh->disconnect;

