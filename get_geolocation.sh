#!/bin/sh

os=$(uname -s)
if [ "$os" = "Darwin" ]; then
	if ! command -v gsed >/dev/null 2>&1 ;	then
		echo Running on MacOS, but gsed is not installed
		exit 1
	fi
fi

ip=$(curl -s https://ipinfo.io/ip)
# echo $ip

json=$(curl -s "https://api.iplocation.net/?cmd=ip-country&ip=$ip")
# echo $json

if [ "$os" = "Darwin" ]; then
	country=$(echo $json | gsed 's/^.*\"country_name\":\"\(\w*\)\".*$/\1/')
else
	country=$(echo $json | sed 's/^.*\"country_name\":\"\(\w*\)\".*$/\1/')
fi
echo $ip $country
