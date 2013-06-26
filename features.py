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
import getopt
import linuxcnc
import subprocess
from threading import Timer
from copy import deepcopy 
import io
from cStringIO import StringIO

import gettext

if os.path.exists('./locale/linuxcnc-features.po') :
	gettext.install('linuxcnc-features', './locale', unicode=True)
else :
	gettext.install('linuxcnc-features', None, unicode=True)


PARAMETERS = ["string", "float", "int", "image", "bool"]	
FEATURES = ["feature"]
GROUPS = ["group"]
UNDO_MAX_LEN = 200
ADD_ICON_SIZE = 60
UNIQUE_ID = [10000]
INCLUDE = []

def get_int(s) :
	try :
		return int(s)
	except :
		return 0	

PIXBUF_DICT = {}
FEATURE_DICT = {}


def search_path(path, f) :
	for s in path.split(":") :
		if os.path.isfile(s+"/"+f) :
			return s+"/"+f
	return None		
		

def get_pixbuf(icon) :
	if icon != "" and icon != None :
		if icon not in PIXBUF_DICT :
			try :
				PIXBUF_DICT[icon] = gtk.gdk.pixbuf_new_from_file( search_path(SUBROUTINES_PATH,icon) ) 
			except Exception, e:
				PIXBUF_DICT[icon] = None 
				print _("Warning! Failed to load catalog icon from: %(icon)s at path %(path)s!") % {"icon":icon, "path":SUBROUTINES_PATH}
		pixbuf = PIXBUF_DICT[icon]
		return PIXBUF_DICT[icon]
	else :
		return None

class Parameter() :
	def __init__(self, ini=None, ini_id = None, xml=None) :
		self.attr = {}
		self.pixbuf = {}
		if ini != None : self.from_ini(ini, ini_id)
		if xml != None : self.from_xml(xml)

	def __repr__(self) :
		return etree.tostring(self.to_xml(), pretty_print=True)

	def from_ini(self,ini, ini_id)	:
		self.attr = {}
		ini = dict(ini)
		for i in ini :
			self.attr[i] = ini[i]
		if "type" in self.attr : self.attr["type"] = self.attr["type"].lower()
		if "call" not in self.attr : self.attr["call"] = "#"+ini_id.lower()
		self.id = ini_id
		
	def from_xml(self, xml) :
		for i in xml.keys() :
			self.attr[i] = xml.get(i)

		
	def to_xml(self) : 
		xml = etree.Element("param")
		for i in self.attr :
			xml.set(i, unicode(str(self.attr[i])))
		return xml
		
	def get_icon(self) : return get_pixbuf(self.get_attr("icon"))

	def get_image(self) : return get_pixbuf(self.get_attr("image"))

	def get_value(self, ptype) :
		if self.attr["type"] in ptype :
			return self.attr["value"] if "value" in self.attr else ""

	def get_name(self) :
		return _(self.attr["name"] if "name" in self.attr else "")
	
	def get_attr(self, name) :
		return self.attr[name] if name in self.attr else None
		
		
