#!/usr/bin/env python
# coding: utf-8
import sys
import os

import pygtk
pygtk.require('2.0')

import gtk
import gtk.glade
from lxml import etree

import gobject

class FeatureParameter :
	def __init__(self, name="Parameter", value = 0, parametertype = "float", icon = "") :
		self.name = name
		self.value = value
		self.type = parametertype

	def get_value(self):
		return self.value

		
	def to_xml(self, path) :
		etree.SubElement(path, "parameter", name=self.name)
	
	
class Feature(): 
	def __init__(self, name="Feature", type="int", value="",  icon = "") :
		self.name = name
		self.value = value
		self.type = type
		
	def get_value(self):
		return self.value
	
	def to_xml(self, path) :
		path = etree.SubElement(path, self.type, name = self.name)
		return path

	def from_xml(self, path) :
		self.name = path.get("name")
		self.value = path.get("value")
		self.type = path.get("type")



#		for p in self.param :
#			p.to_xml(path)



class Features:

	def __init__(self):
		self.glade = gtk.Builder()
		self.glade.add_from_file("features.glade")
		self.glade.connect_signals(self)
		self.window = self.glade.get_object("MainWindow")
		self.window.show_all()	
		self.window.connect("destroy", gtk.main_quit)
		self.treeview = self.glade.get_object("treeview1")
		self.treestore = gtk.TreeStore(object)
		self.treeview.set_model(self.treestore)
		
		columns = [
					["name",self.get_col_name],
					["value",self.get_col_value],
				]	
		self.cols = []
		for c in columns:
			cell = gtk.CellRendererText() 
			self.cols.append( gtk.TreeViewColumn(c[0], cell) )
			self.cols[-1].set_cell_data_func(cell, c[1])
			self.treeview.append_column(self.cols[-1])

		self.TARGETS = [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),]		
		self.treeview.enable_model_drag_source( gtk.gdk.BUTTON1_MASK,
												self.TARGETS,
												gtk.gdk.ACTION_DEFAULT|
												gtk.gdk.ACTION_MOVE)
		self.treeview.enable_model_drag_dest(self.TARGETS,
									gtk.gdk.ACTION_DEFAULT)

		self.treeview.connect("drag_data_get", self.drag_data_get_data)		
		self.treeview.connect("drag_data_received", self.drag_data_received_data)
			
		self.load(None,"test.xml")

		self.tree_root = self.treestore.get_iter_root()

		
		self.tree_root = self.treestore.get_iter_root()

		self.test_button = self.glade.get_object("test")
		self.test_button.connect("clicked", self.treestore_to_xml)
		
		self.test_button = self.glade.get_object("save")
		self.test_button.connect("clicked", self.save)
		self.test_button = self.glade.get_object("open")
		self.test_button.connect("clicked", self.load)
	

	def drag_data_get_data(self, treeview, context, selection, target_id, etime):
		treeselection = treeview.get_selection()
		model, iter = treeselection.get_selected()
		data = model.get_value(iter, 0)
		selection.set(selection.target, 8, data)
	
	def drag_data_received_data(self, treeview, context, x, y, selection, info, etime) :
		model = treeview.get_model()
		data = selection.data
		drop_info = treeview.get_dest_row_at_pos(x, y)
		if drop_info:
				path, position = drop_info
				iter = model.get_iter(path)
				print iter
				if (position == gtk.TREE_VIEW_DROP_BEFORE
					or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
					model.insert_before(iter, [data])
				else:
					model.insert_after(iter, [data])
		else:
			model.append([data])
		if context.action == gtk.gdk.ACTION_MOVE:
			context.finish(True, True, etime)
		return

		
	def get_col_name(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).name )
		
	def get_col_value(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).get_value() )


	def treestore_to_xml_recursion(self, path, xmlpath):
		while path : 
			el = self.treestore.get(path,0)[0]	
			
			xmlpath_ = el.to_xml(xmlpath)
			# check for the childrens
			cpath = self.treestore.iter_children(path)
			if cpath :
				self.treestore_to_xml_recursion(cpath, xmlpath_)
			# check for next items
			path = self.treestore.iter_next(path)

				
	def treestore_to_xml(self, callback=None):
		xml = etree.Element("LinuxCNC-Features")
		self.treestore_to_xml_recursion(self.treestore.get_iter_root(), xml)
		print etree.tostring(xml, pretty_print=True)
		return xml


	def treestore_from_xml_recursion(self, treestore, path, xmlpath):
		for p in xmlpath :
			f = Feature()
			f.from_xml(p)
			cpath = treestore.append(path, [f])
			if len(p) :
				self.treestore_from_xml_recursion(treestore, cpath, p)

		

	def treestore_from_xml(self, xml):
		treestore = gtk.TreeStore(object)
		self.treestore_from_xml_recursion(treestore, treestore.get_iter_root(), xml)		
		self.treestore = treestore
		self.treeview.set_model(self.treestore)



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
