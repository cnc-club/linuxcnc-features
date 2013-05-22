#!/usr/bin/env python
# coding: utf-8
#
# Copyright (c) 2012 Nick Drobchenko aka Nick from cnc-club.ru
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import sys

import pygtk
pygtk.require('2.0')

import gtk
import gtk.glade
from lxml import etree
import time
import gobject

import ConfigParser
import re, os
import  pango

if len(sys.argv)>1:
	w =  sys.argv[1]
else :
	w = 28	
xml = etree.parse("icons.svg")
#print etree.tostring(xml, pretty_print=True)
for x in xml.findall(".//{http://www.w3.org/2000/svg}title") :
	s = "inkscape icons.svg --export-png=subroutines/icons/%s.png --export-id-only --export-id=%s --export-area-snap --export-width=%spx"%(x.text,x.getparent().get("id"),w) 
	os.popen(s)
	print s
	print
	

