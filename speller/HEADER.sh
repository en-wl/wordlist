println() {
    echo "$PREFIX$1"
}

if [ "$SCOWL_VERSION" ] && [ -e $SCOWL/.git ] > /dev/null; then
  println "Version $SCOWL_VERSION"
  println "`git -C $SCOWL log --pretty=format:'%cd [%h]' -n 1 -- . `"
  println
elif [ -e $SCOWL/.git ] > /dev/null; then
  println "`git -C $SCOWL log --pretty=format:'%cd [%h]' -n 1 -- . `"
  println
elif [ "$SCOWL_VERSION" ]; then
  println "Generated from SCOWL Version $SCOWL_VERSION"
  println "`date`"
  println
else
  println "Unknown Version"
  println "`date`"
  println
fi
println "https://wordlist.aspell.net"
println

