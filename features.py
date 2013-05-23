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


PARAMETERS = ["string", "float", "int", "image"]	
FEATURES = ["feature"]
GROUPS = ["group"]
UNDO_MAX_LEN = 200
SUBROUTINES_PATH = "subroutines/"
ADD_ICON_SIZE = 60

datadir = os.path.abspath(os.path.dirname(__file__))

def get_int(s) :
	try :
		return int(s)
	except :
		return 0	

PIXBUF_DICT = {}
FEATURE_DICT = {}


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
		self.set_pixbufs()
		if "type" in self.attr : self.attr["type"] = self.attr["type"].lower()
		if "call" not in self.attr : self.attr["call"] = "#"+ini_id.lower()
		
	def from_xml(self, xml) :
		for i in xml.keys() :
			self.attr[i] = xml.get(i)
		self.set_pixbufs()
		
	def to_xml(self) : 
		xml = etree.Element("param")
		for i in self.attr :
			xml.set(i, unicode(str(self.attr[i])))
		return xml
		
	def set_pixbufs(self) :
		for i in self.attr : 
			if i in ["icon","image"] :
				if self.attr[i] not in PIXBUF_DICT :
					try :
						PIXBUF_DICT[self.attr[i]] = gtk.gdk.pixbuf_new_from_file(SUBROUTINES_PATH+self.attr[i])
					except :
						print "Warning: problem with image %s "%(SUBROUTINES_PATH+self.attr[i])
				self.pixbuf[i] = PIXBUF_DICT[self.attr[i]]
	
	def get_pixbuf(self, t) :
		return self.pixbuf[t]  if t in self.pixbuf else None
	def get_icon(self) : return self.get_pixbuf("icon")
	def get_image(self) : return self.get_pixbuf("image")

	def get_value(self, ptype) :
		if self.attr["type"] in ptype :
			return self.attr["value"] if "value" in self.attr else ""

	def get_name(self) :
		return self.attr["name"] if "name" in self.attr else ""
	
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

	def get_pixbuf(self, t) :
		return self.pixbuf[t]  if t in self.pixbuf else None
	def get_icon(self) : return self.get_pixbuf("icon")
	def get_image(self) : return self.get_pixbuf("image")

	def get_value(self, ptype):
		if self.attr["type"] in ptype :
			return self.attr["value"] if "value" in self.attr else ""
	
	def get_attr(self, attr) :
		return self.attr[attr] if attr in self.attr else None
	
	
	def get_name(self):
		return self.attr["name"] if "name" in self.attr else ""
		
	def from_src(self, src) :
		if src in  FEATURE_DICT : self.from_xml(FEATURE_DICT[src])
		config = ConfigParser.ConfigParser()
		config.read(SUBROUTINES_PATH+src)
		#print src
		self.attr = dict(config.items("SUBROUTINE"))
		self.attr["src"] = src
		self.param = []
		conf = config.sections()
		conf.sort()
		for s in conf :		
			if s[:5]== "PARAM" :
				self.param.append( Parameter(ini=config.items(s), ini_id=s) )
		# get gcode parameters		
		try :
			self.attr["definitions"] = config.get("DEFINITIONS","content")	
		except: 
			self.attr["definitions"] = ""
		try :
			self.attr["before"] = config.get("BEFORE","content")	
		except: 
			self.attr["before"] = ""
		try :
			self.attr["call"] = config.get("CALL","content")	
		except: 
			self.attr["call"] = ""
		try :
			self.attr["after"] = config.get("AFTER","content")	
		except: 
			self.attr["after"] = ""
		self.set_pixbufs()	
		#print etree.tostring(self.to_xml(), pretty_print=True)
		if self.attr["src"] not in 	FEATURE_DICT : FEATURE_DICT[self.attr["src"]] = self.to_xml()
	
	def set_pixbufs(self) :
		for i in self.attr : 
			if i in ["icon","image"] :
				if self.attr[i] not in PIXBUF_DICT :
					PIXBUF_DICT[self.attr[i]] = gtk.gdk.pixbuf_new_from_file(SUBROUTINES_PATH+self.attr[i])
				self.pixbuf[i] = PIXBUF_DICT[self.attr[i]]
		
	def from_xml(self, xml) :
		self.attr = {}
		for i in xml.keys() :
			self.attr[i] = xml.get(i)
		self.set_pixbufs()

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
		
	def get_definitions(self,definitions) :
		if self.attr["type"] not in definitions : 	
			definitions.append(self.attr["type"])
			return self.process(self.attr["definitions"])+"\n"
		else :
			return ""
	

	def process(self, s) :
		def process_callback(m) :
			return eval(m.group(2), {"self":self})
		s = re.sub(r"(?i)(<eval>(.*?)</eval>)", process_callback, s)

		for p in self.param :
			if "call" in p.attr and "value" in p.attr :
				s = re.sub(r"%s"%(re.escape(p.attr["call"])),"%s"%p.attr["value"], s)
		return s
	
