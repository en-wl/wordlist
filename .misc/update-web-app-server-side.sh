set -v
set -e

cd /opt/app
rm -rf wordlist-old wordlist-tmp
cp -a wordlist/ wordlist-tmp
cd wordlist-tmp/
git reset --hard
git clean -xfd
git pull
git gc --aggressive
make

cd scowl/
sql/create.sh 

cd ../..
mv wordlist wordlist-old
mv wordlist-tmp wordlist 
