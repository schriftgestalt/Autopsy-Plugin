#MenuTitle: Autopsy 1.3
# encoding: utf-8



########################################################################
#
#   Autopsy Visual Font Auditing
#   1.3
#
#   Version for Glyphs (glyphsapp.com)
#   (c) 2009 by Yanone
#   2013 Georg Seifert, porting to use CoreGraphics instead of RepordLab to write PDF
#   2016 Jens Kutilek, fixes
#
#   http://www.yanone.de/typedesign/autopsy/
#
#   GPLv3 or later
#
########################################################################


from GlyphsApp import *
from Foundation import NSURL, NSMakeRect, NSTemporaryDirectory
from AppKit import NSFont, NSColor, NSAttributedString, NSBezierPath, NSGraphicsContext, NSFontAttributeName, NSForegroundColorAttributeName
import time, os, string, math, random
import traceback
from Quartz.CoreGraphics import CGRectMake, CGPDFContextCreateWithURL, CGPDFContextBeginPage, CGPDFContextEndPage, CGPDFContextClose



cm = 72/2.54
mm = cm / 10
A4 = (595.276, 841.89)
letter = (612, 792)
Portrait = 0

ratio = 0
__all__ = ["runAutopsy"]

##### Misc.

class Ddict(dict):
	def __init__(self, default=None):
		self.default = default
	   
	def __getitem__(self, key):
		if not self.has_key(key):
			self[key] = self.default()
		return dict.__getitem__(self, key)

##### Settings

programname = 'Autopsy'
programversion = '1.3'
releasedate = '201604121821'
verbose = False

availablegraphs = ('width', 'bboxwidth', 'bboxheight', 'highestpoint', 'lowestpoint', 'leftsidebearing', 'rightsidebearing')

graphrealnames = {
	'width' : 'Width',
	'bboxwidth' : 'BBox Width',
	'bboxheight' : 'BBox Height',
	'highestpoint' : 'BBox Highest',
	'lowestpoint' : 'BBox Lowest',
	'leftsidebearing' : 'L Sidebearing',
	'rightsidebearing' : 'R Sidebearing',
	}


pagemargin = Ddict(dict)
pagemargin['left'] = 12
pagemargin['right'] = 10
pagemargin['top'] = 8
pagemargin['bottom'] = 11
scrapboard = Ddict(dict)
graphcoords = Ddict(dict)

# separator between the scrapboard and the tablesboard
headmargin = 15 # mm
separator = 8 # mm
tableseparator = 3 # mm
roundedcorners = 3 # (pt?)
guidelinedashed = (3, 3) # pt on, pt off

# Colors
colourguides = (1, .5, 0, 0)
colourglobalguides = (0, 1, 1, 0)

# Headline
headerheight = 8 # mm
headlinefontsize = 14
#pdfcolour = (0, .05, 1, 0)
pdfcolour = (.25, 0, 1, 0)
#headlinefontcolour = (.25, .25, 1, .8)
headlinefontcolour = (0, 0, 0, 1)


pdffont = Ddict(dict)
pdffont['Regular'] = 'Courier'
pdffont['Bold'] = 'Courier-Bold'


graphcolour = Ddict(dict)
graphcolour['__default__'] = pdfcolour
graphcolour['width'] = (0, .9, .9, 0)
graphcolour['bboxwidth'] = (0, .75, .9, 0)
graphcolour['bboxheight'] = (0, .5, 1, 0)
graphcolour['highestpoint'] = (0, .3, 1, 0)
graphcolour['lowestpoint'] = (0, .1, 1, 0)
graphcolour['leftsidebearing'] = (0, .75, .25, 0)
graphcolour['rightsidebearing'] = (.25, .75, .25, 0)

# Metrics
glyphcolour = (0, 0, 0, 1)
xrayfillcolour = (0, 0, 0, .4)
metricscolour = (0, 0, 0, .5)
metricslinewidth = .5 # pt
scrapboardcolour = (0, 0, 0, 1)
drawboards = False


# Graphs
#tablenamefont = pdffont['Regular']
graphnamefontsize = 8
#pointsvaluefont = pdffont['Regular']
pointsvaluefontsize = 8


############ Classes


class Report:
	def __init__(self):
		self.gridcolour = metricscolour
		self.strokecolour = pdfcolour
		self.gridwidth = metricslinewidth
		self.strokewidth = 1
		self.values = [] # (value, glyphwidth, glyphheight)
		self.pointslist = []
#		self.scope = 'local' # local or global (relative to this single glyph, or to all glyphs in the pdf)
		self.glyphname = ''
		self.graphname = ''
		
		self.min = 0
		self.max = 0
		self.sum = 0
		#self.ratio = 0

	def addvalue(self, value):
		self.values.append(value)
		
		if len(self.values) == 1:
			self.min = value[0]
			self.max = value[0]
		
		if value[0] > self.max:
			self.max = value[0]
		if value[0] < self.min:
			self.min = value[0]
		self.sum += value[0]

	def draw(self):
		global myDialog
		global globalscopemin, globalscopemax
		global glyphs
		
		drawrect(self.left * mm, self.bottom * mm, self.right * mm, self.top * mm, '', self.gridcolour, self.gridwidth, None, roundedcorners)
		
		r = .05
		mymin = self.min - int(math.fabs(self.min) * r)
		mymax = self.max + int(math.fabs(self.max) * r)
		
		
		if self.scope == 'global':
			
			# Walk through the other graphs and collect their min and max values
			for glyph in glyphs:
				
				try:
					if reports[glyphName][self.graphname].min < mymin:
						mymin = reports[glyphName][self.graphname].min
				except:
					mymin = reports[glyphName][self.graphname].min
				
				try:
					if reports[glyphName][self.graphname].max > mymax:
						mymax = reports[glyphName][self.graphname].max
				except:
					mymax = reports[glyphName][self.graphname].max
				
		if mymax - mymin < 10:
			mymin -= 5
			mymax += 5
		
		pointslist = []
		
		
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			if Glyphs.boolDefaults["com_yanone_Autopsy_drawpointsvalues"]:
				DrawText(pdffont['Regular'], pointsvaluefontsize, glyphcolour, self.left * mm + 1*mm, self.bottom * mm - 3*mm, str(int(mymin)))
				DrawText(pdffont['Regular'], pointsvaluefontsize, glyphcolour, self.right * mm - 5*mm, self.bottom * mm - 3*mm, str(int(mymax)))
			
			try:
				localratio = (self.right - self.left) / (mymax - mymin)
			except:
				localratio = 0

			try:
				y = self.top - (self.values[0][2] / 2 / mm * ratio)
			except:
				y = self.top
			for i, value in enumerate(self.values):
				x = self.left + (value[0] - mymin) * localratio
				pointslist.append((value[0], x, y))
				try:
					y -= self.values[i+1][2] / mm * ratio
				except:
					pass
			
		else:
			if Glyphs.boolDefaults["com_yanone_Autopsy_drawpointsvalues"]:
				DrawText(pdffont['Regular'], pointsvaluefontsize, glyphcolour, self.right * mm + 1*mm, self.bottom * mm + 1*mm, str(int(mymin)))
				DrawText(pdffont['Regular'], pointsvaluefontsize, glyphcolour, self.right * mm + 1*mm, self.top * mm - 3*mm, str(int(mymax)))
