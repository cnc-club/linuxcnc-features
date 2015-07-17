LinuxCNC Features - native realtime CAM for LinuxCNC - aka new NGCGUI


0.	Simple usage
--------------------------------------------------------------------------------
1. You can use LinuxCNC Features in "stand alone" mode. It is almost the same
	except that the Features are not included into Axis window and just lays 
	in a sepparate window. Everything else should work the same including
	preview in Axis!
	
	To use LinuxCNC Features in stand alone mode, just start them after you
	have started LinuxCNC providing path to your LinuxCNC ini file in 
	--ini parameter
	
	Example:
	(in the directory with features.py)
	```sh
	./features.py --ini=/home/nick/linuxcnc/configs/sim/axis/axis_mm.ini
	```


1.	Install
--------------------------------------------------------------------------------

1. Move everything to /usr/share/pyshared/gladevcp/
	Or better create links there:
	```sh
	cd /usr/share/pyshared/gladevcp/
	sudo ln /__full-path-to-git-repository__/features.py -s
	sudo ln /__full-path-to-git-repository__/features.glade -s
	sudo ln /__full-path-to-git-repository__/subroutines -s
	```	


2. Install python-lxml 
	```sh
	sudo apt-get install python-lxml 
	```

3. Create links into /usr/lib/pymodules/python2.6/gladevcp


	```sh
	cd /usr/lib/pymodules/python2.6/gladevcp
	sudo ln /usr/share/pyshared/gladevcp/features.py -s
	sudo ln /usr/share/pyshared/gladevcp/features.glade -s
	sudo ln /usr/share/pyshared/gladevcp/subroutines -s
	```

4. Change hal_pythonplugin.py in /usr/share/pyshared/gladevcp/hal_pythonplugin.py
	Add (find calculator add after :)):
	```python
	from features import Features
	```	

5. Change hal_python.xml in /usr/share/glade3/catalogs glade3 can be glade2
	
	Add (find first calculator add after :)):
	```xml
		<glade-widget-class name="Features" generic-name="features" title="features">
		    <properties>
		        <property id="size" query="False" default="1" visible="False"/>
		        <property id="spacing" query="False" default="0" visible="False"/>
		        <property id="homogeneous" query="False" default="0" visible="False"/>
		    </properties>
		</glade-widget-class>
	```
	
	 Add (find second calculator add after :)):
	```xml
		<glade-widget-class-ref name="Features"/>
	```

6. Translations:
	Make links in your system locale directories to translation files
	```sh
	cd /usr/share/locale/<<<YOUR LOCALE>>>/LC_MESSAGES
	sudo ln /<full path to features sourse>/locale/<<<YOUR LOCALE>>>/LC_MESSAGES/linuxcnc-features.mo -s
	```
	Example:
	```sh
	cd /usr/share/locale/ru/LC_MESSAGES
	sudo ln /home/nick/Design/cnc-club.ru/linuxcnc/features/locale/ru/LC_MESSAGES/linuxcnc-features.mo -s
	```

1.1	Usage
--------------------------------------------------------------------------------

After compliting install procedure, you can add features widget into any your gladevcp panel. 
Or you can just use "features only" panel from this repository. 



2.	Extending subroutines
--------------------------------------------------------------------------------

1. Param subsitutions
	"#param_name" can be used to substitude parameters from the feature. 
	"#self_id" - unique id made of feature Name + smallest integer id. 

2. Eval and exec
	```xml
	<eval>"hello world!"</eval>
	```
	everything inside &lt;eval&gt; tag will be passed
	trought python's eval function. 
	
	```xml
	<exec>print "hello world"</exec>
	```
	allmost the same but will take all printed data.
	
	you can use self as feature's self.

3. Import 
	```xml
	<import>filename<import>
	```
	will import file into feature text before proceccing.	
	
3. Including Gcode
	G-code ngc files can be included by using one of the following functions: 
	```xml
		<eval>self.include_once("rotate-xy.ngc")</eval>
		<eval>self.include("rotate-xy.ngc")</eval>
	```

--------------------------------------------------------------------------------

Some information on Russian can be obtained here: http://cnc-club.ru/forum/viewtopic.php?f=15&t=3124&p=72441#p72441
