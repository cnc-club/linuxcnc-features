from points import P
from math import *
pi2 = pi*2

################################################################################
###		Process - is used to store data while creating Gcode
################################################################################
class Process:
	depth = -10
	depth_step = 1
	surface = 0 
	rappid = 5 
	feed = 1000
	penetration_feed = 400 
	penetration_angle = 45./180.*pi
	final = 0.4
	final_num = 3
	final_feed = 400 
	x,y,z = None,None,None
	gcode = ""
	current_depth = 0
	penetration_strategy = 0
	current_feed = None
	cut_feed = 0
	
	def p(self) : 
		return P(self.x,self.y)
		
	def rappid_move(self, x, y=None) :
		if x.__class__ == P :
			x,y = x.x,x.y
		self.to_rappid()
		if self.x==None or self.y== None or (self.x-x)**2 + (self.y-y)**2 > 1e-8 :
			self.g0(x, y)

	def g1(self,x,y=None,z=None, feed=None, g0=False) :
		if x.__class__ == P :
			x,y = x.x, x.y
		self.gcode += "G00" if g0 else "G01" 
		if x != None :
			self.gcode +=" X%s"%x
			self.x = x
		if y != None :
			self.gcode +=" Y%s"%y
			self.y = y
		if z != None :
			self.gcode +=" Z%s"%z
			self.z = z
		if feed != None and feed != self.current_feed:
			self.current_feed = feed
			self.gcode +=" F%s"%feed

			
		self.gcode += "\n"
		
	def g0(self,x,y=None,z=None) :
		self.g1(x,y,z,None,True)


	def to_surface(self) :	
		if self.z!=self.surface :
			self.g0(None,None,self.surface)

	def to_rappid(self) :	
		if self.z!=self.rappid :
			self.g0(None,None,self.rappid)
	