class Features(gtk.VBox):
	__gtype_name__ = "Features"
	__gproperties__ = {}
	__gproperties = __gproperties__ 
	
	def __init__(self, *a, **kw):
		gtk.VBox.__init__(self, *a, **kw)
		self.undo_list = []
		self.undo_pointer = 0
		self.glade = gtk.Builder()
		self.glade.add_from_file(os.path.join(datadir, "features.glade"))
		self.main_box = self.glade.get_object("FeaturesBox")
		self.glade.connect_signals(self)

		# create features catalog
		self.add_iconview = gtk.IconView()		
		self.icon_liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
		self.add_iconview.set_model(self.icon_liststore)
		self.add_iconview.set_pixbuf_column(0)
		self.add_iconview.set_text_column(1)
		self.add_iconview.connect("item-activated", self.add_feature_from_cat)
		
		self.get_features()
   		
		self.help_viewport = self.glade.get_object("help_viewport")
   		self.help_image = self.glade.get_object("feature_image")	
   		self.help_text = self.glade.get_object("feature_help")	
		
		 
		self.add_container = self.glade.get_object("add_feature_container")	
		self.add_container.add_with_viewport(self.add_iconview)
		
		# create treeview
		self.treeview = self.glade.get_object("treeview1")
		self.treestore = gtk.TreeStore(object, str)
		self.treeview.set_model(self.treestore)
		self.treeview.set_tooltip_column(1)

		self.cols = {}
		col =  gtk.TreeViewColumn("Name")
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
		col =  gtk.TreeViewColumn("Value")
		cell = gtk.CellRendererText() 
		cell.set_property("editable",True)
		cell.connect('edited', self.edit_value)		
		col.pack_start(cell, expand=False)
		col.set_cell_data_func(cell, self.get_col_value, ["string","float","int"])
		
		#cell = gtk.CellRendererSpin()
		#adjustment = gtk.Adjustment(value=0, lower=0, upper=0, step_incr=0.1, page_incr=10, page_size=0)
		#cell.set_property("adjustment", adjustment)
		#cell.set_property("editable",True)
		#cell.connect('edited', self.edit_value)		
		#col.pack_start(cell, expand=True)
		#col.set_cell_data_func(cell, self.get_col_value, ["float" ,"int"])
		
		col.set_resizable(True)		
		self.treeview.append_column(col)
		self.cols["value"] = col
		
		self.TARGETS = [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),]		
		self.treeview.enable_model_drag_source( gtk.gdk.BUTTON1_MASK, self.TARGETS, gtk.gdk.ACTION_DEFAULT |  gtk.gdk.ACTION_MOVE)
		self.treeview.enable_model_drag_dest(self.TARGETS, gtk.gdk.ACTION_DEFAULT)

		self.treeview.connect("drag_data_get", self.drag_data_get_data)		
		self.treeview.connect("drag_data_received", self.drag_data_received_data)
		self.treeview.connect("cursor-changed", self.show_help, self.treeview)

		#self.load(None,"test.xml")

		button = self.glade.get_object("test")
		button.connect("clicked", self.test)
		button = self.glade.get_object("save")
		button.connect("clicked", self.save)
		button = self.glade.get_object("open")
		button.connect("clicked", self.load)
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
		button = self.glade.get_object("collapse_param")
		button.connect("clicked", self.collapse, [Parameter])
		button = self.glade.get_object("collapse_all")
		button.connect("clicked", self.collapse, [Parameter, Feature])
		self.main_box.reparent(self)
		self.main_box.show_all()


		paned = self.glade.get_object("vpaned1")	
		w,h = paned.get_size_request()		
		paned.set_size_request(w,200)	
		paned.set_position(100)
		paned = self.glade.get_object("vpaned2")	
		w,h = paned.get_size_request()
		paned.set_size_request(w,500)	
		paned.set_position(300)
		
	
		w,h = self.treeview.get_size_request()		
		self.treeview.set_size_request(w,200)	
		w,h = self.help_viewport.get_size_request()		
		self.help_viewport.set_size_request(w,100)	

		self.main_box.connect("destroy", gtk.main_quit)
		
		self.add_dialog = None

	def add(self, *arg) :
		if self.add_dialog == None :
			self.add_dialog = gtk.Dialog("Add feature", self.main_box.get_toplevel(), gtk.RESPONSE_CANCEL or gtk.DIALOG_MODAL, (gtk.STOCK_CLOSE,gtk.RESPONSE_REJECT))
			#self.add_container.reparent(self.add_dialog)
			add_iconview = gtk.IconView()		
			add_iconview.set_model(self.icon_liststore)
			add_iconview.set_pixbuf_column(0)
			add_iconview.set_text_column(1)
			add_iconview.connect("item-activated", self.add_feature_from_cat)
			scroll = gtk.ScrolledWindow()
			scroll.add_with_viewport(add_iconview)
			self.add_dialog.vbox.pack_start(scroll)
			self.add_dialog.show_all()
			self.add_dialog.set_size_request(600,500)
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
			if f.__class__ == Feature :
				self.help_image.set_from_pixbuf(f.get_image())
				self.help_text.set_markup(f.get_attr("help"))
				break
			iter = model.iter_parent(iter)	

	def get_features(self) :
		for s in os.listdir(SUBROUTINES_PATH):
			if s[-4:] == ".ini" :
				try :   # TODO make better catalog 
						# if there's an error parsing ini - just skip it
					f = Feature(s)
					if "image" in f.attr :
						image = gtk.Image() 
						pixbuf = gtk.gdk.pixbuf_new_from_file(SUBROUTINES_PATH+f.attr["image"])
						w,h = pixbuf.get_width(), pixbuf.get_height()
						if w > h :
							pixbuf = pixbuf.scale_simple(ADD_ICON_SIZE, h*ADD_ICON_SIZE/w, gtk.gdk.INTERP_BILINEAR)
						else :	
							pixbuf = pixbuf.scale_simple(w*ADD_ICON_SIZE/h, ADD_ICON_SIZE, gtk.gdk.INTERP_BILINEAR)
					else : 
						pixbuf = none
					self.icon_liststore.append([pixbuf,f.attr["name"],s])
				except Exception, e :
					print "Warning: Error while parsing %s..."%s
					print e
	def collapse(self, call, l) :
		def treestore_collapse(model, path, iter, data) :
			self, l = data[0],data[1]
			p = model.get(iter,0)[0]
			if p.__class__ in l :
				self.treeview.collapse_row(path)
		self.treestore.foreach(treestore_collapse, [self, l])

	def refresh_recursive(self, iter) :
		gcode_def = ""
		gcode = ""
		f = self.treestore.get(iter,0)[0]
		if f.__class__ == Feature : 
			gcode_def += f.get_definitions(self.definitions)
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
					
	def refresh(self, *arg ) :
		gcode = ""
		gcode_def = ""
		self.definitions = []
		iter = self.treestore.get_iter_root()
		while iter != None :
			g,d =  self.refresh_recursive(iter)
			gcode += g
			gcode_def += d
			iter = self.treestore.iter_next(iter)
		return gcode_def+"(End definitions)\n\n\n"+gcode + "\n\nM02"

	def to_file(self, *arg) :
		filechooserdialog = gtk.FileChooserDialog("Save as...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
		response = filechooserdialog.run()
		if response == gtk.RESPONSE_OK:
			gcode = self.refresh()
			filename = filechooserdialog.get_filename() 
			if filename[-4]!=".ngc" not in filename :
				filename += ".ngc"
			f = open(filename,"w")
			f.write(gcode)
			f.close()
		filechooserdialog.destroy()
		
		
	def edit_value(self, cellrenderertext, path, new_text) :
		self.action()		
		iter = self.treestore.get_iter(path)
		self.treestore.get(iter,0)[0].attr["value"] = new_text
				
	def remove(self, call) :
		self.action()
		treeselection = self.treeview.get_selection()
		model, iter = treeselection.get_selected()
		if iter != None :
			f = self.treestore.get(iter,0)[0]
			if f.__class__ == Feature : 
				self.treestore.remove(iter)
		
	def add_feature(self, src) :
		self.action()
		xml = self.treestore_to_xml()
		f = Feature(src = src)
		f.get_id(xml)
		fxml = f.to_xml()
		xml.append(fxml)
		self.treestore_from_xml(xml)
		xml = self.treestore_to_xml(xml)

	def add_feature_from_cat(self, iconview, path) :
		if self.add_dialog != None : self.add_dialog.response(gtk.RESPONSE_REJECT) 
		self.action()		
		model = iconview.get_model()
		iter = model.get_iter(path) 
		src = model.get(iter, 2)[0]
		self.add_feature(src)
		
	def action(self, *arg) :
		xml = self.treestore_to_xml()
		self.undo_list = self.undo_list[:self.undo_pointer+1]
		self.undo_list = self.undo_list[max(0,len(self.undo_list)-UNDO_MAX_LEN):]
		self.undo_list.append(etree.tostring(xml))
		self.undo_pointer = len(self.undo_list)-1
		
	def undo(self, *arg) :
		if self.undo_pointer>=0 :
			print "12",self.undo_list
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
		xml = self.treestore_to_xml()
		print self.refresh()

	def move_before(self, src, dst, after = False, append = False) :
		self.action()
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
			print "Error in dst, or src wile moving subtrees! (dst %s) (src %s)"%(dst,src)
			return
		if after :
			dst.getparent().insert(dst.getparent().index(dst)+1, src) 
		elif append :
			dst.insert(0, src) 
		else : 
			dst.getparent().insert(dst.getparent().index(dst), src) 
		self.treestore_from_xml(xml)	
		
	def move_after(self, src, dst) :
		self.move_before(src, dst, after = True)
		
	def append_node(self, src, dst, append = True) :
		self.move_before(src, dst, append = True)
		 

	def drag_data_get_data(self, treeview, context, selection, target_id, etime):
		pass
		#treeselection = treeview.get_selection()
		#model, iter = treeselection.get_selected()
		#feature = self.treestore.get(iter,0)[0]
		#selection.set('textn', 8, "1" )

	
	def drag_data_received_data(self, treeview, context, x, y, selection, info, etime) :
		treeselection = treeview.get_selection()
		model, src = treeselection.get_selected()
		drop_info = treeview.get_dest_row_at_pos(x, y)
		
		if self.treestore.get(src,0)[0].__class__ == Feature : # we can move only features
			if drop_info :
				dst, position = drop_info
				dst = self.treestore.get_iter(dst)
				dst_ = self.treestore.get(dst,0)[0]
				if dst_.__class__ == Feature : # Drop before and after only for features 
					if position == gtk.TREE_VIEW_DROP_BEFORE  :
						self.move_before(src, dst)
					elif  position == gtk.TREE_VIEW_DROP_AFTER:
						self.move_after(src, dst)
				elif dst_.__class__ == Parameter and dst_.get_attr("type") == "items" : # Drop inside only for Group's items 
						self.append_node(src, dst)
			else :
				# pop to root
				root = model.get_iter_root()
				n = model.iter_n_children(root)
				dst = model.iter_nth_child(root,n-1)
				self.move_after(src,dst)
			
		return False # cancel drag 

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
		#print etree.tostring(xml, pretty_print=True)
		return xml


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
		self.treestore.foreach(treestore_set_expand, self)

	def get_expand(self) :
		def treestore_get_expand(model, path, iter, self) :
			p = model.get(iter,0)[0]
			p.attr["path"] = model.get_string_from_iter(iter)
			p.attr["expanded"] = self.treeview.row_expanded(path)
		self.treestore.foreach(treestore_get_expand, self)
		

	def save(self, callback) :
		filechooserdialog = gtk.FileChooserDialog("Save as...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
		response = filechooserdialog.run()
		if response == gtk.RESPONSE_OK:
			xml = self.treestore_to_xml()
			filename = filechooserdialog.get_filename() 
			if filename[-4]!=".xml" not in filename :
				filename += ".xml"
			etree.ElementTree(xml).write(filename, pretty_print=True)
		filechooserdialog.destroy()
		
	def load(self, callback, filename=None) :
		if filename != None :
			xml = etree.parse(filename)
		else :	
			filechooserdialog = gtk.FileChooserDialog("Open", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
			response = filechooserdialog.run()
			if response == gtk.RESPONSE_OK:
				filename = filechooserdialog.get_filename() 
				xml = etree.parse(filename)
			filechooserdialog.destroy()
		if filename != None :
			self.treestore_from_xml(xml.getroot())
		

# for testing without glade editor:
def main():
    window = gtk.Dialog("My dialog",
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    
    features = Features()
    
    window.vbox.add(features)
    window.connect("destroy", gtk.main_quit)
    window.show_all()
    response = window.run()

if __name__ == "__main__":	
	main()
	
	
