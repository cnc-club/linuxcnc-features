#!/usr/bin/env python
# coding: utf-8
import sys
import os

import pygtk
pygtk.require('2.0')

import gtk
import gtk.glade
from lxml import etree
import time
import gobject

import ConfigParser
import re, os

PARAMETERS = ["string", "float", "int"]	
FEATURES = ["feature"]
UNDO_MAX_LEN = 200
SUBROUTINES_PATH = "subroutines/"
ADD_TABLE_WIDTH =2


def get_int(s) :
	try :
		return int(s)
	except :
		return 0	

class Feature():
	def __init__(self,src, xml = None) :
		self.src = src
		config = ConfigParser.ConfigParser()
		config.read(SUBROUTINES_PATH+self.src)
		self.attr = dict(config.items("SUBROUTINE"))

		num = 1		
		if xml!=None :
			# get smallest free name 
			l = xml.findall(".//feature[@type='%s']"%self.attr["type"])		
			num = max([ get_int(i.get("name")[-4:]) for i in l ])+1

		self.attr["name"] = self.attr["type"]+" %04d"%num
		
		self.param = []
		for s in config.sections() :		
			if s[:5]== "PARAM" :
				self.param.append( dict(config.items(s)) )
				
		#print etree.tostring(self.to_xml(), pretty_print=True)
		self.from_xml(self.to_xml())
		
	def to_xml(self) :
		xml = etree.Element("feature")
		for i in self.attr :
			xml.set(i, self.attr[i])
			
		for p in self.param :
			pxml = etree.Element("param")
			for i in p :
				pxml.set(i, p[i])
			xml.append(pxml)
		return xml	
		
	def from_xml(self, xml) :
		self.attr = {}
		for i in xml.keys() :
			self.attr[i] = xml.get(i)

		
	
	def execute(self,defenitions) :
		pass
		
	
class TreeFeature(): 
	param = {}
	type = "int"
	def __init__(self, xmlpath=None) :
		if xmlpath != None :
			self.from_xml(xmlpath)

		
	def get_value(self):
		return self.param["value"] if "value" in self.param else ""

	def get_name(self):
		return self.param["name"] if "name" in self.param else ""


	def get_icon(self):
		return self.pixbuf


	def to_xml(self, xmlpath, path, expanded=False) :
		p = dict([ ( i,str(self.param[i]) ) for i in self.param ])
		p["path"] = str(path)
		p["expanded"] = str(expanded)
		path = etree.SubElement(xmlpath, self.type, p)
		return path

	def from_xml(self, xmlpath) :
		self.param = {} 
		self.type = xmlpath.tag
		for i in xmlpath.keys() :
			self.param[i] = xmlpath.get(i)
		if "expanded" in self.param : self.param["expanded"] = self.param["expanded"].lower()=="true"
		
		if "icon" not in self.param: self.param["icon"] = "icons/no_icon.svg"
		self.pixbuf = gtk.gdk.pixbuf_new_from_file(SUBROUTINES_PATH+self.param["icon"])
			

