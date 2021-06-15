#!/bin/bash
declare -A osInfo;
osInfo[/etc/debian_version]="apt-get install -y"
osInfo[/etc/alpine-release]="apk --update add"
osInfo[/etc/centos-release]="yum install -y"
osInfo[/etc/fedora-release]="dnf install -y"
osInfo[/etc/redhat-release]="yum install -y"
osInfo[/etc/arch-release]="pacman -U"
osInfo[/etc/gentoo-release]="emerge"
osInfo[/etc/SuSE-release]="zypper install -y"
packages=(python3-pip git default-jdk curl make)
packagesapt=(autoconf automake libtool-bin texinfo)

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
    ${package_manager} ${i}
done

for i in ${packages[@]}
do
    if [[ $package_manager == "apt-get" ]]; then
        update="apt-get update -y"
        ${update}
    fi
    ${package_manager} ${i}
done

TPATH=$HOME/chktex-1.7.6.tar.gz
FPATH=$HOME/chktex
url='http://download.savannah.gnu.org/releases/chktex/chktex-1.7.6.tar.gz'
curl -L $url > TPATH
cd $HOME
tar -xvf chktex-1.7.6.tar.gz -C /home/ub
cd $HOME/chktex-1.7.6/
sudo ./configure --prefix ~/
sudo make
sudo make install
sudo make check
make clean


TARPATH=$HOME/diction-1.14.tar.gz
FPATH=$HOME/diction
url=http://ftp.gnu.org/gnu/diction/diction-1.11.tar.gz
curl $url > $TARPATH
cd $HOME
tar -xvf diction-1.14.tar.gz
cd diction-1.11
sudo ./configure
sudo make
sudo make install
make clean

TARPATH=$HOME/aspell-master.zip
FPATH=$HOME/aspell
url=https://github.com/GNUAspell/aspell/aspell-master.zip
curl $url > $TARPATH
cd $HOME
gunzip aspell-master.zip
./autogen
./configure --disable-static
make
make install
make clean
# or ./config-opt <options> or ./config-debug <options>


TARPATH=$HOME/latexbuddy-master.tar.gz
FPATH=$HOME/latexbuddy
url=https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/latexbuddy-master.tar.gz
curl $url > $TARPATH
cd $HOME
tar -xvf latexbuddy-master.tar.gz

cd $HOME/LanguageTool
curl -L https://raw.githubusercontent.com/languagetool-org/languagetool/master/install.sh | sudo bash
