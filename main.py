#!/usr/bin/python
# -*- coding: utf-8 -*-  
##########################################################
#
#	autore: 		Damiano Lollini
#	nome prog:		Video To Ogv
#	date:			26/03/2012
#	ver:			1.1
#	descrizione:	converte vari formati video in ogv
#	vers python:	2.7
#
##########################################################

# Copyright © 2011-2013 Damiano Lollini <damiano.lollini@gmail.com>
# 
# This file is part of video to ogv (VTO).
# 
# Video To Ogv is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# Video To Ogv is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
# 
# You should have received a copy of the GNU General Public License along with
# Video To Ogv.  If not, see <http://www.gnu.org/licenses/>.



import time
from threading import *
import psutil
import wx
import os
import subprocess
import sys
from wx.lib.buttons import GenBitmapTextButton
import shutil
import glob
from Queue import Queue, Empty
import json
import wx.lib.agw.advancedsplash as AS
import re


ENABLENOTEBOOK = 1
EXTENSIONFILE = [".mov",".avi",".mp4",".flv",".qt",".ogg"]

testoabout = """Video To Ogv is a simple program 
to convert any file video in 
file ogv with codec theora.

Developed by Damiano Lollini 
in Python using wxPython as 
the GUI toolkit.
Tested on Windows and Linux.

Copyright (C) <2011-2013> Damiano Lollini
https://github.com/damnemo/videotoogv
"""

testolicense = """
Video To Ogv is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as 
published by the Free Software Foundation, either version 3 of 
the License, or (at your option) any later version.

Video To Ogv is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License 
along with Video To Ogv.
If not, see <http://www.gnu.org/licenses/>.
"""


# opzioni ffmpeg2theora
VIDEOQUALITY = 6
ASPECTRATIO = "16:9"


FOLDER = os.path.dirname(sys.argv[0])
CODEC = os.path.join(FOLDER,"codec")
OUTPUTFOLDER = os.path.join(FOLDER,"DIR_OGV")

#ICONFOLDER = os.path.join(FOLDER,"img")
#sys.path.append(ICONFOLDER)

import images


if os.name == "nt":
	CMDOPENFOLDER = "explorer"
	CMDFFMPEG2THEORA = "ffmpeg2theora.exe"
	shellos = True
	## print "windows"	
else:
	CMDOPENFOLDER = "xdg-open"
	CMDFFMPEG2THEORA = "ffmpeg2theora"
	shellos = False	
	## print "linux"

cwd = CODEC
CMDFFMPEG2THEORAFOLDER =  os.path.join(FOLDER,"codec",CMDFFMPEG2THEORA)
ON_POSIX = 'posix' in sys.builtin_module_names

# DRAG AND DROP FILE
#################################################################

# Define File Drop Target class
class FileDrop(wx.FileDropTarget):
	def __init__(self, obj):
		wx.FileDropTarget.__init__(self)
		self.obj = obj

	def OnDropFiles(self, x, y, filenames):
		mioprog.page1.addvideo(filenames)		

# NOTEBOOK CONVERSIONE (PAGEONE)
###########cmd.append######################################################

