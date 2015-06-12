import os.path
import json
import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.options
from tornado import gen
import pymongo
import motor
from bson import json_util
from datetime import date,datetime
from datetime import timedelta
from tornado.options import define,options
import schedule

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
			(r"/schedule",schedule.ScheduleHandler),
			(r"/api/schedule_start",ScheduleApiStartHandler),
			(r"/api/schedule_dates",ScheduleApiDatesHandler),
			(r"/api/schedule_end",ScheduleApiEndHandler)
			

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

#Index page or Registration page 
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
	'''
	loads cal.html file which contains datapicker and range
	'''
	def get(self):
		self.render("cal.html")

class RegisterHandler(tornado.web.RequestHandler):
	'''
	Registration of user and stores details in user_events and users
	'''
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
	'''
	Performs user Login authentication 
	'''
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
	'''
	Callback request from the javascript are handled 
	AJAX request is handled
	'''
	@tornado.web.asynchronous
	@gen.coroutine
	def post(self):
		users_coll = self.application.db.users 

		user_events_coll = self.application.db.user_events
		calendar_coll = self.application.db.calendar
		if self.get_secure_cookie('email'):
			email = self.get_secure_cookie('email')
			user = yield user_events_coll.find_one({'email':email})
			# if user is not initialized
			if not user['initialized'] :
				if user:
					user['events'] = {}
					user_events=user
					data = json.loads(self.request.body.decode('utf-8'))
					timezone = data['timezone']
					del data['timezone']
					timezone_coll = self.application.db.timezone
					time_rec = yield timezone_coll.find_one({'timezone':timezone})
					if not time_rec :
						time_rec['timezone'].append(timezone)
					dates = data.keys()
					for date in dates:
						events = data[date]
						user_events['timezone'] = timezone
						if not date in user_events.keys():
							user_events['events'][date] = []
						for event in events:
							user_events['events'][date].append(event)
					user['initialized'] = True
					yield user_events_coll.save(user)			
					for date in dates:
						rec = yield calendar_coll.find_one({'date':date})
						if rec:
							email = email.replace(".","-")
							# Email encoding to over MongoDB error
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
							#update user events in calendar collection
		self.write("redirect")

class ScheduleApiDatesHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	@gen.coroutine
	def get(self):
		result = dict()
		result['error'] = []
		result['events'] = dict()
		email = self.get_argument('email')
		date_start = ""
		date_end = ""
		try:
			date_start = self.get_argument('start_date')
			date_end = self.get_argument('end_date')
		except:
			result['error'] = "Start (or) End dates not available"
		user_event_col = self.application.db.user_events
		user_rec = yield user_event_col.find_one({'email':email})
		if user_rec :
			if date_start != "" and date_end != "" and date_start<= date_end :
				date_start = str(date_start)
				date_end = str(date_end)
				if date_start in user_rec['events'].keys():
					result['start_date'] = date_start
					while date_start != date_end :
						if date_start in user_rec['events'].keys():
							result['events'][date_start] = user_rec['events'][date_start]
						next_date = datetime.strptime(date_start, '%Y-%m-%d')
						next_date = next_date + timedelta(days=1)
						date_start = str(next_date)
						date_start = date_start[:10]
			else :
				result['error'].append("Start and end date are not informat")
		else :
			result['error'] = 'Email not registered'

		new_data = result

				#new_data = json_util.dumps(result,default=json_util.default)
		self.set_header("X-Frame-Options","SAMEORIGIN")
		self.set_header("Content-Type","application/json")
		self.write(json.dumps(new_data))
class ScheduleApiEndHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	@gen.coroutine
	def get(self):
		result = dict()
		result['error'] = []
		email = self.get_argument('email')
		end_date = ""
		days = ""
		try:
			days = self.get_argument('days')
			end_date = self.get_argument('end_date')
		except:
			if days == "":
				days = 7
		result = dict()
		days = int(days)
		if not email :
			result['error'] = 'Missing email parameter'
		else :
			result['email'] = email
			result['events'] = {}
			#result['end_date'] = end_date
			user_event_col = self.application.db.user_events
			user_rec = yield user_event_col.find_one({'email':email})
			if user_rec :
				dates = user_rec['events'].keys()
				dates.sort()

				if end_date == "":
					end_date = dates[-1]
					end_date = str(end_date)
					for i in range(days):
						if end_date in user_rec['events'].keys():
							result['events'][end_date] = user_rec['events'][end_date]
						next_date = datetime.strptime(end_date, '%Y-%m-%d')
			 			next_date = next_date - timedelta(days=1)
						end_date = str(next_date)
			 			end_date = end_date[:10]
			 	else :
			 		#validate date_start
			 		try:
			 			end_date = str(end_date)
				 		if end_date in user_rec['events'].keys():
				 			result['end_date'] = end_date
					 		for i in range(days):
								if end_date in user_rec['events'].keys():
									result['events'][end_date] = user_rec['events'][end_date]
								next_date = datetime.strptime(end_date, '%Y-%m-%d')
					 			next_date = next_date - timedelta(days=1)
								end_date = str(next_date)
					 			end_date = end_date[:10]
					except :
						result['error'].append("Start date not in format YYYY-MM-DD") 

			else :
				result['error'] = 'Email not registered'

		new_data = result
		#new_data = json_util.dumps(result,default=json_util.default)
		self.set_header("X-Frame-Options","SAMEORIGIN")
		self.set_header("Content-Type","application/json")
		self.write(json.dumps(new_data))



class ScheduleApiStartHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	@gen.coroutine
	def get(self):
		result = dict()
		result['error'] = []
		email = self.get_argument('email')
		date_start = ""
		days = ""
		
		try:
			days = self.get_argument('days')
			date_start = self.get_argument('start_date')
		except:
			if days == "":
				days = 7	
		result = dict()
		days = int(days)
		if not email :
			result['error'] = 'Missing email parameter'
		else :
			result['email'] = email
			result['events'] = {}
			
			user_event_col = self.application.db.user_events
			user_rec = yield user_event_col.find_one({'email':email})
			if user_rec :
				if date_start == "":
					start_date = date.today().isoformat()
					start_date = str(start_date)
					for i in range(days):
						if start_date in user_rec['events'].keys():
							result['events'][start_date] = user_rec['events'][start_date]
						next_date = datetime.strptime(start_date, '%Y-%m-%d')
			 			next_date = next_date + timedelta(days=1)
						start_date = str(next_date)
			 			start_date = start_date[:10]
			 	else :
			 		#validate date_start
			 		try:
			 			date_start = str(date_start)
				 		if date_start in user_rec['events'].keys():
				 			result['start_date'] = date_start
					 		for i in range(days):
								if date_start in user_rec['events'].keys():
									result['events'][date_start] = user_rec['events'][date_start]
								next_date = datetime.strptime(date_start, '%Y-%m-%d')
					 			next_date = next_date + timedelta(days=1)
								date_start = str(next_date)
					 			date_start = date_start[:10]
					except :
						result['error'].append("Start date not in format YYYY-MM-DD") 

			else :
				result['error'] = 'Email not registered'

		#new_data = result
		result['events'].keys().sort()
		new_data = result
		#new_data = json_util.dumps(result,default=json_util.default)
		self.set_header("X-Frame-Options","SAMEORIGIN")
		self.set_header("Content-Type","application/json")
		self.write(json.dumps(new_data))


class LogoutHandler(tornado.web.RequestHandler):
	'''
	User session is detroyed with this handler
	'''
	@tornado.web.authenticated
	def get(self):
		self.clear_cookie("email")
		self.redirect("/")


if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application(),xheaders=True)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()