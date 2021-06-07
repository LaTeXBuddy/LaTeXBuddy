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
else
  echo OS not Supported!
fi

echo Done!
