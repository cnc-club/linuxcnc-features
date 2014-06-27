from points import P
from biarc import *
import sys
sys.stderr=sys.stdout
import re
log_level=1

def log(*arg):
	if log_level > 0 :
		for s in arg :
			print s,", ",
		print 


class MillDraw:
	def __init__(self, id=None):
		self.path = LineArc()
		 
	def draw_start(self,x,y):
		self.items = []
		# item g x y z i j k
		self.st = P(x,y) 
		self.p = P(x,y)

	def line_to(self,x,y):
		self.path.items.append( Line(self.p, [x,y]) )
		self.p = P(x,y)
		print "Line to (%s, %s)"%(x,y)
	
	def arc_to(self,x,y,i,j):
		self.path.items.append( Line(self.p, [x,y]) )
		self.p = P(x,y)
		print "Arc to (%s, %s)-(%s, %s)"%(x,y,i,j)

	def close(self) :
		self.path.items.append( Line(self.p, self.st) )
	

	def process(self):
		self.exp = []
		self.line_num = 0		
		gcode = self.path.to_gcode()
		for s in gcode.split("\n") :
			s = re.sub("\(.*\)","",s)
			s = re.sub(";.*","",s)
			r = re.search("(?i)G0?(1|0)\s*(X([-0-9\.]+))?\s*(Y([-0-9\.]+))?\s*(Z([-0-9\.]+))?\s*(F([-0-9\.]+))?",s) 
			if r :
				r = r.groups()
				g1 = 10*(r[2]!=None) + 20*(r[4]!=None) + 40*(r[6]!=None)
				g = (int(r[0])*100+g1, r[2],r[4],r[6], None, None, None,r[8])
				self.exp.append(g)
		self.exp.append((-1, None, None, None, None, None, None, None))		


	def get_line(self) :

			if self.line_num < len(self.exp) :
				self.line_num += 1
				return self.exp[self.line_num-1]
			else :
				return (-1, None, None, None, None, None, None, None)
		
#draw = MillDraw()
#draw.path.items.append(Line([0,0],[0,100]))
#draw.path.items.append(Line([0,100],[100,100]))
#draw.path.items.append(Line([100,100],[100,0]))
#draw.path.items.append(Line([100,0],[0,0]))
#draw.process()

