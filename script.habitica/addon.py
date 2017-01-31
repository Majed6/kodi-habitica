#! python3
# -*- coding: utf-8 -*-
import os
import xbmcaddon
import xbmcgui
import datetime
import resources.lib.httplib2 as httplib2
import urllib
import json

addon = xbmcaddon.Addon()
dialog = xbmcgui.Dialog()
http = httplib2.Http()

class Habitica(xbmcgui.Window):
	def __init__(self):
		self.background = xbmcgui.ControlImage(0, 0, 1280, 720, 'special://home/addons/script.habitica/resources/media/fanart.jpg')
		self.profile = xbmcgui.ControlLabel(450,0,700,50,'XP:0/0 HP:0/0 Gold:0 Silver:0')
		self.habitsButton = xbmcgui.ControlButton(0, 50, 200, 50, 'Habits',textOffsetX=70)
		self.dailiesButton = xbmcgui.ControlButton(200, 50, 200, 50, 'Dailies',textOffsetX=70)
		self.todoButton = xbmcgui.ControlButton(400, 50, 200, 50, 'TODO',textOffsetX=70)
		self.cList = xbmcgui.ControlList(0, 110, 800, 550,selectedColor="0xC0FF0000")
		self.avatar = xbmcgui.ControlImage(900, 90, 350, 350,'special://home/addons/script.habitica/resources/media/icon.png')
		self.addControl(self.background)
		self.addControl(self.profile)
		self.addControl(self.habitsButton)
		self.addControl(self.dailiesButton)
		self.addControl(self.todoButton)
		self.addControl(self.cList)
		self.addControl(self.avatar)
		self.API_Token = addon.getSetting("API_Token").decode("utf-8")
		self.ID = addon.getSetting("ID").decode("utf-8")
	#def onClick(self,controlId):
		#self.close()
	'''def onAction(self, action):
		if action.getId()==4:
			dialog.ok('action',str(action.getId()))
			self.setFocus(self.todoButton)
			dialog.ok('action',str(self.todoButton.getId()))'''
	def onControl(self,Control):
		if Control==self.habitsButton:
			self.getAllhabits()
		elif Control==self.dailiesButton:
			self.getAllDaillies()
		elif Control==self.todoButton:
			self.getAllTasks()
		elif Control==self.cList:
			choice = dialog.yesno('Mark as complete',"Do you want to mark \""+Control.getSelectedItem().getLabel()+"\" as Complete?")#+str(Control.getId())
			if choice:
				self.score(Control.getSelectedItem())
		else:
			Control
	def login(self):
		username = dialog.input('Login Username')
		password = dialog.input('Login Password',option=xbmcgui.ALPHANUM_HIDE_INPUT)
		url = 'https://habitica.com/api/v3/user/auth/local/login'   
		body = {'username': username, 'password': password}
		headers = {'Accept': 'application/json','Content-type': 'application/x-www-form-urlencoded'}
		response, content = http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
		#dialog.ok('response', str(response)) not intersting
		#dialog.ok('response', response['status'])
		if response['status']!="200":
			msg = response['status']+': Login failed. Do you want to retry?'
			choice = dialog.yesno('Login Failed',msg)
			if choice:
				self.login()
			else:
				quit()
				return
		dContent = json.loads(content)
		addon.setSetting(id='API_Token', value=dContent['data']['apiToken'])
		addon.setSetting(id='ID', value=dContent['data']['id'])
	def callAPI(self,method, partialURL, postData):
		if self.API_Token=='':
			self.login()
		baseURL = 'https://habitica.com/api/v3'
		headers = {'Accept': 'application/json','Content-type': 'application/x-www-form-urlencoded','x-api-user':self.ID,'x-api-key':self.API_Token}
		response, content = http.request(baseURL+partialURL, method, headers=headers, body=urllib.urlencode(postData))
		return json.loads(content)

	def getProfile(self):
		profile = self.callAPI('GET', '/members/'+self.ID,'')['data']['stats']
		gold = int(profile['gp'])
		silver = int((profile['gp']-gold)*100)
		level = profile['lvl']
		xp = profile['exp']
		hp = profile['hp'] #max health is always 50
		lvlupAt = int(round((0.25*(level**2)+10*level+139.75)/10)*10)
		tProfile = "XP:"+str(xp)+"/"+str(lvlupAt)+" HP:"+str(hp)+"/50"+" Gold:"+str(gold)+" Silver:"+str(silver)
		self.profile.setLabel(tProfile)
		self.getAvatar()
		return profile
	def getAllTasks(self):
		tasks = self.callAPI('GET','/tasks/user?type=todos','')['data']
		if tasks==[]:
			dialog.ok('All tasks Completed','You have completed all of your tasks!')
			return
		self.cList.reset()
		for task in tasks:
			tTask =task['text']+""
			listitem = xbmcgui.ListItem(tTask,'label2')
			listitem.setProperty('type', 'task')
			listitem.setUniqueIDs({ 'id': task['id']})
			self.cList.addItem(listitem)
	def getAllDaillies(self):
		dailies = self.callAPI('GET','/tasks/user?type=dailys','')['data']
		if dailies==[]:
			dialog.ok('There are no dailies!')
			return
		self.cList.reset()
		#{0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
		weekday = {0: 'm', 1: 't', 2: 'w', 3: 'th', 4: 'f', 5: 's', 6: 'su'}
		today = weekday[datetime.datetime.today().weekday()]
		for daily in dailies:
			if daily['repeat'][today] and not daily['completed']:
				tDaily=daily['text']+""
				listitem = xbmcgui.ListItem(tDaily)
				listitem.setProperty('type', 'daily')
				listitem.setUniqueIDs({ 'id': daily['id']})
				self.cList.addItem(listitem)
		if self.cList.size()==0:
			dialog.ok('No dailies for today!')
	def getAllhabits(self):
		habits = self.callAPI('GET','/tasks/user?type=habits','')['data']
		if habits==[]:
			dialog.ok('There are no habits!')
			return
		self.cList.reset()
		for habit in habits:
			tHabit = habit['text']+""
			listitem = xbmcgui.ListItem(tHabit)
			listitem.setProperty('type', 'habit')
			listitem.setUniqueIDs({ 'id': habit['id']})
			self.cList.addItem(listitem)
	def getAvatar(self):
		avatar = 'https://habitica.com/export/avatar-'+self.ID+'.png'
		self.avatar.setImage(avatar,False)
	def score(self,item):
		before = self.getProfile()
		after = self.callAPI("POST", '/tasks/' + item.getUniqueID('id') + '/score/' + 'up','')['data']
		gold = abs(int(after['gp']-before['gp']))
		silver = abs(int(((after['gp']-int(after['gp']))-(before['gp']-int(before['gp'])))*100))
		xp = after['exp']-before['exp']
		habiticaNotiXP = "★+"+str(xp)+" Experince"
		habiticaNotiCash = "⚫+"+str(gold)+" GOLD"+" ⚪+"+str(silver)+" Silver"
		if item.getProperty('type')=='task':
			dialog.notification('Task scored',habiticaNotiXP,xbmcgui.NOTIFICATION_INFO)
			dialog.notification('Task scored',habiticaNotiCash,xbmcgui.NOTIFICATION_INFO)
			self.getAllTasks()
		elif item.getProperty('type')=='daily':
			dialog.notification('Daily scored',habiticaNotiXP,xbmcgui.NOTIFICATION_INFO)
			dialog.notification('Daily scored',habiticaNotiCash,xbmcgui.NOTIFICATION_INFO)
			self.getAllDaillies()
		elif item.getProperty('type')=='habit':
			dialog.notification('Habit scored',habiticaNotiXP,xbmcgui.NOTIFICATION_INFO)
			dialog.notification('Habit scored',habiticaNotiCash,xbmcgui.NOTIFICATION_INFO)
			self.getAllHabits()
		
win = Habitica()
win.show()
win.getProfile()
win.getAllTasks()

win.doModal()
