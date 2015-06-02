var start_date = new Date();
var limit = 0;
var calendar = new Object();
var schedule = {};

var final_events = [];
var checked = 1;

var CLIENT_ID = '1010275621086-5ghkmj1p5tiv9ehp5l2opjcbrrb5lrb0.apps.googleusercontent.com';
var SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'];


function checkAuth()
{
	gapi.auth.authorize({
			'client_id':CLIENT_ID,
			'scope':SCOPES,
			'immediate':true
		}, handleAuthResult);
}

function handleAuthResult(authResult)
{
	if (authResult && !authResult.error)
	{
		gapi.client.load('calendar','v3',startScheduling);
	}
	else
	{
		console.log("unauthorized");
	}
}

function startScheduling()
{
	calendar = gapi.client.calendar;


	getCalendarIds();
}

function getCalendarIds()
{
	request = calendar.calendarList.list();

	request.execute(function (resp){
			var calendars = resp.items;

			getEvents(calendars);
		});
}

function getEvents(calendars)
{
	console.log(calendars)
	for(i=0;i<calendars.length;i++)
	{

		var request_items = calendar.events.list({
			'calendarId':calendars[i]['id'],

			'timeMin':start_date.toISOString(),
			'singleEvents':true
		});

		request_items.execute(function (resp){
				var events = resp.items;
				addInstances(events,calendars.length)
			});
	}
}

function addInstances(events,length)
{
	if (checked == length)
	{
		createSchedule(final_events);
	}
	else
	{
		for(i=0;i<events.length;i++)
		{
			final_events.push(events[i]);
		}
		checked+=1;
	}
}

function createSchedule(final_events)
{
	for(i=0;i<final_events.length;i++)
	{
		var event = final_events[i];
        var when = event.start.date;
       	if (!(when in schedule))
        {
           	schedule[when] = [event['summary']];
        }
        else
        {
           	schedule[when].push(event['summary']);
        }
	}
	console.log(schedule);
	sendToServer();
}

function sendToServer()
{
	var http = new XMLHttpRequest();
	var url = "/callback_auth";
	var params = new Object();
	params = JSON.stringify(schedule);

	http.open("POST", url, true);

	//Send the proper header information along with the request
	http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	

	http.onreadystatechange = function() {//Call a function when the state changes.
		
	}
	http.send(params);
}




