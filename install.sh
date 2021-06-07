#!/bin/bash

BSYS=$(uname -n)
sudo echo $bsys
PYVERSION=$(python3 --version)


if [ $BSYS='ubuntu' ]
then
  #sudo apt update
  sudo apt install python3-pip
  sudo pip3 install poetry
  poetry install
elif [ $BSYS='arch' ]
then
  echo arch
  #pacman -Syu
  pacman -S python
elif[ $BSYS='redhat']
then
  sudo yum install python37
elif[ $SYSB='suse']
then
    sudo zypper install python3-3.7
else
  echo 'OS not supported!'
fi

echo Done!