################################################################################
###		Biarc classes - Arc, Line and Biarc
################################################################################
class Arc():
	def __init__(self,st,end,c,a,r=None) :
		# a - arc's angle, it's not defining actual angle before now, but defines direction so it's value does not mather matters only the sign.
		if st.__class__ == P :  st = st.to_list()
		if end.__class__ == P : end = end.to_list()
		if c.__class__ == P :   c = c.to_list()
		self.st = P(st)
		self.end = P(end)
		self.c = P(c)
		if r == None : self.r = (P(st)-P(c)).mag()
		else: self.r = r
		self.a = ( (self.st-self.c).angle() - (self.end-self.c).angle() ) % pi2
		if a>0 : self.a -= pi2
		self.a *= -1.
		self.cp = (self.st-self.c).rot(self.a/2)+self.c # central point of an arc

	def __repr__(self) :
		return "Arc: s%s e%s c%s r%.2f a%.2f (l=%.3f) " % (self.st,self.end,self.c,self.r,self.a,self.length())

	def copy(self) :
		return Arc(self.st,self.end,self.c,self.a,self.r)	

	def rebuild(self,st=None,end=None,c=None,a=None,r=None) : 
		if st==None: st=self.st
		if end==None: end=self.end
		if c==None: c=self.c
		if a==None: a=self.a
		if r==None: r=self.r
		self.__init__(st,end,c,a,r)

	def get_t_at_point(self, p, y=None) :
		if y!=None : p = P(p,y)
		if not self.point_inside_angle(p) : return -1.
		return abs( acos( (self.st-self.c).dot((p-self.c))/(self.r**2) )/pi ) # consuming all arcs les than 180 deg

		
	def point_inside_angle(self,p,y=None) :  # TODO need to be done faster! 
		if y!=None : p = P(p,y)
		if (p-self.c).l2() != self.r**2 :  # p is not on the arc, lets move it there
			p = self.c+(p-self.c).unit()*self.r
		warn( (self.cp-self.c).dot(p-self.c),self.r**2, (self.cp-self.c).dot(p-self.c)/self.r**2)
		try:
			abs(  acos( (self.cp-self.c).dot(p-self.c) /self.r**2  )  )  <  abs(self.a/2)
		except :

			return True	 
		return abs(  acos( (self.cp-self.c).dot(p-self.c) /self.r**2  )  )  <  abs(self.a/2) 

	def bounds(self) : 
		# first get bounds of start/end 
		x1,y1, x2,y2 =  ( min(self.st.x,self.end.x),min(self.st.y,self.end.y),
						  max(self.st.x,self.end.x),max(self.st.y,self.end.y) )
		# Then check 0,pi/2,pi and 2pi angles. 
		if self.point_Gde_angle(self.c+P(0,self.r)) :
			y2 = max(y2, self.c.y+self.r)
		if self.point_inside_angle(self.c+P(0,-self.r)) :
			y1 = min(y1, self.c.y-self.r)
		if self.point_inside_angle(self.c+P(-self.r,0)) :
			x1 = min(x1, self.c.x-self.r)
		if self.point_inside_angle(self.c+P(self.r,0)) :
			x2 = max(x2, self.c.x+self.r)
		return x1,y1, x2,y2

	def head(self,p):
		self.rebuild(end=p)

	def tail(self,p):
		self.rebuild(st=p)

	def offset(self, r):
		oldr = self.r
		if self.a>0 :
			self.r = self.r + r
		else :
			self.r = self.r - r
		
		if self.r != 0 :
			self.st = self.c + (self.st-self.c)*self.r/oldr
			self.end = self.c + (self.end-self.c)*self.r/oldr
		self.rebuild()	
			
	def length(self):
		return abs(self.a*self.r)
	

	def check_intersection(self, points): 
		res = []
 		for p in points :
 			if self.point_inside_angle(p) :
 				res.append(p)
		return res		
		
	def intersect(self,b) :
		if b.__class__ == Line :
			return b.intersect(self)
		else : 
			# taken from http://paulbourke.net/geometry/2circle/
			if (self.st-b.st).l2()<1e-10 and (self.end-b.end).l2()<1e-10 : return [self.st,self.end]
			r0 = self.r 
			r1 = b.r
			P0 = self.c
			P1 = b.c
			d2 = (P0-P1).l2() 
			d = sqrt(d2)
			if d>r0+r1  or r0+r1<=0 or d2<(r0-r1)**2 :
				return []
			if d2==0 and r0==r1 :
				return self.check_intersection( b.check_intersection(
					[self.st, self.end, b.st, b.end] ) )
			if d == r0+r1  :
				return self.check_intersection( b.check_intersection(
								[P0 + (P1 - P0)*r0/(r0+r1)]  ) )
			else: 
				a = (r0**2 - r1**2 + d2)/(2.*d)
				P2 = P0 + a*(P1-P0)/d
				h = r0**2-a**2
				h = sqrt(h) if h>0 else 0. 
				return self.check_intersection(b.check_intersection( [
							P([P2.x+h*(P1.y-P0.y)/d, P2.y-h*(P1.x-P0.x)/d]),
							P([P2.x-h*(P1.y-P0.y)/d, P2.y+h*(P1.x-P0.x)/d]),
						] ))

	def point_d2(self, p):
		if self.point_inside_angle(p) :
			l = (p-self.c).mag()
			if l == 0 : return self.r**2
			else : return ((p-self.c)*(1 - self.r/l)).l2()
		else :
			return min( (p-self.st).l2(), (p-self.end).l2() )	


			
