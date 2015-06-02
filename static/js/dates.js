// /**
//  *  This function takes a start date and a last date 
//  *  and returns a list of dates for this range
//  *
// **/

// var dates_list = [];

// function getDatesList(startDate,number_of_dates)
// {
// 	var start_date = startDate;
// 	var number_of_dates = number_of_dates;

// 	var d = start_date;

// 	for(i=1;i<number_of_dates;i++)
// 	{
// 		d.setDate(d.getDate()+1);
// 		addToList(d);
// 	}
// 	console.log(dates_list);
// }

// function addToList(date)
// {
// 	dates_list.push(date);
// }


var schedule = new Object();
var calendar = new Object();

var CLIENT_ID = '1010275621086-5ghkmj1p5tiv9ehp5l2opjcbrrb5lrb0.apps.googleusercontent.com';
var SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'];

/**
 * Check if current user has authorized this application.
*/
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
    var startDiv = document.getElementById("startDiv");
    if (authResult && !authResult.error)
    {
        startDiv.style.display = "none";
        createSchedule();
    }
    else
    {
        startDiv.style.display = "block";
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
    var start_date = new Date();
    var end_date = new Date();
    end_date.setDate(start_date.getDate()+30);
    var calendarId = "";
    for (i=0;i<calendars.length;i++)
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
                addInstances(events);
            });
    }
}

function start()
{
    checkAuth();
}

function addInstances(events)
{
    if (events.length>0)
    {
        for(i=0;i<events.length;i++)
        {
            var event = events[i];
            var when = event.start.dateTime;
            if (!when) 
            {
                when = event.start.date;
            }
            //console.log(when + " - " + event['summary']);
            if (!(when in schedule))
            {
                schedule[when] = [event['summary']];
            }
            else
            {
                schedule[when].push(event['summary']);
            }
        }
        setFinalSchedule(schedule);
    }   
}

function setFinalSchedule(schedule)
{
    var start_date = new Date();
    var num_of_days = 20;
    var dates = [];


    for (i=0;i<num_of_days;i++)
    {
        var temp_date = new Date();
        temp_date.setDate(temp_date.getDate() + i);
        dates.push(temp_date);
    }

    
}









// Above JS contains calendar API
function DatesInRange1(dStrStart, dStrEnd) {
    var dStart = new Date(dStrStart);
    var dEnd = new Date(dStrEnd);

    var aDates = [];
    aDates.push(dStart);

    if(dStart <= dEnd) {
        for(var d = dStart; d <= dEnd; d.setDate(d.getDate() + 1)) {
            aDates.push(d);
        }
    }

    return aDates;
}

// function to get dates in range

function DatesInRange(date_start,date_end,limit)
{
    var free = [];
    var date_start = new Date(date_start);
    var date_end = new Date(date_end);
    var count = 0;
    var calIds = getCalendarIds(calendar);
    
    while(count<limit)
    {

        var request_items = calendar.events.list({
            'calendarId':calIds[0]['id'],
            'timeMin':start_date.toISOString(),
            'timeMax':end_date.toISOString(),
            'singleEvents':true
        });
        console.log(request_items);
        break;
    }

}