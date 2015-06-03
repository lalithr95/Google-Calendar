import os.path
import json
import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.options
from tornado import gen
import pymongo
import motor
from datetime import date,datetime
from datetime import timedelta
from tornado.options import define,options

define("port",default=8000,help="run on this port",type=int)
url = 'mongodb://ganadiniakshay:intigrent123@ds043062.mongolab.com:43062/calendar'

#client = pymongo.MongoClient(url)
#db = client.calendar
class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/",IndexHandler),
			(r"/cal",CalHandler),
			(r"/register",RegisterHandler),
			(r"/login",LoginHandler),
			(r"/callback_auth",CallBackHandler),
			(r"/logout",LogoutHandler),
			(r"/schedule",ScheduleHandler)
			

		]
		settings = dict(
				template_path = os.path.join(os.path.dirname(__file__),"templates"),
				static_path = os.path.join(os.path.dirname(__file__),"static"),
				cookie_secret="fjkhkfhsdkjhgkjhfue32g747498iehf8374nfjf!@#!jfiuyif",
				xsrf_cookies=False,
				login_url = "/login",
				debug=True
			)
		client=motor.MotorClient(url)
		self.db = client.calendar
		tornado.web.Application.__init__(self,handlers,**settings)


class IndexHandler(tornado.web.RequestHandler):
	def get(self):
		if self.get_secure_cookie('email'):
			self.render("calendar.html")
		else :
			self.render("index.html")



#extends get current user
class BaseHandler(tornado.web.RequestHandler):
	"""
		overrides get current user
	"""
	def get_current_user(self):
		email=self.get_secure_cookie('email')
		if email:
			users = self.application.db.users
			user = users_coll.find_one({'email':email})
			if user:
				return user



class CalHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("cal.html")

class RegisterHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html")
	@tornado.web.asynchronous
	@gen.coroutine
	def post(self):
		users = dict()
		user_events = dict()
		flash = dict()
		users_coll = self.application.db.users
		users_events_coll = self.application.db.user_events
		username = self.get_argument('username')
		email = self.get_argument('email')
		password = self.get_argument('password')
		confirm = self.get_argument('confirm')
		if password == confirm :

			users['email'] = email
			users['username'] = username
			users['password'] = password
			yield users_coll.insert(users)
			user_events['email'] = email
			user_events['events'] = {}
			user_events['initialized'] = False
			yield users_events_coll.insert(user_events)
			self.render('calendar.html',flash=flash)
		else :
			flash['failure'] = "Invalid Details"
			self.render('register.html',email=email,username=username,password=password,confirm=confirm)



class LoginHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html")
	@tornado.web.asynchronous
	@gen.coroutine
	def post(self):
		users_coll = self.application.db.users
		email = self.get_argument("lemail")
		password = self.get_argument("lpassword")
		currentuser = yield users_coll.find_one({'email':email})
		if currentuser: 
			loginpassword = password
			if loginpassword == currentuser['password']:
				currentusername = currentuser['username']
				self.set_secure_cookie("email",email)
				self.render("calendar.html")
			else:
				self.write("hey please enter the pass word correctly")
		else:
			self.write("please register")

class CallBackHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	@gen.coroutine
	def post(self):
		

		users_coll = self.application.db.users 

		user_events_coll = self.application.db.user_events
		calendar_coll = self.application.db.calendar
		if self.get_secure_cookie('email'):

			email = self.get_secure_cookie('email')
			user = yield user_events_coll.find_one({'email':email})

			print user
			if not user['initialized'] :
				if user:
					user['events'] = {}
					user_events=user

					data = json.loads(self.request.body.decode('utf-8'))
					timezone = data['timezone']
					del data['timezone']
					dates = data.keys()

					#print dates

					for date in dates:
						events = data[date]
						if not date in user_events.keys():
							user_events['events'][date] = []
						for event in events:
							user_events['events'][date].append(event)
					user['initialized'] = True
					yield user_events_coll.save(user)
				# for calendar

					
					
					for date in dates:
						rec = yield calendar_coll.find_one({'date':date})
						if rec:
							email = email.replace(".","-")
							events = data[date]
							if timezone in rec['events'].keys():
								if not email in rec['events'][timezone].keys():
									rec['events'][timezone][email] = []
								for event in events:
									rec['events'][timezone][email].append(event)
								
							else:
								rec['events'][timezone] = {}
								rec['events'][timezone][email] = []
								for event in events:
									rec['events'][timezone][email].append(event)
							
							yield calendar_coll.save(rec)

		self.write("redirect")

					
	



class ScheduleHandler(tornado.web.RequestHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("cal.html")

	@tornado.web.asynchronous
	@gen.coroutine
	def post(self):
		limit = self.get_argument("range")
		limit = int(limit)
		start_date = self.get_argument("date")

		

		# start_date = datetime.strptime(start_date, '%Y-%m-%d'),isoformat()
		start_date = start_date[:10]
		print start_date
		user_events_coll = self.application.db.user_events
		count = 0
		dates = {}
		# { 
		# 	alloted : []
		# 	free : []
		# }
		temp_dates = []
		rec = yield user_events_coll.find_one({'email':self.get_secure_cookie('email')})
		while count<limit:

			if rec :
				count+=1
				
		 		if not start_date in rec['events'].keys() :
		 			count+=1
		 			dates[start_date] = "Free day"
		 			
		 			
		 		else :

		 			dates[start_date] = rec['events'][start_date]
		 		start_date = datetime.strptime(start_date, '%Y-%m-%d')
		 		start_date = start_date + timedelta(days=1)
		 		temp_dates.append(start_date)
		 		start_date = str(start_date)
		 		start_date = start_date[:10]
		 		# print dates

		#print dates
		temp = dates
		data = []
		for key in sorted(temp):
			tup = (key,temp[key])
			# tup = tup + str(key) + temp[key]
			
			print tup
			data.append(tup)

		self.render("display.html",data=data)




		




class LogoutHandler(tornado.web.RequestHandler):
	
	@tornado.web.authenticated
	def get(self):
		self.clear_cookie("email")
		self.redirect("/")


if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application(),xheaders=True)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()