orig="`cat`"
if [ "$GIT_COMMIT" = "ae1ccd2695c2ee7d257ebc2a7dc3d3e60ebb11e2" ]
then
  echo "-p 5430d0357d899d3377796744d752c2c1d0e12d0a"
else
  echo $orig
fi


