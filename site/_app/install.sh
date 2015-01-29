
install() {
  name=$1
  bn=`basename $1 .cgi`
  if [ -e /opt/app/cgi/$bn.bk ]; then
    echo "/opt/app/cgi/$bn.bk exists, please remove it first"
    exit 1
  fi
  mv /opt/app/cgi/$bn /opt/app/cgi/$bn.bk
  echo "Installing $name"  
  cp $name /opt/app/cgi/$bn 
  chmod 755 /opt/app/cgi/$bn 
}

install lookup.cgi
install create.cgi
install lookup-freq.cgi