class Feature():
	def __init__(self, src=None, xml = None) :
		self.attr = {}
		self.pixbuf = {}
		self.param = []		
		if src != None :
			self.from_src(src)
		if xml != None :
			self.from_xml(xml)
		
		
		
	def __repr__(self) :
		return etree.tostring(self.to_xml(), pretty_print=True)
		
	def copy() :
		f = Feature()
		for i in self.attr :
			f.attr = self.attr	
		for p in self.param :
			f.param.append(self.param)
		for i in self.pixbuf :
			f.pixbuf[i] = self.pixbuf[i]
		return f

	
	def get_icon(self) : return get_pixbuf(self.get_attr("icon"))
	def get_image(self) : return get_pixbuf(self.get_attr("image"))

	def get_value(self, ptype):
		return self.attr["value"] if "value" in self.attr else ""
	
	def get_attr(self, attr) :
		return self.attr[attr] if attr in self.attr else None
	
	
	def get_name(self):
		return _(self.attr["name"] if "name" in self.attr else "")
		
	def from_src(self, src) :
		if src in  FEATURE_DICT : self.from_xml(FEATURE_DICT[src])
		config = ConfigParser.ConfigParser()
		path_src = search_path(SUBROUTINES_PATH,src) 
		if path_src == None :
			print _("Feature ini file %(src)s not found in %(path)s!")%{"src":src,"path":SUBROUTINES_PATH}
			raise IOError, "File not found"

		f = open(path_src).read()
		# add "." in the begining of multiline parameters to save indents
		f = re.sub(r"(?m)^(\ |\t)",r"\1.",f)
		config.readfp(io.BytesIO(f))
		# remove "." in the begining of multiline parameters to save indents
		conf = {}
		for section in config.sections() :
			conf[section] = {}
			for item in config.options(section) :
				s = config.get(section,item, raw=True)
				s = re.sub(r"(?m)^\.","", " "+s)[1:] 
				conf[section][item] = s
		self.attr = conf["SUBROUTINE"]

		self.attr["src"] = src
		if "type" not in self.attr : 
			self.attr["type"] = self.attr["name"]
		
		# get order
		if "order" not in self.attr :
			self.attr["order"] = []
		else :
			self.attr["order"] = self.attr["order"].upper().split()
		self.attr["order"] = [s if s[:6]=="PARAM_" else "PARAM_"+s for s in self.attr["order"]]		 

		# get params
		self.param = []
		parameters = self.attr["order"] + [p for p in conf if (p[:6]=="PARAM_" and p not in self.attr["order"])]
		for s in parameters :
			if s in conf :
				p = Parameter(ini=conf[s], ini_id=s.lower())
				self.param.append(p)
		
		# get gcode parameters		
		for l in ["definitions","before","call","after"] :
			l = l.upper()
			if l in conf and "content" in conf[l] :	
				self.attr[l.lower()] = re.sub(r"(?m)\r?\n\r?\.","\n",conf[l]["content"])
			else : 
				self.attr[l.lower()] = ""

		#print etree.tostring(self.to_xml(), pretty_print=True)
		if self.attr["src"] not in 	FEATURE_DICT : FEATURE_DICT[self.attr["src"]] = self.to_xml()
	
	
	def from_xml(self, xml) :
		self.attr = {}
		for i in xml.keys() :
			self.attr[i] = xml.get(i)

		self.param = []
		for p in xml :
			self.param.append(Parameter(xml = p))
				
	def to_xml(self) :
		xml = etree.Element("feature")
		for i in self.attr :
			xml.set(i, unicode(str(self.attr[i])))

		for p in self.param :
			xml.append(p.to_xml())

		return xml	


	def get_id(self, xml) :
		num = 1		
		if xml!=None :
			# get smallest free name 
			l = xml.findall(".//feature[@type='%s']"%self.attr["type"])		
			num = max([ get_int(i.get("name")[-4:]) for i in l ]+[0])+1
		self.attr["name"] = self.attr["type"]+" %04d"%num
		self.attr["id"] = re.sub("[^a-zA-Z0-9\-]","-",self.attr["name"])
		
	def get_definitions(self) :
		global DEFINITIONS
		if self.attr["type"] not in DEFINITIONS : 	
			s = self.process(self.attr["definitions"])
			if s != "" :
				DEFINITIONS.append(self.attr["type"])
			return s+"\n"
		else :
			return ""

	def include(self, src) :
		f = open(search_path(SUBROUTINES_PATH,src))
		s = f.read()
		f.close()
		return s

	def include_once(self, src) :
		global INCLUDE
		if src not in INCLUDE : 
			INCLUDE.append(src)
			return self.include(src)
		return ""	

	def get_param_value(self, call) :
		call = "#"+call.lower()
		for p in self.param :
			if "call" in p.attr and "value" in p.attr :
				if call == p.attr["call"] :
					return p.attr['value']
		return None
				
	def process(self, s) :
		def eval_callback(m) :
			return str( eval(m.group(2), {"self":self}) )
			
		def exec_callback(m) :
			s = m.group(2) 
			
			#strip starting spaces 
			s = s.replace("\t","    ")
			i = 1e10
			for l in s.split("\n") : 
				if l.strip() != "" :
					i = min(i, len(l)-len(l.lstrip()))
			if i<1e10 :
				res = "" 	
				for l in s.split("\n") : 	
					res += l[i:]+"\n"
				s = res			

			old_stdout = sys.stdout
			redirected_output = StringIO()
			sys.stdout = redirected_output
			exec(s) in {"self":self}
			sys.stdout = old_stdout			
			redirected_output.reset()
			out = str(redirected_output.read())
			return out
		
		def import_callback(m) :
			fname = m.group(2)
			f = search_path(SUBROUTINES_PATH, fname)
			if f != None :
				return str( open(f).read() )
			else :
				print _("Error! Can not find file %(file)s in %(path)s, wile processing <import> tag in feature!")%{"file":fname, "path":SUBROUTINES_PATH}
				raise IOError, "File not found"

			
		s = re.sub(r"(?i)(<import>(.*?)</import>)", import_callback, s)
		s = re.sub(r"(?i)(<eval>(.*?)</eval>)", eval_callback, s)
		s = re.sub(r"(?ims)(<exec>(.*?)</exec>)", exec_callback, s)
		
		for p in self.param :
			if "call" in p.attr and "value" in p.attr :
				s = re.sub( r"%s([^A-Za-z0-9_]|$)" % (re.escape(p.attr["call"])), r"%s\1" % (p.attr["value"]), s)
				
		s = re.sub(r"#self_id","%s"%self.get_attr("id"), s)

		return s
	
	
	
	def get_unique_id(self) :
		id = max(UNIQUE_ID)+1 
		UNIQUE_ID.append(id)
		return id
	