#			DrawText(pdffont['Regular'], graphnamefontsize, self.gridcolour, self.left * mm + 1.7*mm, self.top * mm - 4*mm, graphrealnames[self.graphname])
			
			try:
				localratio = (self.top - self.bottom) / (mymax - mymin)
			except:
				localratio = 0
			
			try:
				position = self.left + (self.values[0][1] / 2 / mm * ratio)
			except:
				position = self.left
			for i, value in enumerate(self.values):
				x = position
				y = self.bottom + (value[0] - mymin) * localratio
				pointslist.append((value[0], x, y))
				try:
					position += self.values[i+1][1] / mm * ratio
				except:
					# print traceback.format_exc()
					pass
		
		# Calculate thickness of stroke according to scope of graph
		minthickness = 6
		maxthickness = 12
		thickness = -.008 * (mymax - mymin) + maxthickness
		if thickness < minthickness:
			thickness = minthickness
		elif thickness > maxthickness:
			thickness = maxthickness
		
		DrawTableLines(pointslist, self.strokecolour, thickness)
		DrawText(pdffont['Regular'], graphnamefontsize, self.gridcolour, self.left * mm + 1.7*mm, self.top * mm - 4*mm, graphrealnames[self.graphname])


#################################

def SetScrapBoard(pageratio):
	global myDialog
	global scrapboard
	global graphcoords
	scrapboard['left'] = pagemargin['left']
	scrapboard['right'] = pagewidth/mm - pagemargin['right']
	scrapboard['top'] = pageheight/mm - pagemargin['top'] - headmargin
	scrapboard['bottom'] = pagemargin['bottom']
	graphcoords['left'] = pagemargin['left']
	graphcoords['right'] = pagewidth/mm - pagemargin['right']
	graphcoords['top'] = pageheight/mm - pagemargin['top'] - headmargin
	graphcoords['bottom'] = pagemargin['bottom']

	# Recalculate drawing boards
	if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
		availablewidth = pagewidth/mm - pagemargin['left'] - pagemargin['right']
		partial = availablewidth * pageratio
		scrapboard['right'] = pagemargin['left'] + partial - separator / 2
		graphcoords['left'] = scrapboard['right'] + separator
	else:
		availablewidth = pageheight/mm - pagemargin['top'] - pagemargin['bottom'] - headmargin
		partial = availablewidth * pageratio
		scrapboard['bottom'] = pageheight/mm - headmargin - partial + separator / 2
		graphcoords['top'] = scrapboard['bottom'] - separator 



##################################################################
#
#   PDF section
#


def DrawText(font, fontsize, fontcolour, x, y, text):
	attributes = {NSFontAttributeName : NSFont.fontWithName_size_(font, fontsize), NSForegroundColorAttributeName: NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(fontcolour[0], fontcolour[1], fontcolour[2], fontcolour[3], 1)}
	String = NSAttributedString.alloc().initWithString_attributes_(text, attributes)
	String.drawAtPoint_((x, y))

def DrawTableLines(list, colour, thickness):
	
	global myDialog
	for i, point in enumerate(list):

		try:
			drawline(list[i][1]*mm, list[i][2]*mm, list[i+1][1]*mm, list[i+1][2]*mm, colour, thickness, None)
		except:
			pass

		NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(colour[0], colour[1], colour[2], colour[3], 1).set()
		Rect = NSMakeRect(point[1]*mm-(thickness), point[2]*mm-(thickness), thickness*2, thickness*2)
		NSBezierPath.bezierPathWithOvalInRect_(Rect).fill()
		if Glyphs.boolDefaults["com_yanone_Autopsy_drawpointsvalues"]:
			DrawText(pdffont['Regular'], pointsvaluefontsize, glyphcolour, point[1]*mm + (thickness/6+1)*mm, point[2]*mm - (thickness/6+2.5)*mm, str(int(round(point[0]))))

def DrawHeadlineIntoPage(text):

	drawrect(pagemargin['left']*mm, pageheight - pagemargin['top']*mm - headerheight*mm, pagewidth - pagemargin['right']*mm, pageheight - pagemargin['top']*mm, pdfcolour, None, 0, None, roundedcorners)
	DrawText(pdffont['Bold'], headlinefontsize, headlinefontcolour, 2*mm + pagemargin['left']*mm, 2.2*mm + pageheight - pagemargin['top']*mm - headerheight*mm, text)

