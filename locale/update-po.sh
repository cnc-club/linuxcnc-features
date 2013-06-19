#!/usr/bin/env sh

for file in `find -name *.po -mindepth 2`; do
	msgmerge $file messages.po -U
done


