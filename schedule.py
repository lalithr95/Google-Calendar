import tornado.web
from tornado import gen
import pymongo
import motor
from datetime import date,datetime
from datetime import timedelta
from tornado.options import define,options



#Schedule free date list from the user
class ScheduleHandler(tornado.web.RequestHandler):
	'''
	Schedule get the free date list in @data
	Updates free list to calendar and user_events collection
	@data [(email,free_date)...]

	'''
	@tornado.web.authenticated
	def get(self):
		self.render("cal.html")

	@tornado.web.asynchronous
	@gen.coroutine
	def post(self):
		limit = self.get_argument("range")
		limit = int(limit)
		start_date = self.get_argument("date")
		start_date = start_date[:10]
		future_start_date = start_date
		user_events_coll = self.application.db.user_events
		count = 0
		dates = {}
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
		temp = dates
		data = []
		for key in sorted(temp):
			tup = (key,temp[key])
			data.append(tup)
		self.render("display.html",data=data)

		# storing data to calendar and user_events
		email = self.get_secure_cookie('email')
		calendar_coll = self.application.db.calendar
		if rec :
			rec_events = rec['events'].keys()
			rec_events.sort()
			last_day = rec_events[-1]
			while start_date != last_day :
				if not start_date in rec['events'].keys() :
					rec['events'][start_date] = "Free day"
				start_date = datetime.strptime(start_date, '%Y-%m-%d')
		 		start_date = start_date + timedelta(days=1)
		 		start_date = str(start_date)
		 		start_date = start_date[:10]
		 	timezone = rec['timezone']
		 	yield user_events_coll.save(rec)
		 	new_email = email.replace(".","-")
		 	# Email is encode by replacing . with -
		 	for tup in data :
		 		cal_rec = yield calendar_coll.find_one({'date':tup[0]})
		 		if cal_rec:
		 			# if timezone is not available in cal_rec events
			 		if not timezone in cal_rec['events'].keys():
			 			cal_rec['events'][timezone] = {new_email : []}	
			 			cal_rec['events'] = {timezone:email_rec}
			 		else :
			 		# if timezone is avaiable and email is not available
			 			if not new_email in cal_rec['events'][timezone].keys() :
			 				cal_rec['events'][timezone][new_email] = []
			 		cal_rec['events'][timezone][new_email].append("Free date")
			 		print cal_rec['date']
			 		yield calendar_coll.save(cal_rec)

			