def DrawMetrics(f, glyph, xoffset, yoffset, ratio):
	global myDialog
	g = glyph.layers[0]
	
	mywidth = g.width
	if mywidth == 0:
		mywidth = g.bounds.size.width
		
	# Draw metrics
	if Glyphs.defaults["com_yanone_Autopsy_drawmetrics"] == 1:
		# Versalhöhe
		drawline(xoffset*mm, yoffset*mm + capheight(f) * ratio, xoffset*mm + mywidth*ratio, yoffset*mm + capheight(f) * ratio, metricscolour, metricslinewidth, None)
		# x-Höhe
		drawline(xoffset*mm, yoffset*mm + xheight(f) * ratio,   xoffset*mm + mywidth*ratio, yoffset*mm + xheight(f) * ratio, metricscolour, metricslinewidth, None)
		# Grundlinie
		drawline(xoffset*mm, yoffset*mm,                        xoffset*mm + mywidth*ratio, yoffset*mm, metricscolour, metricslinewidth, None)

		# Bounding Box
		drawrect(xoffset*mm, yoffset*mm + descender(f)*ratio,   xoffset*mm + mywidth*ratio, yoffset*mm + ascender(f)*ratio, '', metricscolour, metricslinewidth, None, 0)

	# Draw guidelines
	if Glyphs.boolDefaults["com_yanone_Autopsy_drawguidelines"] == 1 and False: #GSNotImplemented

		# Local vertical guides
		for guide in g.vguides:
			try:
				a = (ascender(f)) * math.tan(math.radians(guide.angle))
			except:
				a = 0
			x1 = guide.position / mm * ratio
			y1 = (0 - descender(f)) / mm * ratio
			x2 = (guide.position + a) / mm * ratio
			y2 = (ascender(f) - descender(f)) / mm * ratio
			drawline(xoffset*mm + x1*mm, yoffset*mm + y1*mm, xoffset*mm + x2*mm, yoffset*mm + y2*mm, colourguides, metricslinewidth, guidelinedashed)

		# Global vertical guides
		for guide in f.vguides:
			try:
				a = (ascender(f)) * math.tan(math.radians(guide.angle))
			except:
				a = 0
			x1 = guide.position / mm * ratio
			y1 = (0 - descender(f)) / mm * ratio
			x2 = (guide.position + a) / mm * ratio
			y2 = (ascender(f) - descender(f)) / mm * ratio
			drawline(xoffset*mm + x1*mm, yoffset*mm + y1*mm, xoffset*mm + x2*mm, yoffset*mm + y2*mm, colourglobalguides, metricslinewidth, guidelinedashed)

		# Local horizontal guides
		for guide in g.hguides:
			try:
				a = g.width * math.tan(math.radians(guide.angle))
			except:
				a = 0
			x1 = 0
			y1 = (guide.position - descender(f)) / mm * ratio
			x2 = g.width / mm * ratio
			y2 = (guide.position - descender(f) + a) / mm * ratio
			drawline(xoffset*mm + x1*mm, yoffset*mm + y1*mm, xoffset*mm + x2*mm, yoffset*mm + y2*mm, colourguides, metricslinewidth, guidelinedashed)

		# Global horizontal guides
		for guide in f.hguides:
			try:
				a = g.width * math.tan(math.radians(guide.angle))
			except:
				a = 0
			x1 = 0
			y1 = (guide.position - descender(f)) / mm * ratio
			x2 = g.width / mm * ratio
			y2 = (guide.position - descender(f) + a) / mm * ratio
			drawline(xoffset*mm + x1*mm, yoffset*mm + y1*mm, xoffset*mm + x2*mm, yoffset*mm + y2*mm, colourglobalguides, metricslinewidth, guidelinedashed)

	# Draw font names under box
	if Glyphs.boolDefaults["com_yanone_Autopsy_fontnamesunderglyph"]:
		DrawText(pdffont['Regular'], pointsvaluefontsize, glyphcolour, xoffset*mm + 2, yoffset*mm - 8, f.familyName)


def PSCommandsFromGlyph(glyph):

	CommandsList = []

	for path in glyph.paths:
		lastNode = None
		if path.closed:
			lastNode = path.nodes[-1]
		else:
			lastNode = path.nodes[0]
		CommandsList.append(('moveTo', (lastNode.x, lastNode.y)))
		for i, node in enumerate(path.nodes):
			
			if node.type == GSOFFCURVE:
				CommandsList.append(('close', (node.x, node.y)))
			
			#if node.type == nMOVE:
			#	CommandsList.append(('moveTo', (node.x, node.y)))

			if node.type == GSLINE:
				CommandsList.append(('lineTo', (node.x, node.y)))

			if node.type == GSCURVE:
				CurveCommandsList = []
				CurveCommandsList.append('curveTo')
				
				#for point in node.points:
				CurveCommandsList.append( (node.x, node.y) )
				point = path.nodes[i-2]
				CurveCommandsList.append( (point.x, point.y) )
				point = path.nodes[i-1]
				CurveCommandsList.append( (point.x, point.y) )
				
				CommandsList.append(CurveCommandsList)

	return CommandsList

