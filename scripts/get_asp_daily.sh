#! /bin/bash

# make directory for software/asp
dir=~/third-party-tools/asp/
if [ ! -d $dir ] ; then
  mkdir -pv $dir
fi
cd $dir

# grab latest tarball
wget -r -l1 --no-check-certificate --no-directories --no-parent -Ax86_64-Linux.tar.bz2 http://byss.arc.nasa.gov/stereopipeline/daily_build/

# get tarball name, extract and remove
tarball=$(ls -t *x86_64-Linux.tar.bz2 | head -1 )
tar -jvxf $tarball
rm $tarball

# backup previously downloaded version
if [ -d $dir/StereoPipeline ] ; then
  rm -rf $dir/StereoPipeline_previous
  mv $dir/StereoPipeline $dir/StereoPipeline_previous
fi

# rename current version to match executable path in .bash_profile or .bashrc. E.g. export PATH="$HOME/sw/asp/StereoPipeline/bin:$PATH"
mv $dir/StereoPipeline*Linux $dir/StereoPipeline

