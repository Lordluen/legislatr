#!/bin/bash

curl "http://www.senate.gov/legislative/Public_Disclosure/contributions_download.htm" | egrep -o 'http[^"]*.zip' | xargs -P 5 -n 1 wget

for i in *.zip; do
	unzip -o $i
done;

for i in *.xml; do
	iconv -f utf-16 -t utf-8 $i > $i.bak
	mv $i.bak $i
done

rm -rf *.zip