class PageOne(wx.Panel):
	def __init__(self, parent):

		self.dirname=''
		self.isrunning = False
		# colore sfondo e pulsanti
		self.buttoncolor = '#c2e6f8'
		self.backgroundcolor = '#4aaaf0'
		self.tablecolor = '#c2e6f8'

		wx.Panel.__init__(self, parent)
		self.SetBackgroundColour(self.backgroundcolor)

		############### VARIABILI
		self.selecteditems = []

		############### TABELLA

		# creazione della tabella
		self.textlistafile = wx.ListCtrl(self,wx.ID_ANY, pos=(160,30), size=(580,290), style=wx.LC_REPORT|wx.SIMPLE_BORDER|wx.LC_HRULES)
		self.textlistafile.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnSelected)
		self.textlistafile.Bind(wx.EVT_LIST_ITEM_DESELECTED,self.OnDeselected)
		self.textlistafile.Show(True)
		self.textlistafile.SetBackgroundColour(self.tablecolor)	

		# dimensioni della tabella
		self.textlistafile.InsertColumn(0,"path")
		self.textlistafile.SetColumnWidth(0,320)
		self.textlistafile.InsertColumn(1,"filename")
		self.textlistafile.SetColumnWidth(1,180)
		self.textlistafile.InsertColumn(2,"status")
		self.textlistafile.SetColumnWidth(2,80)

		###############
		fontprogress = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')

		text = wx.StaticBox(self, wx.ID_ANY, '  Lista di conversione dei file in ogv  ', (5, 5), size=(745, 390))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)

		############### testo barre di progressione

		text = wx.StaticText(self, wx.ID_ANY,"Converting file", (15,325))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)

		self.percfile = wx.StaticText(self, wx.ID_ANY,"--%", (116,325))
		self.percfile.SetForegroundColour('BLUE')
		self.percfile.SetFont(fontprogress)

		text = wx.StaticText(self, wx.ID_ANY,"Time Left [sec]", (15,340))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)

		self.timeleft = wx.StaticText(self, wx.ID_ANY,"--:--", (116,340))
		self.timeleft.SetForegroundColour('BLUE')
		self.timeleft.SetFont(fontprogress)

		text = wx.StaticText(self, wx.ID_ANY,"Total progress", (15,365))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)

		self.perctot = wx.StaticText(self, wx.ID_ANY,"--%", (116,365))
		self.perctot.SetForegroundColour('BLUE')
		self.perctot.SetFont(fontprogress)

		############### barre di progessione della conversione
		self.gaugefile = wx.Gauge(self,wx.ID_ANY, 100, pos=(160,330), size=(580,25))
		self.gaugefile.SetBezelFace(3)
		self.gaugefile.SetShadowWidth(3)
		self.gaugetotal = wx.Gauge(self,wx.ID_ANY, 100, pos=(160,360), size=(580,25))
		self.gaugetotal.SetBezelFace(3)
		self.gaugetotal.SetShadowWidth(3)

		############### Create a Text Drop Target object and Link the Drop Target Object
		dest = FileDrop(self.textlistafile)
		self.textlistafile.SetDropTarget(dest)

		############### CREAZIONE DEI BUTTONS
	
		# Button ADDFILE
		self.addfile = GenBitmapTextButton(self, wx.ID_ANY,images.getaddBitmap(),'Add'.rjust(10), (15, 30),(140, 40))
		self.addfile.SetBackgroundColour(self.buttoncolor)
		self.Bind(wx.EVT_BUTTON, self.Onaddfile,self.addfile)
		
		# Button DELETEFILE	
		self.deletefile = GenBitmapTextButton(self, wx.ID_ANY,images.getcancelBitmap(),'Delete'.rjust(10), (15, 80),(140, 40))
		self.deletefile.SetBackgroundColour(self.buttoncolor)
		self.Bind(wx.EVT_BUTTON, self.Ondeletefile,self.deletefile)

		# Button CLEARLIST	
		self.clearlist = GenBitmapTextButton(self, wx.ID_ANY,images.getclearBitmap(),'Clearlist'.rjust(10), (15, 130),(140, 40))
		self.clearlist.SetBackgroundColour(self.buttoncolor)
		self.Bind(wx.EVT_BUTTON, self.OnClearlist,self.clearlist)

		# Button STARTCONV
		self.startconv = GenBitmapTextButton(self, wx.ID_ANY,images.getstartBitmap(),'Start'.rjust(10), (15, 180),(140, 40))
		self.startconv.SetBackgroundColour(self.buttoncolor)		
		self.Bind(wx.EVT_BUTTON, self.OnStart,self.startconv)

		# Button STOPCONV
		self.stopconv = GenBitmapTextButton(self, wx.ID_ANY,images.getstopBitmap(),'Stop'.rjust(10), (15, 230),(140, 40))
		self.stopconv.SetBackgroundColour(self.buttoncolor)
		self.Bind(wx.EVT_BUTTON, self.OnStop,self.stopconv)

		# Button QUIT
		self.quit = GenBitmapTextButton(self, wx.ID_ANY,images.getexitBitmap(),'Quit'.rjust(10), (15, 280),(140, 40))
		self.quit.SetBackgroundColour(self.buttoncolor)
		self.Bind(wx.EVT_BUTTON, self.OnQuit,self.quit)

		self.buttononoff(1,0,0,0,0,1)
			

	def addvideo(self,lista):
		totalevideo = self.textlistafile.GetItemCount()
		oldlista = []

		for i in range (totalevideo): 		#creo la lista nell'elenco
			oldfilename = self.textlistafile.GetItem(i,1).GetText()
			oldlista.append(oldfilename)

		for files in lista:
			++totalevideo
			(filepath, filename) = os.path.split(files)
			(shortname, extension) = os.path.splitext(filename)

			if (self.textlistafile.GetItemCount() >= 10): # video >10?
				dlg = wx.MessageDialog(None,u"Non puoi aggiungere più di 10 video!" ,'Error',wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				continue

			if (extension not in EXTENSIONFILE): # file con estensione errata?
				dlg = wx.MessageDialog(None,'Il file: ' + filename + u' Non è un file video','Error',wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()	
				continue

			if (len(filename) > 50):
				dlg = wx.MessageDialog(None,'Il file: ' + filename + ' ha il nome troppo lungo, rinomina il file','Error',wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()	
				continue 

			match = re.search('[^ ^()^a-zA-Z0-9_.+-]',filename)
			if (match):
				dlg = wx.MessageDialog(None,'Il file: ' + filename + u' contiene dei caratteri non ammessi, rinomina il file. Caratteri ammessi: a..z A..Z 0..9 + - ( ) _ .','Error',wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				continue 				

			if (filename in oldlista):	# file già presente?
				dlg = wx.MessageDialog(None, files + u' è gia presente nella lista!','Error',wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()	
			else:
				self.textlistafile.InsertStringItem(totalevideo,filepath)			
				self.textlistafile.SetStringItem(totalevideo,1,filename)		
				self.textlistafile.SetStringItem(totalevideo,2,"ready")

		if (self.textlistafile.GetItemCount() > 0):
			self.buttononoff(1,1,1,1,0,1)
		else:
			self.buttononoff(1,0,0,0,0,1)

	# FUNZIONI EVENTI SUI PULSANTI
	# ADD BUTTON
	def Onaddfile(self,e):
		stringtemp  = ["*" + x + ";"  for x in EXTENSIONFILE]
		stringtemp = "".join(stringtemp)
		dlg = wx.FileDialog(self, "Scegli i files da convertire in OGV", self.dirname, "", "File video|" + stringtemp, wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
		if dlg.ShowModal() == wx.ID_OK:	
			listafiletemp = dlg.GetPaths()
			self.addvideo(listafiletemp)
		dlg.Destroy()
	
	# DELETE BUTTON	
	def Ondeletefile(self,e):
		self.selecteditems.sort()
		self.selecteditems.reverse()	
		for i in self.selecteditems:
			self.textlistafile.DeleteItem(i)
		self.selecteditems = []
		if self.textlistafile.GetItemCount() == 0:
			self.buttononoff(1,0,0,0,0,1)

	# MAKE OUTPUTFOLDER
	def MakeOutputdir(self):
		global OUTPUTFOLDER		
		if not os.path.exists(OUTPUTFOLDER):
			try:
				os.makedirs(OUTPUTFOLDER)
			except:
				dial = wx.MessageDialog(None, "Impossibile creare la cartella di output a questo indirizzo, Permesso negato.... cambiare indirizzo nel menu option!", 'Error',wx.OK | wx.ICON_ERROR)
				dial.ShowModal()
				return False
		else:
			dirlistfiles = os.path.join(OUTPUTFOLDER,"*")
			dirlistfiles = glob.glob(dirlistfiles)
			for i in dirlistfiles:
				try:
					os.remove(i)
				except:
					dial = wx.MessageDialog(None, 'Errore, il file *** ' + i + u' *** é utilizzato in un altro processo. Chiudere il processo o cambiare la cartella di output nel menu option!', 'Error',wx.OK | wx.ICON_ERROR)
					dial.ShowModal()
					return False
		return True

	# START BUTTON
	def OnStart(self,e):		
		global ENABLENOTEBOOK		
		ENABLENOTEBOOK = 0
		if(self.MakeOutputdir()):
			self.buttononoff(0,0,0,0,1,1)
			if(self.startconvert()):
				time.sleep(2)
				self.renamefile()
			else:
				if self.destroy:
					pass
				else:
					self.buttononoff(1,1,1,1,0,1)
		ENABLENOTEBOOK = 1	

	# STOP BUTTON
	def OnStop(self,event):
		try:
			self.ffmpegpid = self.getpidffmpeg()
			proc = psutil.Process(self.ffmpegpid)
			## print 'ID del processo ffmpeg2theora = ',self.ffmpegpid
			## print 'ID del processo cmd = ',self.fp.pid
			proc.suspend()
		except:
			pass
		dial = wx.MessageDialog(None, 'Sei sicuro di voler fermare la conversione?', 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		ret = dial.ShowModal()				
		if ret == wx.ID_YES:
			self.isrunning = False									# esci dal ciclo for della conversione
			if self.fp.poll() == None:								# se il processo ffmpeg è in corso								
				proc.terminate()										# termina processo
				try:								
					## print "STOP Conversione 1"
					proc.wait(timeout=2)
				except:
					## print "STOP Conversione 1x"
					proc.kill()
			else:													# esci cmq dal ciclo for	
				## print "STOP Conversione 2"
				pass
		else:
			try:
				proc.resume()
			except:
				pass
			## print "RESUME Conversione"
			

	# CLEARLIST
	def OnClearlist(self,e):
		self.selecteditems = []
		self.textlistafile.DeleteAllItems()
		self.buttononoff(1,0,0,0,0,1)

	# QUIT BUTTON
	def OnQuit(self,e):
		self.GetParent().GetParent().chiudoprogramma()

	# SELEZIONE E DESELEZIONE ITEM
	def OnSelected(self,e):
		self.selecteditems.append(e.GetIndex())

	def OnDeselected(self,e):
		self.selecteditems.remove(e.GetIndex())


	def buttononoff(self,pushadd,pushdelete,pushclearlist,pushstart,pushstop,pushquit):
		if pushadd:		
			self.addfile.Enable()
		else:
			self.addfile.Disable()
		if pushdelete:		
			self.deletefile.Enable()
		else:
			self.deletefile.Disable()
		if pushclearlist:		
			self.clearlist.Enable()
		else:
			self.clearlist.Disable()
		if pushstart:		
			self.startconv.Enable()
		else:
			self.startconv.Disable()
		if pushstop:		
			self.stopconv.Enable()
		else:
			self.stopconv.Disable()
		if pushquit:		
			self.quit.Enable()
		else:
			self.quit.Disable()

	def cmdline(self,xfromfilename,xtofilename):
		cmd = []
		cmd.append(CMDFFMPEG2THEORAFOLDER)
		cmd.append('--nosound')
		cmd.append('--frontend')
		cmd.append(xfromfilename)
		cmd.append('-v')
		cmd.append(str(VIDEOQUALITY))
		cmd.append('--aspect')
		cmd.append(ASPECTRATIO)
		cmd.append('-o')
		cmd.append(xtofilename)
		cmd.append('--artist SPIDERNETWORK')
		cmd.append('--title '+xtofilename)
		cmd.append('--copyright SPIDERNETWORK')
		cmd.append('--organization SPIDERNETWORK')
		cmd.append('--contact www.spidernetwork.it')
		#cmd.append('--width')
		#cmd.append('800')
		#cmd.append('--height')
		#cmd.append('450')
		## print cmd
		return cmd

	def checkffmpeg(self):
		if os.path.exists(CMDFFMPEG2THEORAFOLDER):
			## print "codec ffmpeg presente"
			return True
		else:
			dial = wx.MessageDialog(None, u"Attenzione, codec ffmpeg2theora non é presente!", 'Message',wx.OK | wx.ICON_INFORMATION)
			dial.ShowModal()
			## print "codec ffmpeg non presente"
			return False	

	def getpidffmpeg(self):
		pids = psutil.get_pid_list()
		ret = False
		for pid in pids:
			p = psutil.Process(pid)
			if "ffmpeg2theora" in p.name:
				ret = p.pid
		return ret

	def enqueue_output(self,out, queue):
		for line in iter(out.readline, ''):
			queue.put(line)
		out.close()


	def listavideo(self):
		path = self.textlistafile.GetItem(self.video,0).GetText()
		filename = self.textlistafile.GetItem(self.video,1).GetText()
		fromfilename = os.path.join(path,filename)
		if not os.path.isfile(fromfilename):
			self.textlistafile.SetStringItem(self.video,2,"Err")
			## print "Errore al video " + fromfilename + " .. indirizzo errato"
			dial = wx.MessageDialog(None, "Attenzione, indirizzo errato del video\n" + fromfilename + " !", 'Message',wx.OK | wx.ICON_INFORMATION)
			dial.ShowModal()
			return False,fromfilename,False
		else:
			self.textlistafile.SetStringItem(self.video,2,"In process")
			(shortname, extension) = os.path.splitext(filename)
			shortname = shortname.replace(" ","_")
			shortname = shortname.upper()
			newfilename = shortname + ".ogv"
			tofilename = os.path.join(OUTPUTFOLDER,newfilename)
			return True,fromfilename,tofilename


	def ffmpegprocess(self,fromfilename,tofilename):
		info = {}
		cmd = self.cmdline(fromfilename,tofilename)
		q = Queue()

		self.fp = subprocess.Popen(cmd,shell=shellos, stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=1,cwd=cwd,close_fds=ON_POSIX)		
		self.t = Thread(target=self.enqueue_output, args=(self.fp.stdout, q))
		self.t.daemon = True
		self.t.start()

		while (self.isrunning and self.fp.poll() == None):
			while wx.GetApp().Pending():
					wx.GetApp().Dispatch()
					wx.GetApp().Yield(True)
			try:  
				line = q.get_nowait()	
			except Empty:
				pass
			else:
				try:
					info = json.loads(line)
					self.durationbrano = round(float(info["duration"]),2)
					self.positionbrano = round(float(info["position"]),2)
					self.remainingbrano = round(float(info["remaining"]),2)			
					
					self.percbrano = round(((float(info['position']) / float(info['duration'])) * 100),1)					
					self.gaugefile.SetValue(self.percbrano)
					self.percfile.SetLabel(str(self.percbrano)+"%")
					self.timeleft.SetLabel(str(self.remainingbrano))
				
					self.perctotbrani = round((self.video*100 + self.percbrano)/self.totvideo,1)
					self.gaugetotal.SetValue(self.perctotbrani)
					self.perctot.SetLabel(str(self.perctotbrani)+"%")
				except:
					pass

		if self.isrunning:						# TRUE ->fine conversione / FALSE ->esce per STOP o QUIT
			ntimeout = 0
			while not ("result" in info):
				## print ntimeout
				ntimeout = ntimeout + 1
				try:  
					line = q.get_nowait()
					## print "line --> " + line
					info = json.loads(line)					 
				except:
					pass
				if (ntimeout >= 10):
					## print "oltre il timeout"
					return False
			if info.get('result', 'no') == 'ok':	# risultato conversione
				return True
			else:
				return False


	def startconvert(self):
		self.destroy = False
		ret = False		
		self.totvideo = self.textlistafile.GetItemCount()
		
		for self.video in range(self.totvideo):

			if self.checkffmpeg():													# check 1 controllo presenza di ffmpeg2theora
				pass
			else:
				self.reset()
				ret = False
				break	 

			(check,fromfilename,tofilename) = self.listavideo()						# check 2 controllo presenza del file
			if check:
				pass
			else:
				ret = False
				continue

			## print "Conversione del video n ",self.video+1," di ",self.totvideo		

			self.isrunning = True													# variabile di conversione in corso (riferita al ciclo for)
			
			if (self.ffmpegprocess(fromfilename,tofilename)):						# inizio conversione
				self.textlistafile.SetStringItem(self.video,2,"OK")
				ret = True     			
			else:
				self.textlistafile.SetStringItem(self.video,2,"Err")
				ret = False or ret

			if not self.isrunning:													# stop o quit è stato premuto esco dal ciclo
				## print "STOP Conversione dei video"				
				self.reset()
				if self.destroy:													# termine del programma?
					mioprog.Destroy()
					## print "CLOSE PROGRAM EXIT 2"
				return False

		if (ret):																	# se tutti i video sono stati convertiti senza errori
			## print "FINE Conversione dei video"
			pass
		else:
			dial = wx.MessageDialog(None, 'Errore nella conversione ffmpeg2theora.....', 'Error',wx.OK | wx.ICON_ERROR)
			dial.ShowModal()

		self.isrunning = False
		return ret

	def reset(self):			
		self.percfile.SetLabel("--%")
		self.timeleft.SetLabel("--:--")
		self.perctot.SetLabel("--%")
		self.gaugefile.SetValue(0)
		self.gaugetotal.SetValue(0)
		self.selecteditems = []
		self.textlistafile.DeleteAllItems()
		self.buttononoff(1,0,0,0,0,1)

	def renamefile(self):
		global OUTPUTFOLDER
		dial = wx.MessageDialog(None, "Fine conversione!", 'Message',wx.OK | wx.ICON_INFORMATION)
		dial.ShowModal()
		cmd = CMDOPENFOLDER + ' "' + OUTPUTFOLDER + '"'
		subprocess.Popen(cmd,shell=True)
		self.buttononoff(1,1,1,1,0,1)

# NOTEBOOK FFMPEG2THEORA (PAGETWO)
#################################################################
 
class PageTwo(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		global OUTPUTFOLDER

		# font
		fontprogress = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')

		# colore sfondo e pulsanti
		self.buttoncolor = '#c2e6f8'
		self.backgroundcolor = '#4aaaf0'
		self.tablecolor = '#c2e6f8'

		# contorno
		self.SetBackgroundColour(self.backgroundcolor)
		text = wx.StaticText(self, wx.ID_ANY, "Opzioni di conversione", (5,5))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)
		wx.StaticLine(self, wx.ID_ANY, (5, 30), (745,1))
		text = wx.StaticBox(self, wx.ID_ANY, '  FFMPEG2THEORA options  ', (5, 40), size=(745, 160))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)
		# output directory
		text = wx.StaticText(self, wx.ID_ANY,"Cartella di destinazione dei file convertiti", (15, 60))
		font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
		text.SetForegroundColour('BLUE')
		text.SetFont(font)
		self.outputfolder = wx.TextCtrl(self, wx.ID_ANY,OUTPUTFOLDER,pos=(15,85),size=(500,-1),style=wx.TE_READONLY)
		self.outputfolder.Enable(False)
		self.browse = GenBitmapTextButton(self, wx.ID_ANY,images.getbrowseBitmap(),'Browse...'.rjust(10), (520, 82),(120, 30))
		self.browse.SetBackgroundColour(self.buttoncolor)
		self.Bind(wx.EVT_BUTTON, self.OnBrowse,self.browse)		
		# video quality
		text = wx.StaticText(self, wx.ID_ANY,"Video quality", (15, 120))	
		font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
		text.SetForegroundColour('BLUE')
		text.SetFont(font)
		self.quality = wx.Slider(self,wx.ID_ANY,5,1,10,size=(140, 40),pos=(15,140),style= (wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS ))
		self.Bind(wx.EVT_SLIDER, self.OnQuality, self.quality)
		# aspect ratio
		text = wx.StaticText(self, wx.ID_ANY,"Aspect ratio", (180, 120))	
		font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
		text.SetForegroundColour('BLUE')
		text.SetFont(font)
		self.ratio1 = wx.RadioButton(self,wx.ID_ANY, '16:9', (180, 155), style=wx.RB_GROUP)
		self.ratio2 = wx.RadioButton(self,wx.ID_ANY, '4:3', (250, 155))
		self.ratio1.Bind(wx.EVT_RADIOBUTTON, self.OnRatio)
		self.ratio2.Bind(wx.EVT_RADIOBUTTON, self.OnRatio)

	def OnRatio(self,e):
		btn = e.GetEventObject()
		global ASPECTRATIO
		ASPECTRATIO = btn.GetLabel()

	def OnQuality(self,e):
		global VIDEOQUALITY
		VIDEOQUALITY = self.quality.GetValue()
		
	def OnBrowse(self,e):
		dialog = wx.DirDialog(self, "Choose a directory:",style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal() == wx.ID_OK:
			global OUTPUTFOLDER
			OUTPUTFOLDER = dialog.GetPath()
			OUTPUTFOLDER = os.path.join(OUTPUTFOLDER,"DIR_OGV")
			self.outputfolder.SetValue(OUTPUTFOLDER)
		dialog.Destroy()	


# NOTEBOOK ABOUT (PAGETHREE)
#################################################################

class PageThree(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		# font
		fontprogress = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
		fonttitle = wx.Font(20, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
		
		# colore sfondo e pulsanti
		self.backgroundcolor = '#4aaaf0'
		self.tablecolor = '#c2e6f8'

		# contorno e background
		self.SetBackgroundColour(self.backgroundcolor)
		text = wx.StaticText(self, wx.ID_ANY, "About this program", (5,5))
		text.SetForegroundColour('RED')
		text.SetFont(fontprogress)
		wx.StaticLine(self, wx.ID_ANY, (5, 30), (745,1))
		text = wx.StaticBox(self, wx.ID_ANY, '  Video To Ogv ver 1.1 ', (5, 40), size=(745, 280))
		text.SetForegroundColour('RED')
		text.SetFont(fonttitle)
		# testo
		font = wx.Font(10, wx.ROMAN, wx.NORMAL, wx.NORMAL)
		testo = wx.StaticText(self, wx.ID_ANY, testoabout , (20,80),style=wx.ALIGN_LEFT)
		testo.SetFont(font)
		testo.SetForegroundColour('BLACK')
		# LOGO about
		Bmap = images.getaboutBitmap()
		wx.StaticBitmap(self,wx.ID_ANY, Bmap,(350,62))

		# button licenza
		self.licenza = wx.Button(self, 1, 'License', (20, 270))
		self.licenza.Bind(wx.EVT_BUTTON, self.OnLicense)

	def OnLicense(self,e):
		wx.MessageBox(testolicense, 'Info', wx.OK | wx.ICON_INFORMATION)
	"""	"""




# FRAME PRINCIPALE
#################################################################

class MainFrame(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title , size=(770,470), style = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))	
		self.SetIcon(images.getlogoIcon())

	# COSTRUZIONE DEL FRAME E DEI NOTEBOOK

		# Here we create a panel and a notebook on the panel
		nb = wx.Notebook(self, wx.ID_ANY)

		# create the page windows as children of the notebook
		self.page1 = PageOne(nb)
		self.page2 = PageTwo(nb)
		self.page3 = PageThree(nb)

		# add the pages to the notebook with the label to show on the tab
		nb.AddPage(self.page1, "Conversion List")
		nb.AddPage(self.page2, "Option")
		nb.AddPage(self.page3, "About")

		sizer = wx.BoxSizer()
		sizer.Add(nb, 1, wx.EXPAND)
		self.SetSizer(sizer)

		# eventi sul frame
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
		self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

		il = wx.ImageList(32, 32)
		img0 = il.Add(images.getdiscoBitmap())
		img1 = il.Add(images.getoptionBitmap())
		img2 = il.Add(images.getinfoBitmap())
		nb.AssignImageList(il)
		nb.SetPageImage(0, img0)
		nb.SetPageImage(1, img1)
		nb.SetPageImage(2, img2)

		self.Centre()

	# FUNZIONE EVENTO SUL CAMBIO DEL NOTEBOOK
	def OnPageChanging(self, event):
		if not ENABLENOTEBOOK:
			event.Veto()
			dial = wx.MessageDialog(None, 'Processo di conversione in corso...', 'Information',
			wx.OK | wx.ICON_INFORMATION)
			dial.ShowModal()

	# FUNZIONE CHIUSURA FRAME
	def OnCloseFrame(self, event):
		self.chiudoprogramma()

	def chiudoprogramma(self):
		try:
			self.ffmpegpid = self.page1.getpidffmpeg()
			proc = psutil.Process(self.ffmpegpid)
			## print 'ID del processo ffmpeg2theora = ',self.ffmpegpid
			## print 'ID del processo cmd = ',self.page1.fp.pid
			proc.suspend()
		except:
			pass
		dial = wx.MessageDialog(None, 'Sei sicuro di voler uscire?', 'Question',wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		ret = dial.ShowModal()
		if ret == wx.ID_YES:						
			if self.page1.isrunning:
				self.page1.destroy = True
				self.page1.isrunning = False
				proc.terminate()
				try:										
					## print "STOP Conversione 1"
					proc.wait(timeout=2)
				except:
					## print "STOP Conversione 1x"
					proc.kill()
			else:
				mioprog.Destroy()
				## print "CLOSE PROGRAM EXIT 1"
		else:
			if self.page1.isrunning:
				proc.resume()
				## print "RESUME Conversione"
			## print "RETURN TO PROGRAM"


class MiaApp(wx.App):
	def OnInit(self):
		mysplashscreen = images.getsplashscreenBitmap()
		shadow = wx.Color(0,0,0)
		self.MySplash = AS.AdvancedSplash(None, bitmap=mysplashscreen, timeout=5000,
										agwStyle=AS.AS_TIMEOUT |
										AS.AS_CENTER_ON_PARENT |
										AS.AS_SHADOW_BITMAP,
										shadowcolour = shadow)

		self.MySplash.Bind(wx.EVT_CLOSE, self.Onclosesplash)	
		wx.Yield()
		return True
	
	def Onclosesplash(self,event):
		self.MySplash.Hide()
		mioprog.Show()
		event.Skip()



# MAIN
#################################################################

if __name__ == '__main__':
	app = MiaApp()
	mioprog = MainFrame(None,wx.ID_ANY,"Video to OGV")	
	app.MainLoop()