def DrawGlyph(f, glyph, PSCommands, xoffset, yoffset, ratio, fillcolour, strokecolour, strokewidth, dashed):
	if not PSCommands:
		
		type = "glyph"
		
		# Copy glyph into memory (so remove overlap won't affect the current font)
		g = glyph.layers[0]
		if len(g.components) > 0:
			for component in g.components:
				position = component.position
				DrawGlyph(f, component.component, None, xoffset+(position.x*ratio/mm), yoffset+(position.y*ratio/mm), ratio, fillcolour, strokecolour, strokewidth, dashed)
	
		# Glyph has nodes of its own
		if len(g.paths):
			PSCommands = PSCommandsFromGlyph(g)
			#print PSCommands
		else:
			PSCommands = ()
		
	else:
		type = "PScommands"


	if PSCommands:
		p = NSBezierPath.bezierPath()
		
		for command in PSCommands:
		
			if command[0] == 'moveTo':
				try:
					p.close()
				except:
					pass
	
				x = xoffset*mm + command[1][0] * ratio
				y = yoffset*mm + command[1][1] * ratio
				p.moveToPoint_((x, y))
				#print "('moveTo', (%s, %s))," % (command[1][0], command[1][1])
	
			if command[0] == 'lineTo':
				x = xoffset*mm + command[1][0] * ratio
				y = yoffset*mm + command[1][1] * ratio
				p.lineToPoint_((x, y))
				#print "('lineTo', (%s, %s))," % (command[1][0], command[1][1])
	
			if command[0] == 'curveTo':
	
				points = []
				
				for point in command[1:]:
					points.append( (xoffset*mm + point[0] * ratio, yoffset*mm + point[1] * ratio) )
				
				p.curveToPoint_controlPoint1_controlPoint2_(points[0], points[1], points[2])
	
		p.closePath()
		if fillcolour:
			NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(fillcolour[0], fillcolour[1], fillcolour[2], fillcolour[3], 1).set()
			p.fill()
		if strokecolour:
			NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(strokecolour[0], strokecolour[1], strokecolour[2], strokecolour[3], 1).set()
			if dashed:
				p.setLineDash_count_phase_(dashed, 2, 0.0)
			p.setLineWidth_(strokewidth)
			p.stroke()




######### draw primitives

def drawline(x1, y1, x2, y2, colour, strokewidth, dashed):

	NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(colour[0], colour[1], colour[2], colour[3], 1).set()
	Path = NSBezierPath.bezierPath()
	Path.moveToPoint_((x1, y1))
	Path.lineToPoint_((x2, y2))
	Path.setLineWidth_(strokewidth)
	
	if dashed:
		Path.setLineDash_count_phase_(dashed, 2, 0.0)
	Path.stroke()

def drawrect(x1, y1, x2, y2, fillcolour, strokecolour, strokewidth, dashed, rounded):
	Rect = NSMakeRect(x1, y1, x2 - x1, y2 - y1)
	Path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(Rect, rounded, rounded)
	if fillcolour:
		NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(fillcolour[0], fillcolour[1], fillcolour[2], fillcolour[3], 1).set()
		Path.fill()
	if strokecolour:
		Path.setLineWidth_(strokewidth)
		if dashed:
			Path.setLineDash_count_phase_(dashed, 2, 0.0)
		NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(strokecolour[0], strokecolour[1], strokecolour[2], strokecolour[3], 1).set()
		Path.stroke()

# collects the glyphs that should be displayed
# and returns list of glyph names
def collectglyphnames():
	
	glyphlist = []
	Font = Glyphs.orderedDocuments()[0].font
	if Font.selectedLayers is not None:
		for Layer in Font.selectedLayers:
			glyphlist.append(Layer.parent.name)
	
	return glyphlist

def capheight(f):
	return f.masters[0].capHeight

def xheight(f):
	return f.masters[0].xHeight

def descender(f):
	return f.masters[0].descender

def ascender(f):
	return f.masters[0].ascender

def unicode2hex(u):
	return string.zfill(string.upper(hex(u)[2:]), 4)

errortexts = []
errors = 0

def raiseerror(text):
	global errors, errorslist
	errortexts.append(text)
	try:
		errors += 1
	except:
		errors = 1


def CheckForUpdates():
	return
	if Defaults['com_yanone_Autopsy_checkforupdates']:
		import webbrowser, urllib
		try:
			if int(releasedate) < int(urllib.urlopen('http://www.yanone.de/typedesign/autopsy/latestreleasedate.txt').read()):
				x = fl.Message('Hey, I was reincarnated as a newer version.\nDo you want to connect to my download page on the internet?')
				if x == 1:
					webbrowser.open('http://www.yanone.de/typedesign/autopsy/download.php', 1, 1)
		except:
			pass # No network connection

##### MAIN

