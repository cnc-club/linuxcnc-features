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

class FeatureParameter :
	def __init__(self, name="Parameter", value = 0, parametertype = "float", icon = "") :
		self.name = name
		self.value = value
		self.type = parametertype

	def get_value(self):
		return self.value

		
	def to_xml(self, xmlpath, path='') :
		etree.SubElement(path, "parameter", name=self.name)
		

PARAMETERS = ["string", "float", "int"]	
UNDO_MAX_LEN = 200
	
class Feature(): 
	def __init__(self, name="Feature", type="int", value="",  icon = "") :
		self.name = name
		self.value = value
		self.type = type
		
	def get_value(self):
		return self.value
	
	def to_xml(self, xmlpath, path, expanded=False) :
		print path 
		path = etree.SubElement(xmlpath, 
									self.type, 
									name = self.name, 
									path=str(path), 
									value=str(self.value),
									expanded = str(expanded) )
		
		return path

	def from_xml(self, xmlpath) :
		self.name = xmlpath.get("name")
		self.value = xmlpath.get("value")
		self.type =  xmlpath.tag.lower()
		self.expanded = xmlpath.get("expanded").lower()=="true"


class Features:

	def __init__(self):
		self.undo_list = []
		self.undo_pointer = []
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
		print iter
		selection.set('textn', 8, "1" )
		if feature.type in PARAMETERS and False:	
			print feature.type,"!!!!!!!!!!!!!!!!!!!"
			context.drag_abort(0)
			context.finish(True, True, etime)
			return 

	def move_before(self, src, dst, before = True) :
		src = self.treestore.get_string_from_iter(src)
		dst = self.treestore.get_string_from_iter(dst)		
		xml = self.treestore_to_xml()
		src = xml.find(".//*[@path='%s']"%src)		
		dst = xml.find(".//*[@path='%s']"%dst)
		if dst==None or src==None :		
			print "Error in dst, or src wile moving subtrees! (dst %s) (src %s)"%(dst,src)
			return
		if before :
			dst.getparent().insert(dst.getparent().index(dst), src) 
		else : 
			dst.getparent().insert(dst.getparent().index(dst)+1, src) 
		self.treestore_from_xml(xml)	

		
	
	
	def move_after(self, src, dst) :
		self.move_before(src, dst, before = False) 
	
	def drag_data_received_data(self, treeview, context, x, y, selection, info, etime) :
		treeselection = treeview.get_selection()
		model, src = treeselection.get_selected()
		drop_info = treeview.get_dest_row_at_pos(x, y)
		if drop_info :
			dst, position = drop_info
			dst = self.treestore.get_iter(dst)
			if (position == gtk.TREE_VIEW_DROP_BEFORE or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE) :
				self.move_before(src, dst)
			else:
				self.move_after(src, dst)
		else :
			# pop to root
			root = model.get_iter_root()
			n = model.iter_n_children(root)
			dst = model.iter_nth_child(root,n-1)
			self.move_after(src,dst)
			
		#context.finish(True, True, etime)	
		return True

	def get_col_name(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).name )
		
	def get_col_value(self, column, cell, model, iter) :	
		cell.set_property('text', model.get_value(iter, 0).get_value() )


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
			f = Feature()
			f.from_xml(p)
			citer = treestore.append(iter, [f])
			if len(p) :
				self.treestore_from_xml_recursion(treestore, citer, p)

	def treestore_from_xml(self, xml, expand = True):
		treestore = gtk.TreeStore(object)
		self.treestore_from_xml_recursion(treestore, treestore.get_iter_root(), xml)		
		self.treestore = treestore
		self.treeview.set_model(self.treestore)
		if expand :
			def treestore_expand(model, path, iter, self) :
				if model.get(iter,0)[0].expanded :
					self.treeview.expand_row(path, False)
			self.treestore.foreach(treestore_expand, self)
			
			

		###				path = treestore.get_path(iter)
		#		print path, iter
		#		if f.expanded and path!=None : self.treeview.expand_row(path, False)


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
