# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2015 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import wx._core


class Workbench(wx.Panel):

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		vbox = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		self.hbox = wx.BoxSizer(wx.HORIZONTAL)

		self.toolbar = wx.ToolBar(self)
		self.combo = wx.ComboBox(self, -1, style=wx.CB_READONLY)
		self._panel = wx.Panel(self)

		self.toolbar.SetDoubleBuffered(True)

		hbox.Add(self.toolbar, 0, wx.ALL|wx.EXPAND, 1)
		hbox.Add((0,0), 1, wx.ALL|wx.EXPAND, 1)
		hbox.Add(self.combo, 0, wx.ALL, 10)
		vbox.Add(hbox, 0, wx.ALL|wx.EXPAND, 1)
		vbox.Add(self._panel, 1, wx.ALL|wx.EXPAND, 0)

		self._panel.SetSizer(self.hbox)
		self._panel.Layout()

		self.SetSizer(vbox)
		self.Layout()
		self.Hide()

	def addToPanel(self, _object, _size):
		if _object is not None:
			self.hbox.Add(_object, _size, wx.ALL|wx.EXPAND, 1)


import horus.util.error as Error
from horus.util import resources

from horus.engine.driver.driver import Driver

class WorkbenchConnection(Workbench):

	def __init__(self, parent):
		Workbench.__init__(self, parent)

		self.driver = Driver()

		#-- Toolbar Configuration
		self.connectTool    = self.toolbar.AddLabelTool(wx.NewId(), _("Connect"), wx.Bitmap(resources.getPathForImage("connect.png")), shortHelp=_("Connect"))
		self.disconnectTool = self.toolbar.AddLabelTool(wx.NewId(), _("Disconnect"), wx.Bitmap(resources.getPathForImage("disconnect.png")), shortHelp=_("Disconnect"))
		self.toolbar.Realize()

		#-- Disable Toolbar Items
		self.enableLabelTool(self.connectTool   , True)
		self.enableLabelTool(self.disconnectTool, False)

		#-- Bind Toolbar Items
		self.Bind(wx.EVT_TOOL, self.onConnectToolClicked   , self.connectTool)
		self.Bind(wx.EVT_TOOL, self.onDisconnectToolClicked, self.disconnectTool)

		self.Layout()

		self.videoView = None

		self.Bind(wx.EVT_SHOW, self.onShow)

	def onShow(self, event):
		if event.GetShow():
			self.updateStatus(self.driver.is_connected)
		else:
			try:
				if self.videoView is not None:
					self.videoView.stop()
			except:
				pass

	def onConnectToolClicked(self, event):
		self.driver.set_callbacks(self.beforeConnect, lambda r: wx.CallAfter(self.afterConnect,r))
		self.driver.connect()

	def onDisconnectToolClicked(self, event):
		self.driver.disconnect()
		self.updateStatus(self.driver.is_connected)

	def beforeConnect(self):
		self.enableLabelTool(self.connectTool, False)
		self.combo.Disable()
		for i in xrange(self.GetParent().menuBar.GetMenuCount()):
			self.GetParent().menuBar.EnableTop(i, False)
		self.driver.board.unplug_callback = None
		self.driver.camera.set_unplug_callback(None)
		self.waitCursor = wx.BusyCursor()

	def afterConnect(self, response):
		ret, result = response

		if not ret:
			if result is Error.WrongFirmware:
				dlg = wx.MessageDialog(self, _("Board has a wrong firmware or an invalid Baud Rate.\nPlease select your Board and press Upload Firmware"), _(result), wx.OK|wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
				self.updateStatus(False)
				self.GetParent().onPreferences(None)
			elif result is Error.BoardNotConnected:
				dlg = wx.MessageDialog(self, _("Board is not connected.\nPlease connect your board and select a valid Serial Name"), _(result), wx.OK|wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
				self.updateStatus(False)
				self.GetParent().onPreferences(None)
			elif result is Error.CameraNotConnected:
				dlg = wx.MessageDialog(self, _("Please plug your camera and try to connect again"), _(result), wx.OK|wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
			elif result is Error.WrongCamera:
				dlg = wx.MessageDialog(self, _("You probably have selected a wrong camera.\nPlease select other Camera Id"), _(result), wx.OK|wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
				self.updateStatus(False)
				self.GetParent().onPreferences(None)
			elif result is Error.InvalidVideo:
				dlg = wx.MessageDialog(self, _("Unplug and plug your camera USB cable and try to connect again"), _(result), wx.OK|wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()

		if self.driver.is_connected:
			self.GetParent().workbenchUpdate(False)
		
		self.updateStatus(self.driver.is_connected)
		self.combo.Enable()
		for i in xrange(self.GetParent().menuBar.GetMenuCount()):
			self.GetParent().menuBar.EnableTop(i, True)
		del self.waitCursor

	def enableLabelTool(self, item, enable):
		self.toolbar.EnableTool(item.GetId(), enable)

	def updateStatus(self, status):
		self.updateToolbarStatus(status)
		if status:
			self.enableLabelTool(self.connectTool   , False)
			self.enableLabelTool(self.disconnectTool, True)
			self.driver.board.set_unplug_callback(lambda: wx.CallAfter(self.GetParent().onBoardUnplugged))
			self.driver.camera.set_unplug_callback(lambda: wx.CallAfter(self.GetParent().onCameraUnplugged))
		else:
			self.enableLabelTool(self.connectTool   , True)
			self.enableLabelTool(self.disconnectTool, False)
			self.driver.board.set_unplug_callback(None)
			self.driver.camera.set_unplug_callback(None)

	def updateToolbarStatus(self, status):
		pass