class Features:

	def __init__(self):
		self.undo_list = []
		self.undo_pointer = 0
		self.glade = gtk.Builder()
		self.glade.add_from_file("features.glade")
		self.glade.connect_signals(self)
		self.window = self.glade.get_object("MainWindow")
		self.window.show_all()	
		self.window.connect("destroy", gtk.main_quit)
		self.treeview = self.glade.get_object("treeview1")
		self.treestore = gtk.TreeStore(object, str)
		self.treeview.set_model(self.treestore)
		self.treeview.set_tooltip_column(1)

		self.add_container = self.glade.get_object("add_feature_container")
		self.add_table = gtk.Table(rows=1, columns=ADD_TABLE_WIDTH, homogeneous=True)
		self.add_container.add_with_viewport(self.add_table)

		# load fratures
		i = 0
		table_w = self.window.get_size_request()[0]
		for s in os.listdir(SUBROUTINES_PATH):
			print s
			if s[-4:] == ".ini" :
				try :
					print s,"!!!"
					f = Feature(s)
					vbox = gtk.VBox()
					hbox = gtk.HBox()
					if "icon" in f.attr :
						image = gtk.Image() 
						image.set_from_file(SUBROUTINES_PATH+f.attr["icon"])
						hbox.pack_start(image)
					label = gtk.Label(f.attr["type"])
					label.set_line_wrap(True)
					hbox.pack_start(label)
					vbox.pack_start(hbox)
					if "image" in f.attr :
						image = gtk.Image() 
						pixbuf = gtk.gdk.pixbuf_new_from_file(SUBROUTINES_PATH+f.attr["image"])
						w,h = pixbuf.get_width(), pixbuf.get_height()
						pixbuf = pixbuf.scale_simple(table_w/ADD_TABLE_WIDTH,h*table_w/w/ADD_TABLE_WIDTH, gtk.gdk.INTERP_BILINEAR)
						image.set_from_pixbuf(pixbuf)
						vbox.pack_start(image)

					button = gtk.Button()
					button.add(vbox)						
					w,h = pixbuf.get_width(), pixbuf.get_height()
					self.add_table.attach(button,i%ADD_TABLE_WIDTH,i%ADD_TABLE_WIDTH+1,int(i/ADD_TABLE_WIDTH),int(i/ADD_TABLE_WIDTH)+1, gtk.SHRINK, gtk.SHRINK)
					i+=1
				except :
					pass
				
		self.add_table.show_all()
		
		self.cols = {}
		col =  gtk.TreeViewColumn("Name")
		cell = gtk.CellRendererPixbuf()
		col.pack_start(cell, expand=False)
		col.set_cell_data_func(cell, self.get_col_icon)
		cell = gtk.CellRendererText() 
		col.pack_start(cell, expand=False)
		col.set_cell_data_func(cell, self.get_col_name)
		col.set_resizable(True)
		self.treeview.append_column(col)
		self.cols["name"] = col
		
		
		col =  gtk.TreeViewColumn("Value")
		cell = gtk.CellRendererText() 
		col.pack_start(cell, expand=True)
		col.set_cell_data_func(cell, self.get_col_value)
		col.set_resizable(True)		
		self.treeview.append_column(col)
		self.cols["value"] = col
		
			
		self.TARGETS = [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),]		
		self.treeview.enable_model_drag_source( gtk.gdk.BUTTON1_MASK, self.TARGETS, gtk.gdk.ACTION_DEFAULT |  gtk.gdk.ACTION_MOVE)
		self.treeview.enable_model_drag_dest(self.TARGETS, gtk.gdk.ACTION_DEFAULT)

		self.treeview.connect("drag_data_get", self.drag_data_get_data)		
		self.treeview.connect("drag_data_received", self.drag_data_received_data)

		self.load(None,"test.xml")

		f = Feature("simp.ini",self.treestore_to_xml())
		fxml = f.to_xml()
		xml = self.treestore_to_xml()
		xml.append(fxml)
		self.treestore_from_xml(xml)
		
		self.tree_root = self.treestore.get_iter_root()

		self.test_button = self.glade.get_object("test")
		self.test_button.connect("clicked", self.test)
		self.test_button = self.glade.get_object("save")
		self.test_button.connect("clicked", self.save)
		self.test_button = self.glade.get_object("open")
		self.test_button.connect("clicked", self.load)
		self.test_button = self.glade.get_object("undo")
		self.test_button.connect("clicked", self.undo)
		self.test_button = self.glade.get_object("redo")
		self.test_button.connect("clicked", self.redo)

		
	def action(self, *arg) :
		xml = self.treestore_to_xml()
		self.undo_list = self.undo_list[:min(self.undo_pointer, UNDO_MAX_LEN-1)]
		self.undo_list.append(etree.tostring(xml))
		self.undo_pointer = len(self.undo_list)-1
		
	def undo(self, *arg) :
		if self.undo_pointer>0 :
			self.undo_pointer -= 1
			self.treestore_from_xml(etree.xml(self.undo_list[self.undo_pointer]))
			
	def redo(self, *arg) :
		if self.undo_pointer < len(self.undo_list)-1 :
			self.undo_pointer += 1
			self.treestore_from_xml(etree.xml(self.undo_list[self.undo_pointer]))
		
	def clear_undo(self, *arg) :
		self.undo_list = []
		self.undo_pointer = 0
	
	def test(self, *arg) :
		xml = self.treestore_to_xml()
		print etree.tostring(xml, pretty_print=True)

	def drag_data_get_data(self, treeview, context, selection, target_id, etime):
		treeselection = treeview.get_selection()
		model, iter = treeselection.get_selected()
		feature = self.treestore.get(iter,0)[0]
		selection.set('textn', 8, "1" )

	def move_before(self, src, dst, after = False, append = False) :
		src = self.treestore.get_string_from_iter(src)
		dst = self.treestore.get_string_from_iter(dst)		
		xml = self.treestore_to_xml()
		src = xml.find(".//*[@path='%s']"%src)		
		dst = xml.find(".//*[@path='%s']"%dst)
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
		 
	
	def drag_data_received_data(self, treeview, context, x, y, selection, info, etime) :
		treeselection = treeview.get_selection()
		model, src = treeselection.get_selected()
		drop_info = treeview.get_dest_row_at_pos(x, y)
		if self.treestore.get(src,0)[0].param["type"] in FEATURES :
			if drop_info :
				dst, position = drop_info
				dst = self.treestore.get_iter(dst)
				if position == gtk.TREE_VIEW_DROP_BEFORE :
					self.move_before(src, dst)
				elif  position == gtk.TREE_VIEW_DROP_AFTER:
					self.move_after(src, dst)
				else :	## drop inside
					self.append_node(src, dst)
				
			else :
				# pop to root
				root = model.get_iter_root()
				n = model.iter_n_children(root)
				dst = model.iter_nth_child(root,n-1)
				self.move_after(src,dst)
			
		#context.finish(True, True, etime)	
		return True

	def get_col_name(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).get_name() )
		
	def get_col_value(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).get_value() )

	def get_col_icon(self, column, cell, model, iter) :	
		cell.set_property('pixbuf', model.get_value(iter, 0).get_icon() )


	def treestore_to_xml_recursion(self, iter, xmlpath):
		while iter : 
			el = self.treestore.get(iter,0)[0]	
			path = self.treestore.get_path(iter)
			xmlpath_ = el.to_xml(xmlpath, self.treestore.get_string_from_iter(iter), self.treeview.row_expanded(path))
			# check for the childrens
			citer = self.treestore.iter_children(iter)
			if citer :
				self.treestore_to_xml_recursion(citer, xmlpath_)
			# check for next items
			iter = self.treestore.iter_next(iter)
				
	def treestore_to_xml(self, callback=None):
		xml = etree.Element("LinuxCNC-Features")
		self.treestore_to_xml_recursion(self.treestore.get_iter_root(), xml)
		#print etree.tostring(xml, pretty_print=True)
		return xml


	def treestore_from_xml_recursion(self, treestore, iter, xmlpath):
		for p in xmlpath :
			f = TreeFeature(p)
			tool_tip = f.param["tool_tip"] if "tool_tip" in f.param else None
			
			citer = treestore.append(iter, [f, tool_tip])
			if len(p) :
				self.treestore_from_xml_recursion(treestore, citer, p)
				

	def treestore_from_xml(self, xml, expand = True):
		treestore = gtk.TreeStore(object, str)
		self.treestore_from_xml_recursion(treestore, treestore.get_iter_root(), xml)		
		self.treestore = treestore
		self.treeview.set_model(self.treestore)
		if expand :
			def treestore_expand(model, path, iter, self) :
				p = model.get(iter,0)[0].param
				if "expanded" in p and p["expanded"] :
					self.treeview.expand_row(path, False)
			self.treestore.foreach(treestore_expand, self)
			

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
		
		
		
if __name__ == "__main__":
	features = Features()
	gtk.main()
