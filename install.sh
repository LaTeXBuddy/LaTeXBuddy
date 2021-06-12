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
packages=(python3-pip git default-jdk curl )

for f in ${!osInfo[@]}
do
    if [[ -f $f ]];then
        package_manager=${osInfo[$f]}
    fi
done

for i in ${packages[@]}
do
   ${package_manager} ${i}
done