def drawTitlePage(fonts):
	try:
		xoffset = pagewidth/mm * 1/1.61
		yoffset = pageheight/mm * 1.61
		
		#NSRectFill(((-100, -100), (200, 200)))
	
		# Draw front page
		output('-- font page --')
	
		drawrect(3*mm, 3*mm, pagewidth - 3*mm, pageheight - 3*mm, pdfcolour, None, None, None, 0)
		
		# Try to get a random glyph from a random font with nodes
		# try not more than 10000 times
		glyphfound = False

		randomfont = fonts[random.randint(0, len(fonts) - 1)]
		randomglyphindex = random.randint(0, len(randomfont) - 1)
		g = randomfont.glyphs[randomglyphindex]
		
		if g is not None:
			glyphfound = True
		tries = 0
		while glyphfound == False and tries < 10000:
			randomfont = fonts[random.randint(0, len(fonts) - 1)]
			randomglyphindex = random.randint(0, len(randomfont) - 1)
			g = randomfont[randomglyphindex]
			if (g.nodes_number or g.components):
				glyphfound = True
			tries += 1
		# if (g.nodes or g.components):
		# 	glyphfound = True
	
		# if random didn't help, get first glyph with nodes
		if not glyphfound:
			for gi in range(len(fonts[0])):
				if fonts[0][gi].nodes_number or fonts[0][gi].components:
					g = fonts[0][gi]
		
	
		bbox = g.layers[0].bounds
		if bbox.size.height > 1:
			localratio = .65 / bbox.size.height * (pageheight - yoffset)
		else:
			print "____NO height____"
			localratio = .65 / 300
		
		# draw logo and name
		logoyoffset = -5

		## YN
		ynlogo = [('moveTo', (350, 700)), ['curveTo', (0, 350), (138, 700), (0, 562)], ['curveTo', (350, 0), (0, 138), (138, 0)], ['curveTo', (700, 350), (562, 0), (700, 138)], ['curveTo', (350, 700), (700, 562), (562, 700)], ('moveTo', (548, 297)), ('lineTo', (542, 297)), ['curveTo', (536, 286), (536, 297), (536, 288)], ('lineTo', (536, 174)), ['curveTo', (510, 132), (536, 153), (531, 132)], ['curveTo', (481, 155), (496, 132), (489, 140)], ['curveTo', (416, 272), (481, 155), (435, 237)], ('lineTo', (416, 180)), ['curveTo', (422, 168), (416, 168), (420, 168)], ['curveTo', (434, 169), (425, 168), (430, 169)], ['curveTo', (451, 152), (444, 169), (451, 163)], ['curveTo', (430, 136), (451, 144), (445, 136)], ['curveTo', (399, 139), (421, 136), (413, 139)], ['curveTo', (365, 136), (386, 139), (374, 136)], ['curveTo', (345, 153), (350, 136), (345, 144)], ['curveTo', (362, 169), (345, 163), (352, 169)], ['curveTo', (374, 168), (366, 169), (371, 168)], ['curveTo', (380, 179), (376, 168), (380, 168)], ('lineTo', (380, 286)), ['curveTo', (374, 298), (380, 297), (376, 298)], ['curveTo', (362, 297), (371, 298), (368, 297)], ['curveTo', (347, 306), (355, 297), (350, 302)], ['curveTo', (332, 297), (345, 302), (340, 297)], ['curveTo', (320, 298), (326, 297), (326, 298)], ['curveTo', (316, 295), (319, 298), (318, 298)], ('lineTo', (261, 209)), ('lineTo', (261, 175)), ['curveTo', (267, 168), (261, 170), (263, 168)], ['curveTo', (281, 170), (270, 168), (274, 170)], ['curveTo', (296, 153), (291, 170), (296, 163)], ['curveTo', (275, 136), (296, 144), (291, 136)], ['curveTo', (241, 139), (262, 136), (254, 139)], ['curveTo', (208, 136), (228, 139), (221, 136)], ['curveTo', (188, 152), (194, 136), (188, 144)], ['curveTo', (205, 170), (188, 163), (195, 170)], ['curveTo', (217, 168), (211, 170), (212, 168)], ['curveTo', (223, 175), (219, 168), (223, 170)], ('lineTo', (223, 207)), ('lineTo', (168, 296)), ['curveTo', (164, 297), (167, 297), (165, 297)], ['curveTo', (153, 296), (160, 297), (158, 296)], ['curveTo', (134, 313), (139, 296), (134, 304)], ['curveTo', (152, 331), (134, 324), (141, 331)], ['curveTo', (186, 327), (165, 331), (175, 327)], ['curveTo', (215, 331), (197, 327), (203, 331)], ['curveTo', (234, 313), (229, 331), (234, 322)], ['curveTo', (213, 297), (234, 306), (230, 297)], ('lineTo', (212, 297)), ('lineTo', (243, 245)), ['curveTo', (273, 297), (251, 260), (267, 285)], ['curveTo', (268, 296), (270, 296), (268, 296)], ['curveTo', (249, 313), (254, 296), (249, 304)], ['curveTo', (268, 331), (249, 324), (256, 331)], ['curveTo', (298, 328), (275, 331), (287, 328)], ['curveTo', (332, 331), (308, 328), (322, 331)], ['curveTo', (348, 321), (339, 331), (345, 326)], ['curveTo', (365, 331), (350, 326), (356, 331)], ['curveTo', (389, 329), (369, 331), (378, 329)], ['curveTo', (413, 331), (399, 329), (406, 331)], ['curveTo', (431, 320), (428, 331), (430, 324)], ('lineTo', (433, 314)), ('lineTo', (500, 193)), ('lineTo', (500, 286)), ['curveTo', (490, 297), (500, 289), (500, 297)], ('lineTo', (482, 297)), ['curveTo', (465, 313), (472, 297), (465, 305)], ['curveTo', (486, 331), (465, 321), (471, 331)], ['curveTo', (516, 328), (496, 331), (504, 328)], ['curveTo', (547, 331), (526, 328), (536, 331)], ['curveTo', (566, 313), (561, 331), (566, 322)], ['curveTo', (548, 297), (566, 305), (561, 297)], ('moveTo', (359, 568)), ['curveTo', (422, 525), (385, 568), (408, 552)], ['curveTo', (486, 568), (436, 552), (459, 568)], ['curveTo', (544, 508), (518, 568), (544, 546)], ['curveTo', (422, 356), (544, 441), (472, 420)], ['curveTo', (301, 508), (372, 420), (301, 441)], ['curveTo', (359, 568), (301, 546), (326, 568)], ('moveTo', (206, 530)), ['curveTo', (193, 529), (202, 530), (197, 529)], ['curveTo', (176, 546), (183, 529), (176, 538)], ['curveTo', (197, 563), (176, 555), (182, 563)], ['curveTo', (231, 560), (209, 563), (216, 560)], ['curveTo', (264, 563), (244, 560), (252, 563)], ['curveTo', (284, 546), (278, 563), (284, 555)], ['curveTo', (268, 529), (284, 536), (275, 529)], ['curveTo', (255, 530), (263, 529), (260, 530)], ['curveTo', (249, 519), (253, 530), (249, 530)], ('lineTo', (249, 413)), ['curveTo', (255, 401), (249, 401), (253, 401)], ['curveTo', (268, 402), (259, 401), (263, 402)], ['curveTo', (284, 386), (277, 402), (284, 396)], ['curveTo', (264, 368), (284, 377), (278, 368)], ['curveTo', (232, 372), (248, 368), (244, 372)], ['curveTo', (196, 368), (217, 372), (215, 368)], ['curveTo', (176, 386), (182, 368), (176, 377)], ['curveTo', (193, 402), (176, 396), (183, 402)], ['curveTo', (206, 401), (198, 402), (201, 401)], ['curveTo', (211, 413), (207, 401), (211, 401)], ('lineTo', (211, 519)), ['curveTo', (206, 530), (211, 530), (207, 530)]]
		ynlogoring = [('moveTo', (350, 700)), ['curveTo', (0, 350), (138, 700), (0, 562)], ['curveTo', (350, 0), (0, 138), (138, 0)], ['curveTo', (700, 350), (562, 0), (700, 138)], ['curveTo', (350, 700), (700, 562), (562, 700)]]
		textyoffset = 0
		textxoffset = 0
	
		DrawGlyph(None, None, ynlogo, xoffset/mm - .5, 14.5 + logoyoffset, .05, headlinefontcolour, None, None, 1)
	
		DrawGlyph(None, None, ynlogoring, xoffset/mm - .5, 14.5 + logoyoffset, .05, None, (0,0,0,0), 3, (6,4))
		DrawText(pdffont['Regular'], 9, headlinefontcolour, textxoffset + xoffset + 15*mm, 22*mm + textyoffset + logoyoffset*mm, programname + ' ' + programversion + ' by Yanone')
		DrawText(pdffont['Regular'], 9, headlinefontcolour, textxoffset + xoffset + 15*mm, 18.4*mm + textyoffset + logoyoffset*mm, 'www.yanone.de/typedesign/autopsy/')
	
		# Sample glyph
		DrawGlyph(fonts[0], g, None, xoffset/mm - bbox.origin.x/mm*localratio, yoffset/mm - bbox.origin.y/mm*localratio + 18, localratio, (0,0,0,0), headlinefontcolour, 3, (6, 4))

		# Autopsy Report
		DrawText(pdffont['Bold'], 48, headlinefontcolour, xoffset, yoffset, "Autopsy Report")

		# Other infos
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			textmaxratio = 10000
		else:
			textmaxratio = 16000
		lines = []
		if len(fonts) > 1:
			patient = "Patients"
		else:
			patient = "Patient"
		lines.append((pdffont['Regular'], 18, headlinefontcolour, xoffset, 30, patient + ':'))
		yoffset -= 5
		for myfont in fonts:
			if myfont.instances[0] is None:
				lines.append((pdffont['Bold'], 18, headlinefontcolour, xoffset, 20, u"%s —" % (myfont.familyName))) # + ' v' + str(myfont.version)))
			else:
				lines.append((pdffont['Bold'], 18, headlinefontcolour, xoffset, 20, "%s %s" % (myfont.familyName, myfont.instances[0].name))) # + ' v' + str(myfont.version)))
		# get designers(s)
		designers = Ddict(dict)
		for f in fonts:
			if f.manufacturer:
				designers[f.manufacturer] = 1
			elif f.designer:
				designers[f.designer] = 1
			else:
				designers['Anonymous'] = 1
		if len(designers) > 1:
			doctor = 'Doctors'
		else:
			doctor = 'Doctor'
		fontinfos = {
			doctor : ", ".join(designers),
			'Time' : time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()),
		}
		for fontinfo in fontinfos:
			lines.append((pdffont['Regular'], 18, headlinefontcolour, xoffset, 30, fontinfo + ':'))
			lines.append((pdffont['Bold'], 18, headlinefontcolour, xoffset, 20, fontinfos[fontinfo]))
		linesratio = 1.0/len(lines) * textmaxratio / pageheight/mm * 1.61
		if linesratio > 1:
			linesratio = 1
		for line in lines:
			yoffset -= line[4] * linesratio
			DrawText(line[0], line[1] * linesratio, line[2], line[3], yoffset, line[5])
	except:
		print "Problem with titlepage",
		print traceback.format_exc()
		