class Features(gtk.VBox):
	__gtype_name__ = "Features"
	__gproperties__ = {}
	__gproperties = __gproperties__ 
	
	def __init__(self, *a, **kw):
		self.linuxcnc = linuxcnc.command()
		
		settings = gtk.settings_get_default()
		settings.props.gtk_button_images = True

		opt, optl = 'U:c:x:i:t', ["catalog=","ini="]
		optlist, args = getopt.getopt(sys.argv[1:], opt, optl)
		optlist = dict(optlist)
		if "-U" in optlist :
			optlist_, args = getopt.getopt(optlist["-U"].split(), opt, optl)
			optlist.update(optlist_)
		self.catalog_src = "catalogs/catalog.xml"
	
		if "-t" in optlist : 
			# get translations and exit
			self.get_translations()
			sys.exit()

		if "--catalog" in optlist :
			self.catalog_src = optlist["--catalog"]
		ini = os.getenv("INI_FILE_NAME")
		if "-i" in optlist : 
			ini = optlist["-i"]
		if "--ini" in optlist : 
			ini = optlist["--ini"]
				
		global SUBROUTINES_PATH
		SUBROUTINES_PATH = ""
		global PROGRAM_PREFIX
		PROGRAM_PREFIX = ""
		try : 
			inifile = linuxcnc.ini(ini)
			SUBROUTINES_PATH = inifile.find('RS274NGC', 'SUBROUTINE_PATH') or ""
			PROGRAM_PREFIX = inifile.find('DISPLAY', 'PROGRAM_PREFIX') or ""
		except :
			print _("Warning! Problem while loading ini file!")
			
		self.config_src = "" 
		if ini!="" and ini!=None :
			self.config_src = os.path.dirname(ini)
		self.config_src += "/features.ini"
		print self.config_src
		self.config = ConfigParser.ConfigParser()
		self.config.read(self.config_src)
		
		if len(SUBROUTINES_PATH)>0 and SUBROUTINES_PATH[-1]!=":" : SUBROUTINES_PATH+=":"
		SUBROUTINES_PATH +=  os.path.abspath(os.path.dirname(__file__))+"/subroutines:"
		self.file_dialogs_folder = SUBROUTINES_PATH.split(":")[0]
		
		gtk.VBox.__init__(self, *a, **kw)
		self.undo_list = []
		self.undo_pointer = 0
		self.glade = gtk.Builder()
		self.glade.add_from_file(os.path.join(os.path.abspath(os.path.dirname(__file__)), "features.glade"))
		self.main_box = self.glade.get_object("FeaturesBox")
		self.glade.connect_signals(self)
		self.timeout = None
		# create features catalog
		if search_path(SUBROUTINES_PATH, self.catalog_src) == None :
			print _("Error! Fatal! Cannot find features catalog %(src)s at %(path)s!") % {"src":self.catalog_src , "path":SUBROUTINES_PATH}
			sys.exit()
		self.catalog_src = search_path(SUBROUTINES_PATH, self.catalog_src)
		xml = etree.parse(self.catalog_src)
		
		self.catalog = xml.getroot()
		self.catalog_path = self.catalog
		
		self.add_iconview = gtk.IconView()		
		self.icon_store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, int)
		self.add_iconview.set_model(self.icon_store)
		self.add_iconview.set_pixbuf_column(0)
		self.add_iconview.set_text_column(1)
		self.add_iconview.connect("item-activated", self.catalog_activate)

		self.update_catalog(xml=self.catalog_path)
		parent = self.main_box.get_toplevel()
		self.add_dialog = gtk.Dialog(_("Add feature"), parent, gtk.RESPONSE_CANCEL or gtk.DIALOG_MODAL, (gtk.STOCK_CLOSE,gtk.RESPONSE_REJECT))
		
		self.add_dialog.set_transient_for(parent)
		scroll = gtk.ScrolledWindow()
		scroll.add_with_viewport(self.add_iconview)
		self.add_dialog.vbox.pack_start(scroll)

		hbox = gtk.HBox()
		button = gtk.Button(_("Catalog root"))
		button.connect("clicked", self.update_catalog, self.catalog)
		hbox.pack_start(button)		
		button = gtk.Button(_("Upper level"))
		button.connect("clicked", self.update_catalog, "parent")
		hbox.pack_start(button)		
		self.add_dialog.vbox.pack_start(hbox, False)
		
		self.add_dialog.show_all()
		self.add_dialog.set_size_request(600,500)
		self.add_dialog.hide()
	
		self.get_features()

		# setup topfeatures toolbar		
		try :
			topfeatures = self.config.get("VAR","topfeatures", raw=True)
		except :
			topfeatures = "" 
		self.ini = {
			"top-features": 3,
			"last-features": 10
		}
		
		for i in self.ini:
			try :			
				s = self.config.get("FEATURES",i.lower(), raw=True)
				self.ini[i] = int(s)
			except :		
				pass
		topfeatures = topfeatures.split("\n")
		self.topfeatures_dict = {}
		for s in topfeatures :
			s = s.split("\t")
			if len(s)==3 :
				self.topfeatures_dict[s[0]] = [int(s[1]), float(s[2])]
		
			
		feature_list = [s.get("sub") for s in self.catalog.findall(".//sub") if "sub" in s.keys()]
		self.topfeatures_toolbar = self.glade.get_object("topfeatures")
		self.block_toptoolbar = False
		#self.topfeatures_toolbar.connect("expose-event", self.block_expose)
		self.topfeatures = {}
		self.topfeatures_buttons = {}
		self.topfeatures_topbuttons = {}
		
		for src in feature_list :
			try :
				f = Feature(src)
				icon = gtk.Image() # icon widget
				icon.set_from_pixbuf(f.get_icon())
				button = gtk.ToolButton(icon, label=_(f.get_attr("name")))
				button.set_tooltip_markup(_(f.get_attr("name")))
				button.connect("clicked", self.topfeatures_click, src)
				self.topfeatures_buttons[src] = button
				
				icon = gtk.Image() # icon widget
				icon.set_from_pixbuf(f.get_icon())
				button1 = gtk.ToolButton(icon, label=_(f.get_attr("name")))
				button1.set_tooltip_markup(_(f.get_attr("name")))
				button1.connect("clicked", self.topfeatures_click, src)
				self.topfeatures_topbuttons[src] = button1
				
				self.topfeatures[src] = [button,button1,0,0]
				if src in self.topfeatures_dict :
					self.topfeatures[src][2:] = self.topfeatures_dict[src]
			except :
				pass
		self.topfeatures_update()

   		
		self.help_viewport = self.glade.get_object("help_viewport")
   		self.help_image = self.glade.get_object("feature_image")	
   		self.help_text = self.glade.get_object("feature_help")	
		
		 
		#self.add_container = self.glade.get_object("add_feature_container")	
		#self.add_container.add_with_viewport(self.add_iconview)
		
		# create treeview
		self.treeview = self.glade.get_object("treeview1")
		self.treestore = gtk.TreeStore(object, str)
		self.treeview.set_model(self.treestore)
		self.treeview.set_tooltip_column(1)

		self.cols = {}
		col =  gtk.TreeViewColumn(_("Name"))
		# icons
		cell = gtk.CellRendererPixbuf()
		col.pack_start(cell, expand=False)
		col.set_cell_data_func(cell, self.get_col_icon)
		# name
		cell = gtk.CellRendererText() 
		col.pack_start(cell, expand=False)
		col.set_cell_data_func(cell, self.get_col_name)
		col.set_resizable(True)
		self.treeview.append_column(col)
		self.cols["name"] = col
		
		# value
		col =  gtk.TreeViewColumn(_("Value"))
		cell = gtk.CellRendererText() 
		cell.set_property("editable",True)
		cell.connect('edited', self.edit_value)		
		col.pack_start(cell, expand=False)
		col.set_cell_data_func(cell, self.get_col_value, ["string","float","int", "bool"])
		self.cell_value = cell
		self.col_value	= col
		
		col.set_resizable(True)		
		self.treeview.append_column(col)
		self.cols["value"] = col
		
		self.treeview.connect("cursor-changed", self.show_help, self.treeview)
		self.treeview.connect('key_press_event' , self.treeview_keypress)
		self.treeview.connect("key-release-event" , self.treeview_release)

		button = self.glade.get_object("save")
		button.connect("clicked", self.save)
		button = self.glade.get_object("open")
		button.connect("clicked", self.load)
		button = self.glade.get_object("import")
		button.connect("clicked", self.import_file)		

		button = self.glade.get_object("to_file")
		button.connect("clicked", self.to_file)
		button = self.glade.get_object("undo")
		button.connect("clicked", self.undo)
		button = self.glade.get_object("redo")
		button.connect("clicked", self.redo)
		button = self.glade.get_object("add")
		button.connect("clicked", self.add)
		button = self.glade.get_object("remove")
		button.connect("clicked", self.remove)
		button = self.glade.get_object("refresh")
		button.connect("clicked", self.refresh)

		button = self.glade.get_object("copy")
		button.connect("clicked", self.copy)
		button = self.glade.get_object("up")
		button.connect("clicked", self.move, -1)
		button = self.glade.get_object("down")
		button.connect("clicked", self.move,  2)
		button = self.glade.get_object("indent")
		button.connect("clicked", self.indent)
		button = self.glade.get_object("unindent")
		button.connect("clicked", self.unindent)

		self.main_box.reparent(self)
		self.main_box.show_all()

		self.autorefresh = self.glade.get_object("autorefresh")
		self.autorefresh_timeout = self.glade.get_object("autorefresh_timeout")
		if self.autorefresh_timeout.get_value() == 0 :
			self.autorefresh_timeout.set_value(1)  # hack to glade default value=0 bug
		paned = self.glade.get_object("vpaned2")	
		w,h = paned.get_size_request()
		paned.set_size_request(w,500)	
		w,h = paned.get_size_request()
		paned.set_position(max(300,h-200))

		w,h = self.treeview.get_size_request()		
		self.treeview.set_size_request(w,200)	
		w,h = self.help_viewport.get_size_request()		
		self.help_viewport.set_size_request(w,100)	
		
		if search_path(SUBROUTINES_PATH,"defaults.ngc") != None :
			self.defaults = open( search_path(SUBROUTINES_PATH,"defaults.ngc") ).read()
		else :
			print _("Warning defaults.ngc was not found in path %s!")%SUBROUTINES_PATH 
		self.load(filename=search_path(SUBROUTINES_PATH,"template.xml"))

		self.treeview.connect("destroy", self.delete)

	def delete(self, *arg) :
		# save config
		if "VAR" not in self.config.sections() :
			self.config.add_section('VAR')
		if "FEATURES" not in self.config.sections() :
			self.config.add_section('FEATURES')

		for i in self.ini :	
			self.config.set("FEATURES",i.lower() , self.ini[i])
	
		for src in self.topfeatures :
			self.topfeatures_dict[src] = self.topfeatures[src][2:]
		topfeatures = ""
		for src in self.topfeatures_dict :
			topfeatures += "\n%s	%s	%s"%(src,self.topfeatures_dict[src][0], self.topfeatures_dict[src][1]) 
		
		self.config.set("VAR","topfeatures", topfeatures)
		try :
			print self.config_src 
			self.config.write(open(self.config_src,"w"))
		except :	
			print "Warning cannot write to config file %s!"%self.config_src

	
	def get_translations(self) :
		find = os.popen("find ./subroutines/ -name '*.ini'").read()		

		translatable = []
		for s in find.split() :
			print s
			global SUBROUTINES_PATH 
			SUBROUTINES_PATH = "./"

			f = Feature(s)
			for i in ["name", "help"] :
				if i in f.attr :
					s1 = f.attr[i]
		 			translatable.append((s,s1))
			for p in f.param :
				for i in ["name", "help", "tool_tip"] :
					if i in p.attr :
						s1 = p.attr[i]
			 			translatable.append((s,s1))
		out = []
		for i in translatable : 
			out.append( "#: %s"%i[0] )
			s = i[1].replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n")
			out.append( "_(%s)"%repr(i[1]) )
		out = "\n".join(out)	
		
		open("subroutines-ini-files","w").write(out)
		os.popen("xgettext --language=Python features.py -o tmp.po")
		os.popen("xgettext --language=Python subroutines-ini-files -o tmp1.po")
		os.popen("sed --in-place *.po --expression=s/charset=CHARSET/charset=UTF-8/") # fix fckng encoding.
		os.popen("msgcat tmp.po tmp1.po -o locale/linuxcnc-features.po")
		os.popen("rm tmp1.po tmp.po subroutines-ini-files")
		os.popen("cd locale ; ./update-po.sh")
		
			
	def move(self, call, i) :
		f,iter = self.get_selected_feature()
		if f :
			path = self.treestore.get_string_from_iter(iter)
			xml = self.treestore_to_xml()
			src = xml.find(".//*[@path='%s']"%path)		
			parent = src.getparent()
			i = parent.index(src)+i
			if i<0 : return
			parent.insert(i , src) 
			self.treestore_from_xml(xml)	
			self.action(xml)	

	def get_selected_feature(self) :
		selection = self.treeview.get_selection()
		(model, pathlist) = selection.get_selected_rows()
		if len(pathlist) > 0 :
			iter = model.get_iter(pathlist[0])
			f = self.treestore.get(iter,0)[0] 
			if f.__class__ == Feature : 
				return f,iter
		return None, None
		
	def indent(self, call) :
		f,iter = self.get_selected_feature()
		if f : 
			next = self.treestore.iter_next(iter)
			if next :
				f1 = self.treestore.get(next,0)[0] 
				if f1.__class__ == Feature : 
					path = self.treestore.get_string_from_iter(iter)
					path_next = self.treestore.get_string_from_iter(next)
					xml = self.treestore_to_xml()
					src = xml.find(".//*[@path='%s']"%path)
					dst = xml.find(".//*[@path='%s']/param[@type='items']"%path_next)
					if dst != None :
						dst.insert(0,src)
						dst.set("expanded","True")
						dst = xml.find(".//*[@path='%s']"%path_next)
						dst.set("expanded","True")							
						self.treestore_from_xml(xml)	
						self.action(xml)	

	def unindent(self, call) : 
		f,iter = self.get_selected_feature()
		if f : 
			xml = self.treestore_to_xml()
			path = self.treestore.get_string_from_iter(iter)
			src = xml.find(".//*[@path='%s']"%path)
			parent = src.getparent().getparent()
			n = None
			while parent != xml and not (parent.tag=="param" and parent.get("type") == "items") and parent is not None :
				p = parent
				parent = parent.getparent()
				n = parent.index(p)
			if parent is not None and n != None:	
				parent.insert(n, src)
				self.treestore_from_xml(xml)	
				self.action(xml)	
					
		
	def copy(self, *arg) :
		f,iter = self.get_selected_feature()
		if f :
			path = self.treestore.get_string_from_iter(iter)
			xml = self.treestore_to_xml()
			src = xml.find(".//*[@path='%s']"%path)		
			cp = deepcopy(src)
			parent = src.getparent()
			parent.insert(parent.index(src)+1, cp) 
			self.treestore_from_xml(xml)	
			self.action(xml)	
			
	def treeview_release(self, widget, event) :
		return False
		
	def treeview_keypress(self, widget, event) :
		keyname = gtk.gdk.keyval_name(event.keyval)
		selection = self.treeview.get_selection()
		(model, pathlist) = selection.get_selected_rows()
		path = pathlist[0] if len(pathlist) > 0 else None 
		
		if keyname == "Up" : 
			if path :
				rect = self.treeview.get_cell_area(path, self.col_value) 
				path = self.treeview.get_path_at_pos(rect[0],rect[1]-1)
				if path :
					path = path[0]
					self.treeview.set_cursor(path, focus_column=self.col_value, start_editing=False)
					return True
		if keyname == "Down" :
			if path :
				rect = self.treeview.get_cell_area(path, self.col_value) 
				path = self.treeview.get_path_at_pos(rect[0],rect[1]+rect[3]+1)
				if path :
					path = path[0]
					self.treeview.set_cursor(path, focus_column=self.col_value, start_editing=False)
					return True
		if keyname == "Left" : 
			if path!= None :
				self.treeview.collapse_row(path)
				return True			
		if keyname == "Right" : 
			if path!= None :
				self.treeview.expand_row(path,False)
				return True
		if keyname == "Return" : 
			if path!= None :
				iter = model.get_iter(path)
				self.treeview.set_cursor_on_cell(path, focus_column=self.col_value, focus_cell=self.cell_value, start_editing=True)
				return True
		return False

	def add(self, *arg) :
		response = self.add_dialog.run()
		self.add_dialog.hide()

	def do_get_property(self, property) :
		return None
			
	def do_set_property(self, property) :
		pass
	
	def show_help(self, callback, treeview) :
		treeselection = treeview.get_selection()
		model, iter = treeselection.get_selected()
		while iter != None :
			f = model.get(iter,0)[0]
			if f.get_attr("image") != None :
				self.help_image.set_from_pixbuf( get_pixbuf(f.get_attr("image")) )
				self.help_text.set_markup( _(f.get_attr("help")) )
				break
			iter = model.iter_parent(iter)	

	def treestore_from_xml_recursion(self, treestore, iter, xmlpath):
		for xml in xmlpath :
			if xml.tag == "feature" :
				f = Feature(xml = xml)
				tool_tip = f.attr["tool_tip"] if "tool_tip" in f.attr else None
				citer = treestore.append(iter, [f, tool_tip])
				for p in f.param :
					tool_tip = p.attr["tool_tip"] if "tool_tip" in p.attr else None
					piter = treestore.append(citer, [p, tool_tip])
					if p.get_attr("type") == "items" :
						xmlpath_ = xml.find(".//param[@type='items']")
						self.treestore_from_xml_recursion(treestore, piter, xmlpath_)
				

	def treestore_from_xml(self, xml, expand = True):
		treestore = gtk.TreeStore(object, str)
		self.treestore_from_xml_recursion(treestore, treestore.get_iter_root(), xml)		
		self.treestore = treestore
		self.treeview.set_model(self.treestore)
		if expand : self.set_expand()


	def get_features(self) :
		l = self.catalog.findall(".//sub")		
		
		for s in l:
			if "sub" not in s.keys() : 
				print _("Warning there's no 'sub' key in %s") %	etree.tostring(s, pretty_print=True)
				return 
			src = s.get("sub")
			try :   # TODO make better catalog 
					# if there's an error parsing ini - just skip it
				f = Feature(src)
				if "image" in f.attr :
					image = gtk.Image() 
					pixbuf = gtk.gdk.pixbuf_new_from_file(search_path(SUBROUTINES_PATH, f.attr["image"]))
					w,h = pixbuf.get_width(), pixbuf.get_height()
					if w > h :
						pixbuf = pixbuf.scale_simple(ADD_ICON_SIZE, h*ADD_ICON_SIZE/w, gtk.gdk.INTERP_BILINEAR)
					else :	
						pixbuf = pixbuf.scale_simple(w*ADD_ICON_SIZE/h, ADD_ICON_SIZE, gtk.gdk.INTERP_BILINEAR)
						
				else : 
					pixbuf = None
				#self.icon_liststore.append([pixbuf,f.attr["name"],s])
			except Exception, e :
				print _("Warning: Error while parsing %s...")%etree.tostring(s, pretty_print=True)
				print e


	def refresh_recursive(self, iter) :
		gcode_def = ""
		gcode = ""
		f = self.treestore.get(iter,0)[0]
		if f.__class__ == Feature : 
			gcode_def += f.get_definitions()
			gcode += f.process(f.attr["before"]) 
			gcode += f.process(f.attr["call"]) 
		iter = self.treestore.iter_children(iter)
		while iter :
			g,d = self.refresh_recursive(iter)
			gcode += g
			gcode_def += d
			iter = self.treestore.iter_next(iter)
		if f.__class__ ==	 Feature : 
			gcode += f.process(f.attr["after"])+"\n" 

		return gcode,gcode_def
	
	def to_gcode(self, *arg) :
		gcode = ""
		gcode_def = ""
		global DEFINITIONS
		DEFINITIONS = []
		global INCLUDE
		INCLUDE = []		
		iter = self.treestore.get_iter_root()
		while iter != None :
			g,d =  self.refresh_recursive(iter)
			gcode += g
			gcode_def += d
			iter = self.treestore.iter_next(iter)
		if search_path(SUBROUTINES_PATH,"defaults.ngc") != None :
			self.defaults = open( search_path(SUBROUTINES_PATH,"defaults.ngc") ).read()
		else :
			print _("Warning defaults.ngc was not found in path %s!")%SUBROUTINES_PATH 
	
			
		return self.defaults+gcode_def+"(End definitions)\n\n\n"+gcode + "\n\nM02"
		
					
	def refresh(self, *arg ) :
		f = open(PROGRAM_PREFIX + "/features.ngc","w")
		f.write(self.to_gcode())
		f.close()
		self.linuxcnc.reset_interpreter()
		self.linuxcnc.mode(linuxcnc.MODE_AUTO)
		self.linuxcnc.program_open(PROGRAM_PREFIX + "/features.ngc")
		subprocess.call(["axis-remote",PROGRAM_PREFIX + "/features.ngc"])
		
	
	def to_file(self, *arg) :
		filechooserdialog = gtk.FileChooserDialog("Save as...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name("NGC")
		filter.add_mime_type("text/ngc")
		filter.add_pattern("*.ngc")
		filechooserdialog.add_filter(filter)
		filechooserdialog.set_current_folder(self.file_dialogs_folder)		
		
		response = filechooserdialog.run()
		if response == gtk.RESPONSE_OK:
			self.file_dialogs_folder = filechooserdialog.get_current_folder()		
			gcode = self.to_gcode()
			filename = filechooserdialog.get_filename() 
			if filename[-4]!=".ngc" not in filename :
				filename += ".ngc"
			f = open(filename,"w")
			f.write(gcode)
			f.close()
		filechooserdialog.destroy()
		
		
	def edit_value(self, cellrenderertext, path, new_text) :
		iter = self.treestore.get_iter(path)
		self.treestore.get(iter,0)[0].attr["value"] = new_text
		self.action()
		self.treeview.grab_focus()
				
	def remove(self, call) :
		treeselection = self.treeview.get_selection()
		model, iter = treeselection.get_selected()
		if iter != None :
			f = self.treestore.get(iter,0)[0]
			if f.__class__ == Feature : 
				self.treestore.remove(iter)
				self.action()

	def import_xml(self, xml_) :
		xml = self.treestore_to_xml()
		
		if xml_.tag != "LinuxCNC-Features":
			xml_ = xml_.find(".//LinuxCNC-Features")
			
		if xml_ != None :	
			for x in xml_ :
				xml.append(x)
				l = x.findall(".//feature")
				if x.tag == "feature" :
					l = [x]+l
				for xf in l :
					f=Feature(xml=xf)
					f.get_id(xml)
					xf.set("name", f.attr["name"])
					xf.set("id", f.attr["id"])
			self.treestore_from_xml(xml)
			self.action(xml)

		
	def add_feature(self, src) :
		xml = self.treestore_to_xml()
		f = Feature(src = src)
		f.get_id(xml)
		fxml = f.to_xml()
		xml.append(fxml)
		self.treestore_from_xml(xml)
		self.action(xml)
		self.topfeatures_update(src)

	def topfeatures_click(self, call, data)	:
		self.add_feature(data)
	
	def block_expose(self, *arg):
		return self.block_toptoolbar 
	
	def topfeatures_update(self, src = None):
		if src in self.topfeatures :
			# button topbutton i t
			self.topfeatures[src][2] += 1 
			self.topfeatures[src][3] = time.time()
		#self.block_toptoolbar = True
		# clear toolbar
		while self.topfeatures_toolbar.get_n_items() > 0 :
			 self.topfeatures_toolbar.remove(self.topfeatures_toolbar.get_nth_item(0))

		tf = self.topfeatures.items() 
		tf.sort(lambda x,y: -1 if x[1][2]-y[1][2]>0 else 1) # sort by i
		for tfi in tf[:self.ini["top-features"]] :
			self.topfeatures_toolbar.insert(tfi[1][0],-1)

		self.topfeatures_toolbar.insert(gtk.SeparatorToolItem(),-1)
		tf.sort(lambda x,y: -1 if x[1][3]-y[1][3]>0 else 1) # sort by t
		for tfi in tf[:self.ini["last-features"]] :
			self.topfeatures_toolbar.insert(tfi[1][1],-1)

		self.topfeatures_toolbar.show_all()
		self.block_toptoolbar = False	

	def update_catalog(self, call=None, xml=None) :
		if xml == "parent" : 
			self.catalog_path = self.catalog_path.getparent()
		else :	
			self.catalog_path = xml
		if 	self.catalog_path == None : self.catalog_path = self.catalog
		self.icon_store.clear()
		
		# add link to upper level
		if self.catalog_path != self.catalog :
			self.icon_store.append([get_pixbuf("images/upper-level.png"),"","parent",0])
		
		for path in range(len(self.catalog_path)) :
			p = self.catalog_path[path]
			name = _(p.get("name")) if "name" in p.keys() else None 
			sub = p.get("sub") if "sub" in p.keys() else None 
			icon = p.get("icon") if "icon" in p.keys() else None
			if icon == None :
				try :
					f = Feature(sub)
					icon = f.get_attr("image")
				except:
					print _("Warning no icon for feature %(feature)s in catalog %(catalog)")%{"feature":sub,"catalog":self.catalog_src}
			pixbuf = get_pixbuf(icon)
			self.icon_store.append([pixbuf, name, sub, path])
		
	
	def catalog_activate(self, iconview, path) : 
		iter = self.icon_store.get_iter(path)
		src = self.icon_store.get(iter,2)[0]
		if src != None :
			if src == "parent" :
				self.update_catalog(xml="parent")
			else :
				self.add_feature(src)
				self.add_dialog.hide()
		else : 	# it's a group
			path = self.icon_store.get(iter,3)[0]		
			self.update_catalog(xml=self.catalog_path[path]) 
		
	def autorefresh_call(self) :
		self.refresh()
		return False
		
	def action(self, xml = None) :
		if xml==None :
			xml = self.treestore_to_xml()
		self.undo_list = self.undo_list[:self.undo_pointer+1]
		self.undo_list = self.undo_list[max(0,len(self.undo_list)-UNDO_MAX_LEN):]
		self.undo_list.append(etree.tostring(xml))
		self.undo_pointer = len(self.undo_list)-1
		
		if self.autorefresh.get_active() :
			if self.timeout != None :
				gobject.source_remove(self.timeout)
			self.timeout = gobject.timeout_add(self.autorefresh_timeout.get_value()*1000, self.autorefresh_call)
		
	def undo(self, *arg) :
		if self.undo_pointer>=0 and len(self.undo_list)>0:
			self.treestore_from_xml(etree.fromstring(self.undo_list[self.undo_pointer]))
			self.undo_pointer -= 1
						
	def redo(self, *arg) :
		if self.undo_pointer < len(self.undo_list)-1 :
			self.undo_pointer += 1
			self.treestore_from_xml(etree.fromstring(self.undo_list[self.undo_pointer]))
		
	def clear_undo(self, *arg) :
		self.undo_list = []
		self.undo_pointer = 0
	
	def test(self, *arg) :
		global FEATURE_DICT 
		FEATURE_DICT = {}
		self.get_features()
		#gobject.timeout_add(1000, self.test)
		#print	gtk.window_list_toplevels(),gtk.window_list_toplevels()[0].get_focus()
		#for i in gtk.window_list_toplevels() :
		#print arg

	def move_before(self, src, dst, after = False, append = False) :
		src = self.treestore.get_string_from_iter(src)
		dst = self.treestore.get_string_from_iter(dst)		
		xml = self.treestore_to_xml()
		src = xml.find(".//*[@path='%s']"%src)		
		dst = xml.find(".//*[@path='%s']"%dst)
		#print dst
		parent = dst.getparent()
		while parent != None:
			if parent == src : return # can not move element inside itself
			parent = parent.getparent()			
		if dst==None or src==None :		
			print _("Error in dst, or src wile moving subtrees! (dst %(dst)s) (src %(src)s)")%{"dst":dst,"src":src}
			return
		if after :
			dst.getparent().insert(dst.getparent().index(dst)+1, src) 
		elif append :
			dst.insert(0, src) 
		else : 
			dst.getparent().insert(dst.getparent().index(dst), src) 
		self.treestore_from_xml(xml)	
		self.action(xml)	
		
	def move_after(self, src, dst) :
		self.move_before(src, dst, after = True)
		
	def append_node(self, src, dst, append = True) :
		self.move_before(src, dst, append = True)
		 
	def grab(self, *arg) :
		self.treeview.grab_focus()

	def get_col_name(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).get_name() )
		
	def get_col_value(self, column, cell, model, iter, ptype) :	
		cell.set_property('text', model.get_value(iter, 0).get_value(ptype) )

	def get_col_icon(self, column, cell, model, iter) :	
		cell.set_property('pixbuf', model.get_value(iter, 0).get_icon() )

	def treestore_to_xml_recursion(self, iter, xmlpath):
		while iter : 
			f = self.treestore.get(iter,0)[0]	
			if f.__class__ == Feature :
				xmlpath.append(f.to_xml())
			# check for the childrens
			citer = self.treestore.iter_children(iter)
			while citer :
				p = self.treestore.get(citer, 0)[0]
				if p.get_attr("type") == "items" :
					xmlpath_ = xmlpath.find(".//param[@type='items']")
					self.treestore_to_xml_recursion(self.treestore.iter_children(citer), xmlpath_)
				citer = self.treestore.iter_next(citer)
			# check for next items
			iter = self.treestore.iter_next(iter)


		
	def treestore_to_xml(self, *arg):
		xml = etree.Element("LinuxCNC-Features")
		self.get_expand()
		self.treestore_to_xml_recursion(self.treestore.get_iter_root(), xml)
		return xml


	def treestore_from_xml_recursion(self, treestore, iter, xmlpath):
		for xml in xmlpath :
			if xml.tag == "feature" :
				f = Feature(xml = xml)
				tool_tip = _(f.attr["tool_tip"]) if "tool_tip" in f.attr else None
				citer = treestore.append(iter, [f, tool_tip])
				for p in f.param :
					tool_tip = _(p.attr["tool_tip"]) if "tool_tip" in p.attr else None
					piter = treestore.append(citer, [p, tool_tip])
					if p.get_attr("type") == "items" :
						xmlpath_ = xml.find(".//param[@type='items']")
						self.treestore_from_xml_recursion(treestore, piter, xmlpath_)
				

			#if len(xml) :
			#	self.treestore_from_xml_recursion(treestore, citer, xml)
				

	def treestore_from_xml(self, xml, expand = True):
		treestore = gtk.TreeStore(object, str)
		self.treestore_from_xml_recursion(treestore, treestore.get_iter_root(), xml)		
		self.treestore = treestore
		self.treeview.set_model(self.treestore)
		if expand : self.set_expand()

	
	def set_expand(self) :		
		def treestore_set_expand(model, path, iter, self) :
			p = model.get(iter,0)[0].attr
			if "expanded" in p and p["expanded"] == "True":
				self.treeview.expand_row(path, False)
			if "selected" in p and p["selected"] == "True":
				self.selection.select_path(path)
		self.selected_pathlist = []
		self.selection = self.treeview.get_selection()
		self.selection.unselect_all()
		self.treestore.foreach(treestore_set_expand, self)
		

	def get_expand(self) :
		def treestore_get_expand(model, path, iter, self) :
			p = model.get(iter,0)[0]
			p.attr["path"] = model.get_string_from_iter(iter)
			p.attr["expanded"] = self.treeview.row_expanded(path)
			path = self.treestore.get_path(iter)
			p.attr["selected"] = path in self.selected_pathlist
		self.selection = self.treeview.get_selection()
		(model, pathlist) = self.selection.get_selected_rows()
		self.selected_pathlist = pathlist
		self.treestore.foreach(treestore_get_expand, self)

	def import_file(self, calback) :
		filechooserdialog = gtk.FileChooserDialog("Import", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name("XML")
		filter.add_mime_type("text/xml")
		filter.add_pattern("*.xml")
		filechooserdialog.add_filter(filter)
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		filechooserdialog.add_filter(filter)
		filechooserdialog.set_current_folder(self.file_dialogs_folder)
		
		response = filechooserdialog.run()		
		if response == gtk.RESPONSE_OK:
			self.file_dialogs_folder = filechooserdialog.get_current_folder()		
			filename = filechooserdialog.get_filename() 
			xml = etree.parse(filename).getroot()
			self.import_xml(xml)
		
		filechooserdialog.destroy()

	def save(self, callback) :
		filechooserdialog = gtk.FileChooserDialog("Save as...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name("XML")
		filter.add_mime_type("text/xml")
		filter.add_pattern("*.xml")
		filechooserdialog.add_filter(filter)
		filechooserdialog.set_current_folder(self.file_dialogs_folder)
		
		response = filechooserdialog.run()
		if response == gtk.RESPONSE_OK:
			self.file_dialogs_folder = filechooserdialog.get_current_folder()
			xml = self.treestore_to_xml()
			filename = filechooserdialog.get_filename() 
			if filename[-4]!=".xml" not in filename :
				filename += ".xml"
			etree.ElementTree(xml).write(filename, pretty_print=True)
		filechooserdialog.destroy()
		
	def load(self, callback=None, filename=None) :
		if filename != None :
			xml = etree.parse(filename)
		else :	
			filechooserdialog = gtk.FileChooserDialog("Open", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
			filter.set_name("XML")
			filter.add_mime_type("text/xml")
			filter.add_pattern("*.xml")
			filechooserdialog.add_filter(filter)
			filechooserdialog.set_current_folder(self.file_dialogs_folder)
			
			response = filechooserdialog.run()
			if response == gtk.RESPONSE_OK:
				self.file_dialogs_folder = filechooserdialog.get_current_folder()			
				filename = filechooserdialog.get_filename() 
				xml = etree.parse(filename)
			filechooserdialog.destroy()
		if filename != None :
			self.treestore_from_xml(xml.getroot())
		

# for testing without glade editor:
def t(*arg) :
	return False

def main():
    window = gtk.Dialog("My dialog",
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    
    features = Features()
    window.connect("key_press_event", t)
    window.vbox.add(features)
    window.connect("destroy", gtk.main_quit)
    window.show_all()
    response = window.run()

if __name__ == "__main__":	
	main()
	#import cProfile
	#command = """main()"""
	#cProfile.runctx( command, globals(), locals(), filename="test.profile" )
	
	
	
