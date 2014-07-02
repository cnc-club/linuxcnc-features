#!/usr/bin/env sh

for file in `find -mindepth 2 -name *.po`; do
	msgcat linuxcnc-features.po $file -o $file
done