def drawGlyph(fonts, glyphName, i, ratio, reports):
	output('-- ' + glyphName + ' --')
	global graphcoords
	global scrapboard
	# if not tick:
	# 	raiseerror('Aborted by user.')
	# 	break
	#glyphindex = fonts[0].glyphs[glyphName)

	# Draw scrapboard into page
	if drawboards:
		#drawrect(scrapboard['left']*mm, scrapboard['bottom']*mm, scrapboard['right']*mm, scrapboard['top']*mm, '', scrapboardcolour, metricslinewidth, None, 0)
		#drawrect(graphcoords['left']*mm, graphcoords['bottom']*mm, graphcoords['right']*mm, graphcoords['top']*mm, '', scrapboardcolour, metricslinewidth, None, 0)
		pass
	try:
		unicodes = 'u' + string.join(map(unicode2hex, fonts[0].glyphs[glyphName].unicodes), "u u") + 'u'
	except:
		unicodes = ''
	# print '-', fonts[0][glyphindex], '-'
	DrawHeadlineIntoPage("/%s/ #%d# %s" % (glyphName, i, unicodes))

	# Initial offset

	if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
		xoffsetinitial = scrapboard['left']
		yoffsetinitial = scrapboard['top'] - (ascender(fonts[0]) - descender(fonts[0])) / mm * ratio
	else:
		xoffsetinitial = scrapboard['left']
		yoffsetinitial = scrapboard['bottom']

	# Draw Metrics

	xoffset = xoffsetinitial
	yoffset = yoffsetinitial - descender(fonts[0])*ratio/mm


	for i_f, font in enumerate(fonts):

		if font.glyphs.has_key(glyphName):
			g = font.glyphs[glyphName]
		elif not font.glyphs.has_key(glyphName) and fonts[i_f-1].glyphs.has_key(glyphName):
			g = fonts[i_f-1].glyphs[glyphName]
		
		DrawMetrics(font, g, xoffset, yoffset, ratio)

		# increase offset
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			yoffset -= (ascender(font) - descender(font)) / mm * ratio
		else:
			if g.layers[0].width == 0:
				xoffset += g.layers[0].bounds.size.width / mm * ratio
			else:
				xoffset += g.layers[0].width / mm * ratio
	
	# Draw Glyphs
	
	xoffset = xoffsetinitial
	yoffset = yoffsetinitial - descender(fonts[0])*ratio/mm
	# Defaults
	myglyphfillcolour = glyphcolour
	myglyphstrokecolour = None
	myglyphstrokewidth = 0
	myglyphdashed = None
	
	for i_f, font in enumerate(fonts):
		
		# Glyph is in font
		if font.glyphs.has_key(glyphName):
			g = font.glyphs[glyphName]
			
			if Glyphs.intDefaults["Autopsy.OutlineStyle"] == 0:
				myglyphfillcolour = glyphcolour
				myglyphstrokecolour = None
				myglyphstrokewidth = 0
				myglyphdashed = None
			else:
				myglyphfillcolour = xrayfillcolour
				myglyphstrokecolour = glyphcolour
				myglyphstrokewidth = 1.5
				myglyphdashed = None
		
		# Glyph is missing in font, draw replacement glyph
		elif not font.glyphs.has_key(glyphName) and fonts[i_f-1].glyphs.has_key(glyphName):
			g = fonts[i_f-1].glyphs[glyphName]
			myglyphfillcolour = None
			myglyphstrokecolour = glyphcolour
			myglyphstrokewidth = 1
			myglyphdashed = (3, 3)
		
		DrawGlyph(font, g, None, xoffset, yoffset, ratio, myglyphfillcolour, myglyphstrokecolour, myglyphstrokewidth, myglyphdashed)
		
		# increase offset
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			yoffset -= (ascender(font) - descender(font)) / mm * ratio
		else:
			if g.layers[0].width == 0:
				xoffset += g.layers[0].bounds.size.width / mm * ratio
			else:
				xoffset += g.layers[0].width / mm * ratio
	
		#tick = fl.TickProgress((i) * len(fonts) + i_f + 1)
	
	# Aggregate graph objects into a list
	
	tableobjects = []
	for table in availablegraphs:
		if Glyphs.boolDefaults["com_yanone_Autopsy_graph_"+table]:
			reports[glyphName][table].glyphname = glyphName
			reports[glyphName][table].graphname = table
			reports[glyphName][table].drawpointsvalues = Glyphs.boolDefaults["com_yanone_Autopsy_drawpointsvalues"]
			
			reports[glyphName][table].scope = Glyphs.defaults["com_yanone_Autopsy_graph_"+table + '_scope']
			
			if graphcolour.has_key(table):
				reports[glyphName][table].strokecolour = graphcolour[table]
			else:
				reports[glyphName][table].strokecolour = graphcolour['__default__']
			tableobjects.append(reports[glyphName][table])

	# Calculate bbox for graphs an draw them

	for t, table in enumerate(tableobjects):
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			tablewidth = ((graphcoords['right'] - graphcoords['left']) - (tableseparator * (len(tableobjects) - 1))) / len(tableobjects)
			tableheight = reports[glyphName]['height'].sum/mm*ratio
			table.left = graphcoords['left'] + t * (tablewidth + tableseparator)
			table.right = table.left + tablewidth
			table.top = graphcoords['top']
			table.bottom = table.top - tableheight
		else:
			if reports[glyphName]['width']:
				tablewidth = reports[glyphName]['width'].sum/mm*ratio
			else:
				tablewidth = reports[glyphName]['bboxwidth'].sum/mm*ratio
			tableheight = ((graphcoords['top'] - graphcoords['bottom']) - (tableseparator * (len(tableobjects) - 1))) / len(tableobjects)
			table.left = graphcoords['left']
			table.right = table.left + tablewidth
			table.top = graphcoords['top'] - t * (tableheight + tableseparator)
			table.bottom = table.top - tableheight
		table.draw()

	# PDF Bookmarks
	# pdf.bookmarkPage(glyphName)
	# pdf.addOutlineEntry(None, glyphName, 0, 0)
	

