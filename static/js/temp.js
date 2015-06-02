function checkAuth() 
{
    gapi.auth.authorize({
            'client_id':CLIENT_ID,
            'scope':SCOPES,
            'immediate':true
        }, handleAuthResult);
}

/**
 * Handle response from authorization server.
 *
 * @param {Object} authResult Authorization result.
*/
function handleAuthResult(authResult)
{
	var startDiv = document.getElementById("schedule");
	if (authResult && !authResult.error)
	{
		startDiv.style.display = "block";
		createSchedule();
	}
	else
	{
		startDiv.style.display = "none";
	}
}


/*
 * Load the Calendar API
 *
*/
function createSchedule()
{
	gapi.client.load('calendar','v3',startScheduling);
}


function startScheduling()
{
	calendar = gapi.client.calendar;
	getCalendarIds(calendar);
}

function getCalendarIds(calendar)
{
	var calendar = calendar;
	request = calendar.calendarList.list();

	request.execute(function (resp){
			var calendars = resp.items;
			getEvents(calendar,calendars);
		});
}


function getEvents(calendar,calendars)
{
	var count = 0;
	var events = [];
	var str_date = start_date;
	while (count<limit)
	{
		events = get_events_for_date(str_date,calendar,calendars);
		if (events.length == 0)
		{
			count +=1;
			schedule[str_date] = "this day is free";
		}
		else
		{
			for(i=0;i<events.length;i++)
			{
				var event = events[i];
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
		}
	}
	console.log(schedule);
}

function DatesInRange(strt_date,lmt)
{
	start_date.setDate(strt_date.getDate());
	limit = lmt;
	checkAuth();
}

function next_date(current_date)
{
	var next_date = new Date();
	next_date.setDate(current_date.getDate()+1);
	return next_date;
}

function get_events_for_date(start_date,calendar,calendars)
{
	var total_events = [];
	var calendarId = "";
	end_date = next_date(start_date);

	for(i=0;i<calendars.length;i++)
	{
		calendarId = calendars[i]['id'];
		var request_items = calendar.events.list({
			'calendarId':calendarId,
			'timeMin':start_date.toISOString(),
			'timeMax':end_date.toISOString(),
			'singleEvents':true
		});

		request_items.execute(function (resp){
				var events = resp.items;
				if (events.length > 0)
				{
					for(j=0;j<events.length;j++)
					{
						var event = events[j];
						total_events.push(event);
					}
				}
			});
	}
	return total_events;
}