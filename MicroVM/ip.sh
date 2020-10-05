#!/bin/sh

echo "Setting ip ----"
network_device()
{

cat /proc/net/dev | grep : | grep -v lo: | cut -d : -f 1 | tr -d " " | head -n 1
}

ifconfig `network_device` up
/sbin/dhclient `network_device`