class Line():
	def __init__(self,st,end):
		#debugger.add_debugger_to_class(self.__class__)
		if st.__class__ == P :  st = st.to_list()
		if end.__class__ == P :	end = end.to_list()
		self.st = P(st)
		self.end = P(end)
		self.l = self.length() 
		if self.l != 0 :
			self.n = ((self.end-self.st)/self.l).ccw()
		else: 
			self.n = [0,1]
	
	def reverse(self):
		return Line(self.end,self.st)

	def to_gcode(self, process,t=0.):
		process.gcode += "\n(%s)->Start at t=%s\n"%(self,t)	
		if t>0 : # process from t - split line and process it from start
			st = self.st + (self.end-self.st)*t
			line = Line(st,self.end)
			t1 = line.to_gcode(process, 0.)
			l = line.l*t1
			t += l/self.l
			return t
		else : # process from the start	

			if (process.p()-self.st).l2()>1e-5 :
				process.rappid_move(self.st)
			
			if process.z > process.surface :
				process.to_surface()
		
			if process.z > process.current_depth :
				# need to penetrate
				pl = (process.z-process.current_depth)/tan(process.penetration_angle)
				if pl>=self.l :
					process.g1(self.end, None, process.z-self.l/tan(process.penetration_angle), process.penetration_feed)
					return 1.
				else :
					process.g1(self.st + (self.end-self.st)*pl/self.l, None, process.current_depth, process.penetration_feed)
					return pl/self.l # return t
			else :	
				if self.l < process.L - process.l :
					process.g1(self.end, feed=process.cut_feed)
					process.l += self.l
					return 1.
				else :	
					process.g1(self.st + (self.end-self.st)*(process.L-process.l)/self.l, feed=process.cut_feed)			
					t = (process.L-process.l)/self.l
					process.l = process.L
					return t
			
	def get_t_at_point(self,p) :
		if self.st.x-self.end.x != 0 :
			return (self.st.x-p.x)/(self.st.x-self.end.x)
		else :
			return (self.st.y-p.y)/(self.st.y-self.end.y)
			
	def __repr__(self) :
		return "Line: %s %s (l=%0.3f)" % (self.st,self.end,self.l)
				
	def copy(self) : 
		return Line(self.st,self.end)
	
	def rebuild(self,st=None,end=None) : 
		if st==None: st=self.st
		if end==None: end=self.end
		self.__init__(st,end)
	
	def bounds(self) :
		return  ( min(self.st.x,self.end.x),min(self.st.y,self.end.y),
				  max(self.st.x,self.end.x),max(self.st.y,self.end.y) )
	
	def head(self,p):
		self.rebuild(end=p)

	def tail(self,p):
		self.rebuild(st=p)

	def offset(self, r):
		self.st -= self.n*r
		self.end -= self.n*r
		self.rebuild()
		
	def l2(self): return (self.st-self.end).l2()
	def length(self): return (self.st-self.end).mag()
	
	def intersect(self,b, false_intersection = False) :
		if b.__class__ == Line :
			if self.l < 10e-8 or b.l < 10e-8 : return []
			v1 = self.end - self.st
			v2 = b.end - b.st
			x = v1.x*v2.y - v2.x*v1.y 
			if x == 0 :
				# lines are parallel
				res = []

				if (self.st.x-b.st.x)*v1.y - (self.st.y-b.st.y)*v1.x  == 0:
					# lines are the same
					if v1.x != 0 :
						if 0<=(self.st.x-b.st.x)/v2.x<=1 :  res.append(self.st)
						if 0<=(self.end.x-b.st.x)/v2.x<=1 :  res.append(self.end)
						if 0<=(b.st.x-self.st.x)/v1.x<=1 :  res.append(b.st)
						if 0<=(b.end.x-b.st.x)/v1.x<=1 :  res.append(b.end)
					else :
						if 0<=(self.st.y-b.st.y)/v2.y<=1 :  res.append(self.st)
						if 0<=(self.end.y-b.st.y)/v2.y<=1 :  res.append(self.end)
						if 0<=(b.st.y-self.st.y)/v1.y<=1 :  res.append(b.st)
						if 0<=(b.end.y-b.st.y)/v1.y<=1 :  res.append(b.end)
				return res
			else :
				t1 = ( v2.x*(self.st.y-b.st.y) - v2.y*(self.st.x-b.st.x) ) / x
				t2 = ( v1.x*(self.st.y-b.st.y) - v1.y*(self.st.x-b.st.x) ) / x
				
				if 0<=t1<=1 and 0<=t2<=1 or false_intersection : return [ self.st+v1*t1 ]	
				else : return []					
		else: 
			# taken from http://mathworld.wolfram.com/Circle-LineIntersection.html
			x1 = self.st.x - b.c.x
			x2 = self.end.x - b.c.x
			y1 = self.st.y - b.c.y
			y2 = self.end.y - b.c.y
			dx = x2-x1
			dy = y2-y1
			D = x1*y2-x2*y1
			dr = dx*dx+dy*dy
			descr = b.r**2*dr-D*D
			if descr<0 : return []
			if descr==0 : return self.check_intersection(b.check_intersection([ P([D*dy/dr+b.c.x,-D*dx/dr+b.c.y]) ]))
			sign = -1. if dy<0 else 1.
			descr = sqrt(descr)
			points = [
						 P( [ (D*dy+sign*dx*descr)/dr+b.c.x, (-D*dx+abs(dy)*descr)/dr+b.c.y ] ), 
						 P( [ (D*dy-sign*dx*descr)/dr+b.c.x, (-D*dx-abs(dy)*descr)/dr+b.c.y ] )
					]
			if false_intersection :
				return points
			else: 
				return self.check_intersection(b.check_intersection( points ))
							

	def check_intersection(self, points):
		res = []
		for p in points :
			if ((self.st.x-1e-7<=p.x<=self.end.x+1e-7 or self.end.x-1e-7<=p.x<=self.st.x+1e-7)
				and 
				(self.st.y-1e-7<=p.y<=self.end.y+1e-7 or self.end.y-1e-7<=p.y<=self.st.y+1e-7)) :
			   		res.append(p)
		return res
	
	def point_d2(self, p) : 
		w0 = p - self.st
		v = self.end - self.st
		c1 = w0.dot(v)
		if c1 <= 0 :
			return w0.l2()
		c2 = v.dot(v)
		if c2 <= c1 :	
			return (p-self.end).l2()
			
		return ((self.st+c1/c2*v)-p).l2()

			
