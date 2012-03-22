#!/bin/bash

if [ $# -lt 1 ]
then
	echo "Please provide <name-of-usb-stick>"
	exit
fi
echo "rsyncing files..."
/usr/bin/rsync -av /media/$1/.ssh /home/olpc/
/bin/sleep 1
/bin/chmod 600 /home/olpc/.ssh/id_rsa
/bin/chmod 444 /home/olpc/.ssh/id_rsa.pub
/bin/chmod 644 /home/olpc/.ssh/authorized_keys




