LinuxCNC Features - native realtime CAM for LinuxCNC - aka new NGCGUI


	1.	Install
--------------------------------------------------------------------------------

1. Move everything to /usr/share/pyshared/gladevcp/

2. Create links into /usr/lib/pymodules/python2.6/gladevcp

3. Change hal_pythonplugin.py in /usr/share/pyshared/gladevcp/hal_pythonplugin.py
	Add:
		from features import Features

4. Change hal_python.xml in /usr/share/glade3/catalogs glade3 can be glade2
	Add:
		<glade-widget-class name="Features" generic-name="features" title="features">
		    <properties>
		        <property id="size" query="False" default="1" visible="False"/>
		        <property id="spacing" query="False" default="0" visible="False"/>
		        <property id="homogeneous" query="False" default="0" visible="False"/>
		    </properties>
		</glade-widget-class>

		....
		
	   <glade-widget-class-ref name="Features"/>



	2.	Usage
--------------------------------------------------------------------------------

1. Param subsitutions
	#param_name can be used to substitude parameters from the feature. 
	#self_id - unique id made of feature Name + smallest integer id. 

2. Eval and exec
	<eval>"hello world!"</eval> everything inside <eval> tag will be passed
	trought python's eval function. 
	
	<exec>print "hello world"</exec> allmost the same but will take all printed data.
	
	you can use self as feature's self.
	
	
3. Including Gcode
	G-code ngc files can be included by using one of the following functions: 
		<eval>self.include_once("rotate-xy.ngc")</eval>
		<eval>self.include("rotate-xy.ngc")</eval>
