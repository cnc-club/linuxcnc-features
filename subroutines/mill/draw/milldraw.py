from points import P
from biarc import *
from math import *
import sys
sys.stderr=sys.stdout
import re
import subprocess
import os
log_level=1



def log(*arg):
	if log_level > 0 :
		for s in arg :
			print s,", ",
		print 



class MillDraw:
	def __init__(self):
		self.path = LineArc()
		 
	def draw_start(self,x,y) :
		self.st = P(x,y) 
		self.p = P(x,y)
		self.path = LineArc()		

	def done(self) :
		self.path = LineArc()		

	def line_to(self,x,y):
		self.path.items.append( Line(self.p, [x,y]) )
		self.p = P(x,y)
		print "Line to (%s, %s)"%(x,y)

	def arc_to_xyr(self,a,x,y,r, in_out=0) :
		end = P(x,y)
		st = self.p
		c1 = (st+end)/2
		
		if (st-end).l2()<1.e-10 : 
			subprocess.Popen(['zenity', '--warning', '--timeout=3',
							'--text', ('Arc from %s-%s was replaced by the line because of start/end point are the same.\n'+
							'r=%s, st %s, end %s.')%(r,st,end)])
			self.line_to(x,y)			
			return

		b = r**2-(st-end).l2()/4.
		if b<0 : 
			subprocess.Popen(['zenity', '--warning', '--timeout=3',
							'--text', ('Arc from %s-%s was replaced by the line because of given radius to small.\n'+
							'r=%s, st %s, end %s. Should be at least r=%s')%(st,end,r,st,end,sqrt((st-end).l2()/4.) )])
			self.line_to(x,y)			
			return
		n = (end-st).unit()
		n = n.cw() if a==2 else n.ccw()
		c = c1 + n*sqrt(b)
		c = c-st
		if in_out > 0 : 
			a = 5-a # swap direction 2,3 -> 3,2
		self.arc_to_xyij(a,x,y,c.x,c.y)
			
	
	def arc_to_xyij(self,a,x,y,i,j): # a=2|3 => a*2-5=-1|1
		end = P(x,y)
		st = self.p
		c = st+P(i,j) 
		r1,r2 = (st-c).l2(), (c-end).l2()
		if  abs(r1-r2) > 1.e-6 :	# check radiuses at the start/end of the arc
			r1,r2 = (st-c).mag(), (c-end).mag()
			subprocess.Popen(['zenity', '--warning', '--timeout=3',
							'--text', ('Arc from %s-%s was replaced by the line because of start and end raduises are not equal.\n'+
							'r1=%s, r2=%s, st %s, end %s, center %s')%(st,end,r1,r2,st,end,c)])
			self.line_to(x,y)			
		elif r1<1e-6 or r2<1e-6 :
			r1,r2 = (st-c).mag(), (c-end).mag()
			subprocess.Popen(['zenity', '--warning', '--timeout=3',
							'--text', ('Arc from %s-%s was replaced by the line because of radius too small.\n'+
							'r1=%s, r2=%s, st %s, end %s, center %s')%(st,end,r1,r2,st,end,c)])
			self.line_to(x,y)				
		else :
			self.path.items.append( Arc(st, end, c, a*2-5) )
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
			r = re.search("(?i)S([-0-9\.]+)",s)  
			if r :
				r = r.groups()
				self.exp.append((-100,r[0], None, None, None, None, None, None))

			r = re.search("(?i)G0?(1|0)\s*(X([-0-9\.]+))?\s*(Y([-0-9\.]+))?\s*(Z([-0-9\.]+))?\s*(F([-0-9\.]+))?",s) 
			if r :
				r = r.groups()
				g1 = 10*(r[2]!=None) + 20*(r[4]!=None) + 40*(r[6]!=None)
				g = (int(r[0])*100+g1, r[2], r[4], r[6], None, None, None, r[8])
				self.exp.append(g)

			r = re.search("(?i)G0?(2|3)\s*(X([-0-9\.]+))?\s*(Y([-0-9\.]+))?\s*(I([-0-9\.]+))?\s*(J([-0-9\.]+))?\s*(Z([-0-9\.]+))?\s*(F([-0-9\.]+))?",s) 
			if r :
				r = r.groups()
				g1 = 1*(r[2]!=None) + 2*(r[4]!=None) + 4*(r[6]!=None) + 8*(r[8]!=None) + 16*(r[10]!=None)
				g = (int(r[0])*100+g1, r[2], r[4], r[10], r[6], r[8], None, r[12])
				self.exp.append(g)

		self.exp.append((-1, None, None, None, None, None, None, None))		


	def get_line(self) :

			if self.line_num < len(self.exp) :
				self.line_num += 1
				return self.exp[self.line_num-1]
			else :
				return (-1, None, None, None, None, None, None, None)



if __name__ == "__main__" :
	draw = MillDraw()
	draw.draw_start(0,0)
	draw.line_to(0,0)
	draw.arc_to_xyr(3,10,0,4)	
	draw.path.process.penetration_angle = 30./180.*pi
	for i in draw.path.items:
		print i
		
	draw.process()
	
	print draw.path.process.gcode
