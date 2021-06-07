#!/bin/bash

BSYS=$(uname -n)
sudo echo $bsys
PYVERSION=$(python --version)


if [$BSYS='ubuntu']
then
  #sudo apt update
  sudo apt install python3-pip
elif [$BSYS='arch']
  #pacman -Syu
  pacman -S python
then
  echo arch
else
  echo OS not Supported!
fi