def runAutopsy(fonts, glyphNames):
	if fonts and glyphNames:
		
		starttime = time.time()
		
		global pagewidth, pageheight
		#global myDialog
		
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			if not Glyphs.boolDefaults["com_yanone_Autopsy_PageSize_a4"]:
				pagewidth = letter[0]
				pageheight = letter[1]
			else:
				pagewidth = A4[0]
				pageheight = A4[1]
		else:
			if not Glyphs.boolDefaults["com_yanone_Autopsy_PageSize_a4"]:
				pagewidth = letter[1]
				pageheight = letter[0]
			else:
				pagewidth = A4[1]
				pageheight = A4[0]
		
		#############
		#
		# Collect information about the glyphs
		#
	
		# Dimensions
		reports = Ddict(dict)
	
		glyphwidth = Ddict(dict)
		maxwidthperglyph = Ddict(dict)
		maxwidth = 0
		maxsinglewidth = 0
		glyphheight = Ddict(dict)
		maxheightperglyph = Ddict(dict)
		maxheight = 0
		maxsingleheight = 0
		
		for glyphName in glyphNames:
	
			glyphwidth[glyphName] = 0
			glyphheight[glyphName] = 0
			maxwidthperglyph[glyphName] = 0
			maxheightperglyph[glyphName] = 0
			reports[glyphName]['width'] = Report()
			reports[glyphName]['height'] = Report()
			reports[glyphName]['bboxwidth'] = Report()
			reports[glyphName]['bboxheight'] = Report()
			reports[glyphName]['highestpoint'] = Report()
			reports[glyphName]['lowestpoint'] = Report()
			reports[glyphName]['leftsidebearing'] = Report()
			reports[glyphName]['rightsidebearing'] = Report()
			for font in fonts:
				FontMaster = font.masters[0]
				if font.glyphs.has_key(glyphName):
					g = font.glyphs[glyphName].layers[FontMaster.id]
					#print "__g", g
					glyphwidth[glyphName] = g.width
					height = ascender(font) - descender(font)

					widthforgraph = glyphwidth[glyphName]
					if widthforgraph == 0:
						widthforgraph = g.bounds.size.width
					heightforgraph = height
	
					# width of kegel
					reports[glyphName]['width'].addvalue((glyphwidth[glyphName], widthforgraph, heightforgraph))
					# sum of widths per glyph
					if reports[glyphName]['width'].sum > maxwidth:
						maxwidth = reports[glyphName]['width'].sum
					if reports[glyphName]['width'].max > maxsinglewidth:
						maxsinglewidth = reports[glyphName]['width'].max
						
					# height of kegel
					glyphheight[glyphName] = height
					reports[glyphName]['height'].addvalue((glyphheight[glyphName], widthforgraph, heightforgraph))
					# sum of heights per glyph
					if reports[glyphName]['height'].sum > maxheight:
						maxheight = reports[glyphName]['height'].sum
					if reports[glyphName]['height'].max > maxsingleheight:
						maxsingleheight = reports[glyphName]['height'].max
					
					# BBox
					overthetop = 20000
					
					bbox = g.bounds
					
					if bbox.size.width < -1*overthetop or bbox.size.width > overthetop:
						reports[glyphName]['bboxwidth'].addvalue((0, widthforgraph, heightforgraph))
					else:
						reports[glyphName]['bboxwidth'].addvalue((bbox.size.width, widthforgraph, heightforgraph))
					
					if bbox.size.height < -1*overthetop or bbox.size.height > overthetop:
						reports[glyphName]['bboxheight'].addvalue((0, widthforgraph, heightforgraph))
					else:
						reports[glyphName]['bboxheight'].addvalue((bbox.size.height, widthforgraph, heightforgraph))
					
					
					if (bbox.origin.y + bbox.size.height) < -1*overthetop or (bbox.origin.y + bbox.size.height) > overthetop:
						reports[glyphName]['highestpoint'].addvalue((0, widthforgraph, heightforgraph))
					else:
						reports[glyphName]['highestpoint'].addvalue((bbox.origin.y + bbox.size.height, widthforgraph, heightforgraph))
					
					if bbox.origin.y < -1*overthetop or bbox.origin.y > overthetop:
						reports[glyphName]['lowestpoint'].addvalue((0, widthforgraph, heightforgraph))
					else:
						reports[glyphName]['lowestpoint'].addvalue((bbox.origin.y, widthforgraph, heightforgraph))
					
					# L + R sidebearing
					reports[glyphName]['leftsidebearing'].addvalue((g.LSB, widthforgraph, heightforgraph))
					reports[glyphName]['rightsidebearing'].addvalue((g.RSB, widthforgraph, heightforgraph))

		

		# Recalculate drawing boards
		numberoftables = 0
		# GSNotImplemented
		# for table in availablegraphs:
		# 	if eval('myDialog.graph_' + table):
		# 		numberoftables += 1

		if numberoftables < 3:
			numberoftables = 3
		try:
			r = 2.0 / numberoftables
		except:
			r = .8
		SetScrapBoard(r)

			
		# Calculate ratio
		global ratio
		if Glyphs.intDefaults["com_yanone_Autopsy_PageOrientation"] == Portrait:
			ratio = (scrapboard['top'] - scrapboard['bottom']) / maxheight * mm
			ratio2 = (scrapboard['right'] - scrapboard['left']) / maxsinglewidth * mm
			maxratio = 0.3
			if ratio > maxratio:
				ratio = maxratio
			if ratio > ratio2:
				ratio = ratio2
		else:
			ratio = (scrapboard['right'] - scrapboard['left']) / maxwidth * mm
			ratio2 = (scrapboard['top'] - scrapboard['bottom']) / maxsingleheight * mm
			maxratio = 0.3
			if ratio > maxratio:
				ratio = maxratio
			if ratio > ratio2:
				ratio = ratio2
		
		
		# PDF Init stuff
		filename = Glyphs.defaults["com_yanone_Autopsy_filename"]
		tempFileName = NSTemporaryDirectory()+"%d.pdf"%random.randint(1000,100000)
		
		pageRect = CGRectMake (0, 0, pagewidth, pageheight)
		
		fileURL = NSURL.fileURLWithPath_(tempFileName)
		pdfContext = CGPDFContextCreateWithURL(fileURL, pageRect, None)
		CGPDFContextBeginPage(pdfContext, None)
		
		pdfNSGraphicsContext = NSGraphicsContext.graphicsContextWithGraphicsPort_flipped_(pdfContext, False)
		NSGraphicsContext.saveGraphicsState()
		NSGraphicsContext.setCurrentContext_(pdfNSGraphicsContext)
		
		try:
		
			drawTitlePage(fonts)
			CGPDFContextEndPage(pdfContext)
			### MAIN PAGES ###
		
			
			for i, glyphName in enumerate(glyphNames):
				CGPDFContextBeginPage(pdfContext, None)
				drawGlyph(fonts, glyphName, i, ratio, reports)
				# End page
				CGPDFContextEndPage(pdfContext)
			
		except:
			print "__Main"
			print traceback.format_exc()
			
		finally:
			# close PDF
			NSGraphicsContext.restoreGraphicsState()
			CGPDFContextClose(pdfContext)
		
		output("time: " + str(time.time() - starttime) + "sec, ca." + str((time.time() - starttime) / len(glyphNames)) + "sec per glyph")
		
		
		if errors:
			print "__Errors", errors
			for error in errortexts:
				#print "__Message", error, programname
				dlg = message(error)
			
		# if not errors and fonts and myDialog.openPDF:
		if not errors and fonts:
			try:
				os.rename(tempFileName, filename)
			except:
				dlg = Message("Error", "Problem copying final pdf")
			if Glyphs.defaults["com_yanone_Autopsy_openPDF"]:
				launchfile(filename)

def launchfile(path):
	if os.path.exists(path):
		if os.name == 'posix':
			os.system('open "%s"' % path)
		elif os.name == 'nt':
			os.startfile('"' + path + '"')

# Output to console
def output(text):
	if verbose:
		print "> " + str(text) + " <"



'''

TODO

- error message if full_name is empty.

- custom presets for GUI

for better handling of missing glyphs and zero-width glyphs:
- add a class for single graph values, that contain info about width and height of drawing space,
  and whether or not a point should be drawn there.

'''