class LineArc:
	def __init__(self, items=None):
		if items == None :
			self.items = []
		else: 	
			self.items = items
		
	def copy(self) :
		b = LineArc()
		for it in self.items :
			b.items.append(it)
		return b		
	
	def l(self) : 
		return sum([ i.length() for i in self.items ])
	
	
	def close(self) :
			if (self.items[0].st-self.items[-1].end).l2()>10e-10 :
				self.tems.append(Line(self.items[-1].end,self.items[0].st))
	
	def check_close(self) :
		return len(self.items)>0 and (self.items[0].st-self.items[-1].end).l2()<1e-8
	
	def to_gcode(self) :
		if len(self.items)==0 : return ""
		self.process = Process()
		l = 0 # current pass length
		L = self.l() # total path length
		self.process.L = L
		self.process.current_depth = self.process.surface
		self.process.l = 0
		i,t = 0,0.
		w,w1 = 0,0
		last_pass = None	
		self.process.to_rappid()
		self.process.rappid_move(self.items[0].st)
			
		while self.process.current_depth > self.process.depth and w<15 :
			w += 1
			if self.process.current_depth > self.process.depth+self.process.final*self.process.final_num :
				self.process.current_depth -= self.process.depth_step
				self.process.current_depth = max(self.process.current_depth, self.process.depth + self.process.final*self.process.final_num)
				self.process.cut_feed = self.process.feed
			else :	
				self.process.current_depth -= self.process.final
				self.process.current_depth = max(self.process.current_depth, self.process.depth)				
				self.process.cut_feed = self.process.final_feed

			self.process.gcode += "(New Depth = %s)"%self.process.current_depth
			
			self.process.l = 0
			
			if self.check_close() : # path is closed do the spiral
				
				while self.process.l<L :
					# t- start/end point
					t = self.items[i].to_gcode(self.process,t)
					if t>=1 : 
						i = (i+1)%len(self.items)
						t=0
			else :
				if self.process.penetration_strategy == 0 : # saw /|/|/|/|/|/|/|/|
					# penetrate
					if last_pass != None :
						self.process.rappid_move(self.items[0].st)
						self.process.g0(None,None,last_pass)
					while self.process.z > self.process.current_depth :
						t = self.items[i].to_gcode(self.process,t)
					last_pass = self.process.z
					# now reverse and go back
					t = 1.-t
					while i>=0 or t>0. :
						self.process.gcode += "(i=%s t=%s)\n"%(i,t)
						self.process.l = 0
						self.process.gcode += "(Reversed %s)\n"%self.items[i].reverse()
						t = self.items[i].reverse().to_gcode(self.process,t)
						t = 1.-t	
						i -= 1

				else : # triangle /\/\/\/\/\/\/\/\/\
					pass
					
				i,t = 0,0. 
				# now we should be at the depth and at the start of the path
				# process the path again
				self.process.l = 0
				while self.process.l<L :
				# t- start/end point
					t = self.items[i].to_gcode(self.process,t)
					if t>=1 : 
						i = (i+1)%len(self.items)
						t=0
					
		self.process.to_rappid()
		return self.process.gcode
				
		
	def check(self, check_close = True) :
		if check_close : self.check_close()
				
	
	def clean(self) :			
		# clean biarc from 0 length elements.
		i = 0
		while i<len(self.items) :
			j = 0
			closed = self.items[i][0].st.near(self.items[i][-1].end)
			while j<len(self.items[i]) :
				item = self.items[i][j]
				if ( item.__class__==Line and item.l<1e-3 or
					 item.__class__==Arc and abs(item.r)<1e-3 or
					 (item.st-item.end).l2()<1e-5   )  :
					 		if not closed and j==0 : 
					 			self.items[i][j+1].rebuild(st=self.items[i][j].st)
					 		else: 
					 			self.items[i][j-1].rebuild(end=self.items[i][j].end)
							self.items[i][j:j+1] = []
							continue
				j += 1		
			if self.items[i]==[] :
				self.items[i:i+1] = []
				continue
			i += 1	
	
	def offset_items(self,r) :
		for item in self.items :
			item.offset(r)
		self.clean()
		self.connect(r)
		
		
	def offset(self,r, tolerance = 0.0001) :
		self.close()
		self.check()
		self.clean()
		orig = self.copy()

		self.offset_items(r)
		self.check()	

	def connect_items_with_arc(self, a, b, r) :
		# get normals
		if a.__class__ == Line : nst = a.n
		else : nst = (a.end-a.c)/a.r
		if b.__class__ == Line : nend = b.n
		else : nend = (b.st-b.c)/b.r

		# get center
		if a.__class__ == Line : c = a.end+a.n*r
		elif b.__class__ == Line : c = b.st+b.n*r
		else:
			c = a.end + (a.end - a.c)*r/a.r*(1. if a.a < 0 else -1.)
		# get angle sign
		ang = -1. if  (a.end-c).cross(b.st-c)<0 else  1.
		if abs(ang) <= 1e-10 : return None
		# return arc
#		draw_pointer([a.end,c,b.st], layer=gcodetools.layers[-1], color="orange", figure="line")
		return Arc(a.end, b.st, c, ang)
		
		
	def connect(self, r):				
			while i < len(self.items) :
				a,b = self.items[i],self.items[(i+1)%len(self.items)]
				if (a.end-b.st).l2()<1e-10:
					if a.__class__==Line :
						a.__init__(a.st,b.st)
					else :
						a.__init__(a.st,b.st,a.c,a.a)
						
				else :
					points = a.intersect(b)
					if len(points)==0 : 
						arc = self.connect_items_with_arc(a,b,r)
						if arc!=None:
							self.items.insert(i+1,arc)
							i += 1
					else :
						# take closest point to the start of a
						l2 = None
						for p in points :
							if l2==None or (point-a.st).l2()<l2 : point = p 
						# now we've got only one point		
						a.head(point)
						b.tail(point)
#					for p in a.intersect(b) : 
#						draw_pointer(p.to_list(), layer=gcodetools.layers[-1], color="orange")
				i += 1				
				
						

