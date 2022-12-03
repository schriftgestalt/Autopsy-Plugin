# encoding: utf-8

import objc
import sys, os, re

from GlyphsApp import *
from GlyphsApp.plugins import *
GlyphsPluginProtocol = objc.protocolNamed("GlyphsPlugin")

class GlyphsPluginAutopsy(GeneralPlugin):

	_window = objc.IBOutlet()
	_fontListController = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		try:
			self.loadNib('AutopsyDialog', __file__)
			defaultpdf = os.path.join(os.path.expanduser('~'), 'Desktop', 'Autopsy.pdf')
			defaultpreferences = {
				# 'com_yanone_Autopsy_PageOrientation_landscape' : 0,
				# 'com_yanone_Autopsy_PageSize_a4' : 0,
				# 'com_yanone_Autopsy_outline_filled' : True,
				# Other
				'com_yanone_Autopsy_drawpointsvalues': True,
				'com_yanone_Autopsy_drawmetrics': True,
				'com_yanone_Autopsy_drawguidelines': True,
				'com_yanone_Autopsy_fontnamesunderglyph': False,
				'com_yanone_Autopsy_filename': defaultpdf,
				'com_yanone_Autopsy_openPDF': True,
				'com_yanone_Autopsy_checkforupdates': True,
				# Graphs
				'com_yanone_Autopsy_graph_width': True,
				'com_yanone_Autopsy_graph_width_scope_local': True,
				'com_yanone_Autopsy_graph_bboxwidth': False,
				'com_yanone_Autopsy_graph_bboxwidth_scope_local': True,
				'com_yanone_Autopsy_graph_bboxheight': False,
				'com_yanone_Autopsy_graph_bboxheight_scope_local': True,
				'com_yanone_Autopsy_graph_highestpoint': False,
				'com_yanone_Autopsy_graph_highestpoint_scope_local': False,
				'com_yanone_Autopsy_graph_lowestpoint': False,
				'com_yanone_Autopsy_graph_lowestpoint_scope_local': False,
				'com_yanone_Autopsy_graph_leftsidebearing': True,
				'com_yanone_Autopsy_graph_leftsidebearing_scope_local': True,
				'com_yanone_Autopsy_graph_rightsidebearing': True,
				'com_yanone_Autopsy_graph_rightsidebearing_scope_local': True,
				}
			NSUserDefaults.standardUserDefaults().registerDefaults_(defaultpreferences)

		except Exception as e:
			self.logToConsole("init: %s" % str(e))

		#return self

		mainMenu = NSApplication.sharedApplication().mainMenu()
		s = objc.selector(self.showWindow, signature=b'v@:')
		newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.title(), s, "y")
		newMenuItem.setKeyEquivalentModifierMask_(NSAlternateKeyMask | NSCommandKeyMask)
		newMenuItem.setTarget_(self)

		mainMenu.itemAtIndex_(2).submenu().addItem_(newMenuItem)

	def title(self):
		return "Autopsy"

	def interfaceVersion(self):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		return 1

	def showWindow(self):
		self.glyphlist = []
		Font = Glyphs.orderedDocuments()[0].font
		if Font.selectedLayers is not None:
			for Layer in Font.selectedLayers:
				self.glyphlist.append(Layer.parent.name)
		self.mode = 'normal' # TODO implement proper handling of MM
		self._fontListController.setContent_(NSDocumentController.sharedDocumentController().valueForKeyPath_("documents.font"))
		self._window.makeKeyAndOrderFront_(self)

	@objc.IBAction
	def runAutopsy_(self, sender):
		print("autopsy:")
		self._window.orderOut_(self)
		#self.returnValue = NSOKButton
		if self.mode == 'normal':
			#self.d.GetValue('List_sel')
			fonts = self._fontListController.selectedObjects()

		elif self.mode == 'MM':
			#self.d.GetValue('MMvalues')
			myMMvalues = string.replace(self.MMvalues, ' ', '')
			self.selection = myMMvalues.split(",")

			# Save instances into customdata of VFB
			if self.MMvalues != self.customdata['MMinstances']:
				self.MMfont.modified = 1
			self.customdata['MMinstances'] = self.MMvalues
			if self.MMfont.glyphs.has_key('.notdef'):
				self.MMfont['.notdef'].customdata = writePlistToString(self.customdata)

		#NSUserDefaults.standardUserDefaults()['com_yanone_Autopsy_fontselection'] = self.d.List_sel.get()
		import traceback
		try:
			from AutopsyLib import runAutopsy

			runAutopsy(fonts, self.glyphlist)

		except:
			print(traceback.format_exc())

	@objc.IBAction
	def closeDialog_(self, sender):
		self._window.orderOut_(self)

