#!/bin/bash
declare -A osInfo;
osInfo[/etc/debian_version]="apt-get install -y"
osInfo[/etc/alpine-release]="apk --update add"
osInfo[/etc/centos-release]="yum install -y"
osInfo[/etc/fedora-release]="dnf install -y"
osInfo[/etc/redhat-release]="yum install -y"
osInfo[/etc/arch-release]="pacman -S"
osInfo[/etc/gentoo-release]="emerge"
osInfo[/etc/SuSE-release]="zypper install -y"
# rename apt-get
packages=(python3-pip git default-jdk curl make)
packagesapt=(autoconf automake libtool-bin texinfo autogen autopoint)
packagespacman=(pythonpip)

for f in ${!osInfo[@]}
do
    if [[ -f $f ]];then
        package_manager=${osInfo[$f]}
    fi
done

for i in ${packagesapt[@]}
do
    if [[ $package_manager == "apt" ]]; then
        update="apt update -y"
        ${update}
    fi
    sudo ${package_manager} ${i}
    # echo "${i} not installed!"
done

for i in ${packages[@]}
do
    if [[ $package_manager == "apt-get" ]]; then
        update="apt-get update -y"
        ${update}
    fi
    sudo ${package_manager} ${i}
    # echo "${i} not installed!"
done

pip3 install poetry
python3 -m poetry install

TPATH=$HOME/chktex-1.7.6.tar.gz
TFPATH=chktex-1.7.6
url='http://download.savannah.gnu.org/releases/chktex/chktex-1.7.6.tar.gz'
curl -L $url > $TPATH
tar -xvf $TPATH -C $HOME
cd $HOME/$TFPATH
sudo ./configure
sudo make
sudo make install
sudo make check
sudo echo export PATH="$HOME/$TFPATH/:$PATH" >> ~/.profile
# sudo echo chktex="$HOME/$TFPATH/chktex" >> ~/.bash_profile
# make clean


TARPATH=$HOME/diction-1.14.tar.gz
url=http://www.moria.de/~michael/diction/diction-1.14.tar.gz
curl $url > $TARPATH
tar -xvf $TARPATH -C $HOME
cd $HOME/diction-1.14
sudo ./configure
sudo make
sudo make install
# make clean


# TBD: install in /usr/local ???
TARPATH=$HOME/aspell-master.zip
url=https://github.com/GNUAspell/aspell/archive/refs/heads/master.zip
curl -L $url > $TARPATH
unzip $TARPATH -d $HOME
cd $HOME/aspell-master
sudo ./autogen
sudo ./configure --disable-static
sudo make
# sudo make install
# make clean
# or ./config-opt <options> or ./config-debug <options>


# TARPATH=$HOME/latexbuddy-master.tar.gz
# url=https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/latexbuddy-master.tar.gz
# curl -L $url > $TARPATH
# cd $HOME
# tar -xvf latexbuddy-master.tar.gz

cd $HOME
curl -L https://raw.githubusercontent.com/languagetool-org/languagetool/master/install.sh | sudo bash
cd LanguageTool-5.3-stable
sudo echo export PATH="$HOME/LanguageTool-5.3-stable/languagetool-commandline.jar:$PATH" >> ~/.profile
