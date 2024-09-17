# Must precede any llm module imports
from langtrace_python_sdk import langtrace
from dotenv import load_dotenv
load_dotenv()

LANG_TRACE_API_KEY = os.getenv("LANG_TRACE_API_KEY")
langtrace.init(api_key = LANG_TRACE_API_KEY)

import os
from datetime import datetime, timedelta, time
import calendar
import asyncio

from fasthtml.common import *
from fasthtml.oauth import GitHubAppClient, GoogleAppClient

from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI
from llama_index.llms.groq import Groq
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.core.agent import ReActAgent



css = Link(rel="stylesheet", href="static/styles.css")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# github_client = GitHubAppClient(
#     client_id=GITHUB_CLIENT_ID,
#     client_secret=GITHUB_CLIENT_SECRET,
#     redirect_uri="http://localhost:5001/auth_redirect",
# )

client = GoogleAppClient(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri="https://localhost:5001/auth_redirect"
)


login_link = client.login_link(redirect_uri=GOOGLE_REDIRECT_URI)

def before(req, session):
    auth = req.scope['auth'] = session.get('user_id', None)
    print(f"Session: {session}")  # Debug print
    print(f"Auth: {auth}")  # Debug print
    if not auth: 
        print("Redirecting to login")  # Debug print
        return RedirectResponse('/login', status_code=303)
    print("Authentication successful")  # Debug print

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', r'.*\.js', '/login', '/auth_redirect'])

# Initialize FastHTML app with a database for events
app, rt, events, Event = fast_app('calendar.db', live=True, debug=True,
                                 id=int, user_id=str, date=str, start_time=str, end_time=str, 
                                 title=str, description=str, pk='id', hdrs=(css,), before=bware)



setup_toasts(app)

# --- Helper Functions ---
def get_week_dates(week_offset: int):
    today = datetime.today()
    target_date = today + timedelta(weeks=week_offset)
    start_of_week = target_date - timedelta(days=target_date.weekday())
    return [start_of_week + timedelta(days=i) for i in range(7)]

def format_time(hour):
    return f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}"

@rt
def filter_events(auth, date: str, end_date: str = None):
    items = [o for o in events() if o.user_id == auth]
    if end_date:
        filtered_items = [item for item in items if date <= item.date <= end_date]
    else:
        filtered_items = [item for item in items if item.date == date]
    event_list = []
    for item in filtered_items:
        if item.start_time and item.end_time:
            event_dict = {
                "id": item.id,
                "date": item.date,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "title": item.title if item.title else "No Title",  # Ensure there's always a title
                "description": item.description
            }
            # print(f"Filtered event: {event_dict}")  # Add this debug print
            event_list.append(event_dict)
    return event_list


def get_events_by_date(auth, date: str):
    all_events = [o for o in events() if o.user_id == auth]
    filtered_events = [event for event in all_events if event.date == date]
    return [event.id for event in filtered_events]

def get_start_and_end_time(auth, date: str):
    all_events = [o for o in events() if o.user_id == auth]
    filtered_events = [event for event in all_events if event.date == date]
    return [(event.start_time, event.end_time) for event in filtered_events]

# for event in get_start_and_end_time("2024-08-31"):
#     print(f'event: {event}')

def del_events_by_date(date: str):
    event_ids = get_events_by_date(date)
    for event_id in event_ids:
        events.delete(event_id)
# Example usage:
# date = "2024-08-30"
# del_events_by_date(date)

# --- Calendar View ---
def create_calendar_grid(week_dates, week_events):
    try:
        # Week days header
        # This part is creating the header for the calendar grid
        # It consists of a "Time" column and columns for each day of the week
        header = Header(
            # First column for "Time"
            Div("Time", cls="day-header", id="day-header-0"),
            *[Div(
                day.strftime("%a %d %b"), 
                cls=f"day-header {'today' if day.date() == datetime.today().date() else ''}", 
                id=f"day-header-{i+1}"
            ) for i, day in enumerate(week_dates)],
            cls="calendar-header"
        )
        # print(f"Header classes: {[div.attrs.get('class') for div in header.children if hasattr(div, 'attrs')]}")
        
        # Preprocess events into a dictionary for faster lookup
        events_by_day = {}
        for event in week_events:
            day = event['date']
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

        processed_events = set()

        # Time slots for each day
        # This part is creating the time slots for the calendar grid
        time_slots = []
        for hour in range(24):
            # Create a row for each hour
            time_row = [Div(format_time(hour), cls="time-label", id=f"time-label-{hour}")]
            
            # For each day in the week
            for day in week_dates:
                day_str = day.strftime("%Y-%m-%d")
                slot_id = f"slot-{day_str}-{hour:02d}"

                day_events = [event for event in week_events if event['date'] == day_str]

                # processed_events = set()
                slot_content = []  # To keep track of processed events

                for event in day_events:
                    event_start = datetime.strptime(event['start_time'], "%H:%M").time()
                    event_end = datetime.strptime(event['end_time'], "%H:%M").time()

                    # Calculate the event's duration in hours
                    event_duration = calculate_event_duration(event_start, event_end)

                    # Check if the event starts within the current hour or spans across it
                    if event_start.hour <= hour < event_start.hour + event_duration:
                        # Calculate top position and height
                        event_top = 0
                        if event_start.hour == hour:
                            event_top = (event_start.minute / 60) * 100

                        # Calculate event height based on start and end hours
                        if event_end.hour == hour:  # Event ends within this hour
                            event_height = (event_end.minute / 60) * 100 - event_top
                        elif event_start.hour == hour:  # Event starts within this hour
                            event_height = 100 - event_top
                        else:  # Event spans the entire hour
                            event_height = 100
                        # Debug print
                        # print(f"Rendering event in hour {hour}: top={event_top}%, height={event_height}%")

                        event_title = Div(event['title'], cls="event-title")
                        
                        # Define event buttons
                        event_buttons = Div(
                            Button("Edit", 
                                cls="edit-event",
                                hx_get=f"/edit_event_form/{event['id']}",
                                hx_target="#modal-content",
                                hx_swap="outerHTML",  # Change hx-swap to outerHTML
                                hx_trigger="click"),
                            Button("Delete", 
                                cls="delete-event",
                                hx_get=f"/delete_event_form/{event['id']}",
                                hx_target="#modal-content",
                                hx_swap="outerHTML",  # Change hx-swap to outerHTML
                                hx_trigger="click"),
                            cls="event-buttons"
                        )
                        
                        event_div = Div(
                            event_title,
                            event_buttons,
                            cls="event",
                            style=f"top: {event_top}%; height: {event_height}%;",
                            title=f"Debug: top={event_top}%, height={event_height}%, title='{event['title']}'"
                        )
                        slot_content.append(event_div)
                
                # Define the add button for empty slots
                add_button = Button("+", 
                                    cls="add-event",
                                    hx_get=f"/add_event_form/{day_str}/{hour:02d}",
                                    hx_target="#modal-content",
                                    hx_trigger="click")

                # Add the slot content and add button to the time row
                time_row.append(Div(*slot_content, add_button if not slot_content else None, cls="time-slot", id=slot_id))
            
            # Add the completed row to time_slots
            # This line takes all the elements in time_row (the time label and all time slots for that hour)
            # and creates a new Div with the class "time-row" to represent a full row in the calendar
            time_slots.append(Div(*time_row, cls="time-row"))
        # This line creates an empty modal container for dynamic content
        # It will be populated with forms for adding, editing, or deleting events
        modal = Div(id="modal-content")

        # Return the complete calendar grid
        # calendar_grid = Div(header, *time_slots, modal, cls="calendar-grid", id="calendar-content")
        calendar_grid = Div(
            Div(header),
            Div(*time_slots, cls="scrollable-grid"),
            cls="calendar-grid",
            id="calendar-content"
        )
        return calendar_grid
    except Exception as e:
        print(f"Error in create_calendar_grid: {str(e)}")
        import traceback
        traceback.print_exc()
        return Div(f"Error creating calendar: {str(e)}", id="calendar-content")


def calculate_week_offset(selected_year):
    today = datetime.now().date()
    selected_date = datetime(selected_year, today.month, today.day).date()
    return (selected_date.isocalendar()[1] - today.isocalendar()[1]) + \
           (selected_year - today.year) * 52

# Define the toggle outside the function
def create_toggle(year, week_offset):
    return Div(
            Div(
                A("Logout", href="/logout", cls="logout-button"),
                cls="logout"
                ),
            Div(
                Div(
                    Select(
                        *[Option(str(y), value=y, selected=(y == year)) for y in range(year - 5, year + 6)],
                        id="year-selector",
                        onchange="window.location.href='/?year=' + this.value"
                    ),
                    Div(
                        Button("", id="prev-week",
                            hx_get=f"/?year={year}&week_offset={week_offset-1}",
                            hx_target="#calendar-container", hx_swap="innerHTML"),
                        Button("", id="next-week", 
                            hx_get=f"/?year={year}&week_offset={week_offset+1}",
                            hx_target="#calendar-container", hx_swap="innerHTML"),
                        cls="week-toggle-container"
                    ),
                    cls="year-and-week-container"
                ),
                Button("Smart Requests", cls="smart-form-button", hx_get="/smartform",
                    hx_target="#modal-content", hx_swap="outerHTML"),
                cls="nav-container"
            ),
        cls="toggle-logout"
    )
    

@rt("/")
def get(auth, htmx=None, year: int = None, week_offset: int = 0):
    current_year = datetime.now().year
    year = int(year) if year else current_year
    week_offset = int(week_offset)

    # Calculate the new week offset based on the selected year
    year_based_offset = calculate_week_offset(year)
    total_offset = year_based_offset + week_offset

    print(f"Year: {year}, Week offset: {total_offset}")
    week_dates = get_week_dates(total_offset)
    
    # Fetch events for the week
    week_events = []
    for date in week_dates:
        day_events = filter_events(auth, date.strftime("%Y-%m-%d"))
        week_events.extend(day_events)

    toggle = create_toggle(year, week_offset)

    calendar_grid = create_calendar_grid(week_dates, week_events)

    # Rename this to 'calendar_container' to avoid confusion
    calendar_container = Div(
        toggle,
        calendar_grid,
        id="calendar-container"
    )

    modal_script = Script("""
                          
        // JavaScript to scroll to 8 AM
        document.addEventListener('DOMContentLoaded', function() {
            const scrollableGrid = document.querySelector('.scrollable-grid'); 
            const eightAMLabel = scrollableGrid.querySelector('#time-label-8'); 
            if (eightAMLabel) {
                // Calculate the distance from the top of the scrollable grid to the 8 AM label
                const offsetTop = eightAMLabel.getBoundingClientRect().top - scrollableGrid.getBoundingClientRect().top;
                
                // Scroll to the calculated offset
                scrollableGrid.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth' 
                });
            }
        });
                          
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            if (evt.detail.target.id === 'modal-content') {
                evt.detail.target.classList.add('active');
            }
        });

        document.body.addEventListener('htmx:beforeSwap', function(evt) {
            if (evt.detail.target.id === 'calendar-container') {
                var modal = document.getElementById('modal-content');
                if (modal) {
                    modal.classList.remove('active');
                }
                document.getElementById('modal-content').innerHTML = '';
            }
        });

        document.body.addEventListener('htmx:afterSwap', function(evt) {
            if (evt.detail.target.id === 'modal-content') {
                if (evt.detail.target.querySelector('#calendar-content')) {
                    // If the response contains a new calendar grid, swap it into place
                    document.getElementById('calendar-content').outerHTML = 
                        evt.detail.target.querySelector('#calendar-content').outerHTML;
                    // Close the modal
                    evt.detail.target.classList.remove('active');
                } else {
                    // Otherwise, just show the modal
                    evt.detail.target.classList.add('active');
                }
            }
        });

        // Use event delegation for add and delete event buttons
        document.body.addEventListener('click', function(evt) {
            if (evt.target.classList.contains('add-event') || evt.target.classList.contains('delete-event')) {
                var modal = document.getElementById('modal-content');
                if (modal) {
                    modal.classList.add('active');
                }
            }
        });

        // Reinitialize HTMX on newly added content
        document.body.addEventListener('htmx:afterSettle', function(evt) {
            htmx.process(evt.detail.target);
        });
""")


    debug_script = Script("""
        document.body.addEventListener('htmx:beforeRequest', function(evt) {
            console.log('HTMX request about to be made:', evt.detail);
        });

        document.body.addEventListener('htmx:afterRequest', function(evt) {
            console.log('HTMX request completed:', evt.detail);
        });

        document.body.addEventListener('htmx:responseError', function(evt) {
            console.error('HTMX response error:', evt.detail);
            alert('An error occurred. Please try again.');
        });

        document.body.addEventListener('htmx:sendError', function(evt) {
            console.error('HTMX send error:', evt.detail);
        });

        document.body.addEventListener('htmx:targetError', function(evt) {
            console.error('HTMX target error:', evt.detail);
        });

        document.body.addEventListener('submit', function(evt) {
            if (evt.target.id === 'edit-event-form') {  // Target the edit form
                evt.preventDefault();
                console.log('Edit event form submitted');

                var form = evt.target;
                var eventId = form.getAttribute('data-event-id');  // Get event ID
                var startTime = form.querySelector('[name="start_time"]').value;
                var endTime = form.querySelector('[name="end_time"]').value;
                var url = `/update_event/${eventId}/${startTime}/${endTime}`;

                htmx.ajax('PUT', url, {  // Use PUT request for updating
                    target: '#calendar-content',
                    swap: 'outerHTML',
                    values: {
                        title: form.querySelector('[name="title"]').value,
                        description: form.querySelector('[name="description"]').value,
                        date: form.getAttribute('data-date')  // Include date in values
                    }
                });
            }
        });

        document.body.addEventListener('click', function(evt) {
        if (evt.target.id === 'cancel-button') {
            console.log('Cancel button clicked');
            var modal = document.getElementById('modal-content');
            if (modal) {
                modal.classList.remove('active'); // Hide the modal
            }
            htmx.ajax('GET', '/', {target: '#calendar-container', swap: 'innerHTML'});
            }
        });

        document.body.addEventListener('htmx:afterSwap', function(evt) {
            if (evt.detail.target.id === 'calendar-content') {
                htmx.process(evt.detail.target); 
            }
        });
    """)

    return Main(
        css,
        calendar_container,  # Use the new name here
        Div(id="modal-content"),
        modal_script,
        debug_script
    )
        
  


def calculate_event_duration(start_time, end_time):
    if end_time > start_time:
        return (datetime.combine(datetime.today(), end_time) - 
                datetime.combine(datetime.today(), start_time)).seconds / 3600
    else:
        # Handle cases where the event spans midnight
        return ((datetime.combine(datetime.today(), end_time) + timedelta(days=1)) - 
                datetime.combine(datetime.today(), start_time)).seconds / 3600

# --- API Endpoints ---

@rt('/all_events')
def get(auth):
    # Retrieve all events and display them as a list
    items = [Li(o) for o in events() if o.user_id == auth]
    return Titled('Events', Ul(*items))

@rt('/add_event_form/{date}/{hour}')
def get(date: str, hour: int):
    start_time = f"{hour:02d}:00"
    end_time = f"{(hour + 1) % 24:02d}:00"
    return Div(
        Div(
            H3("Add New Event", cls="form-title"),
            Form(
                Input(type="text", name="title", placeholder="Event Title", required=True),
                Textarea(name="description", placeholder="Event Description"),
                Div(
                    Label("Start Time:"),
                    Input(type="time", name="start_time", value=start_time, required=True),
                    Label("End Time:"),
                    Input(type="time", name="end_time", value=end_time, required=True),
                    cls="time-inputs"
                ),
                Div(
                    Button("Cancel", type="button", id="cancel-button"),
                    Button("Save", type="submit", id="save-button"),
                    cls="form-buttons"
                ),
                cls="event-form",
                id="add-event-form",
                hx_post=f"/newevent/{date}",
                hx_target="#calendar-container",  # Changed from "#calendar-content"
                hx_swap="innerHTML"  # Changed from "outerHTML"
            ),
            cls="modal-content"
        ),
        cls="modal active",
        id="modal-content"
    )


@rt('/delete_event_form/{event_id}')
def get(event_id: int):
    return Div(
        Div(
            H3("Delete Event", cls="form-title"),
            P("Are you sure you want to delete this event?"),
            Form(
                Button("Cancel", type="button", hx_get="/", hx_target="#calendar-container", hx_swap="innerHTML"), 
                Button("Delete", type="submit", cls="delete-confirm"),
                cls="event-form",
                hx_delete=f"/del_event/{event_id}",
                hx_target="#calendar-container",
                hx_swap="innerHTML"
            ),
            cls="modal-content"
        ),
        cls="modal active",
        id="modal-content"
    )

@rt('/newevent/{date}')
def post(auth, date: str, title: str = Form(...), description: str = Form(None), 
         start_time: str = Form(...), end_time: str = Form(...)):
    try:
        print(f"Creating new event: date={date}, start_time={start_time}, end_time={end_time}, title='{title}', description='{description}'")
        
        # Check for duplicate events
        all_events = [o for o in events() if o.user_id == auth]
        duplicate_event = next((event for event in all_events if event.date == date and 
                                event.start_time == start_time and event.end_time == end_time and 
                                event.title == title), None)
        
        if duplicate_event:
            print(f"Duplicate event detected: date={date}, start_time={start_time}, end_time={end_time}, title='{title}'")
            return
        
        new_event = dict(user_id = auth, date=date, start_time=start_time, end_time=end_time, 
                         title=title, description=description)
        inserted_event = events.insert(new_event)
        print(f"Inserted event: {inserted_event}")
        
        # Fetch the updated week data
        event_date = datetime.strptime(date, "%Y-%m-%d").date()
        today = datetime.now().date()
        week_offset = (event_date.isocalendar()[1] - today.isocalendar()[1])
        week_dates = get_week_dates(week_offset)
        week_events = []
        for day in week_dates:
            day_events = filter_events(auth, day.strftime("%Y-%m-%d"))
            week_events.extend(day_events)
        
        # Create toggle and calendar grid
        toggle = create_toggle(event_date.year, week_offset)
        calendar_grid = create_calendar_grid(week_dates, week_events)
        
        # Return the updated calendar container with toggle and grid
        return Div(
            toggle,
            calendar_grid,
            id="calendar-container"
        )
    except Exception as e:
        print(f"Error in post: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    
@rt('/edit_event_form/{event_id}')
def get(auth, event_id: int):
    event = events.get(event_id)
    if event.user_id == auth:
        start_time = event.start_time
        end_time = event.end_time
        return Div(
            Div(
                H3("Edit Event", cls="form-title"),
                Form(
                    Input(type="text", name="title", placeholder="Event Title", required=True, value=event.title),
                    Textarea(name="description", placeholder="Event Description", value=event.description),
                    Input(type="hidden", name="date", value=event.date),  # Add hidden input for date
                    Div(
                        Label("Start Time:"),
                        Input(type="time", name="start_time", value=start_time, required=True),
                        Label("End Time:"),
                        Input(type="time", name="end_time", value=end_time, required=True),
                        cls="time-inputs"
                    ),
                    Div(
                        Button("Cancel", type="button", id="cancel-button"),
                        Button("Save", type="submit", id="save-button"),
                        Button("Delete", type="button", id="delete-button", 
                               hx_delete=f"/del_event/{event_id}",
                               hx_target="#calendar-container",
                               hx_swap="innerHTML"),
                        cls="form-buttons"
                    ),
                    cls="event-form",
                    id="edit-event-form",
                    hx_put=f"/update_event/{event_id}",
                    hx_target="#calendar-container",
                    hx_swap="innerHTML"
                ),
                cls="modal-content"
            ),
            cls="modal active",
            id="modal-content"
        )
    else:
        return JSONResponse({"status": "error", "message": f"Event {event_id} not found"}, status_code=404)


@rt('/update_event/{event_id}')
def put(auth, event_id: int, title: str = Form(...), description: str = Form(None), start_time: str = Form(...), end_time: str = Form(...), date: str = Form(...)):
    try:
        print(f"Updating event {event_id}: date={date}, start_time={start_time}, end_time={end_time}, title='{title}', description='{description}'")
        events.update({'user_id': auth, 'date': date, 'start_time': start_time, 'end_time': end_time, 'title': title, 'description': description}, event_id)

        # Fetch the updated week data
        event_date = datetime.strptime(date, "%Y-%m-%d").date()
        today = datetime.now().date()
        week_offset = (event_date.isocalendar()[1] - today.isocalendar()[1])
        week_dates = get_week_dates(week_offset)
        week_events = []
        for day in week_dates:
            day_events = filter_events(auth, day.strftime("%Y-%m-%d"))
            week_events.extend(day_events)
        
        # Create toggle and calendar grid
        toggle = create_toggle(event_date.year, week_offset)
        calendar_grid = create_calendar_grid(week_dates, week_events)
        
        # Return the updated calendar container with toggle and grid
        return Div(
            toggle,
            calendar_grid,
            Script("document.getElementById('modal-content').classList.remove('active');"),
            id="calendar-container"
        )
    except Exception as e:
        print(f"Error in put: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

@rt("/del_event/{event_id}")
def delete(auth, event_id: int, session):
    # Retrieve the event details before deletion
    event = events.get(event_id)
    if event:
        event_name = event.title
        event_date_str = event.date
        # print(f"event_date: {event_date}")
        # Delete the event from the database
        events.delete(event_id)
        add_toast(session, f"Event '{event_name}' on {event_date_str} was deleted.", "warning")
        # Return the updated calendar grid
        week_offset = 0  # You may need to calculate this based on the deleted event's date
        week_dates = get_week_dates(week_offset)
        week_events = []
        for day in week_dates:
            day_events = filter_events(auth, day.strftime("%Y-%m-%d"))
            week_events.extend(day_events)

         # Parse the date string into a datetime object
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")  # Adjust the format if necessary
        toggle = create_toggle(event_date.year, week_offset)
        calendar_grid = create_calendar_grid(week_dates, week_events)
        return Div(
            toggle,
            calendar_grid,
            id="calendar-container"
        )
    else:
        return JSONResponse({"status": "error", "message": f"Event {event_id} not found"}, status_code=404)


def date_time_now():
    today = datetime.now().date()
    time = datetime.now().time()
    return today.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S")


@app.get('/smartform')
async def smartform():
    return Div(
        Div(
            H3("What can I do for you?", cls="form-title"),
            Form(
                Textarea(type="text", name="title", placeholder="Smart Request", required=True),
                Div(
                    Button("Cancel", type="button", id="cancel-button"),
                    Button("Send", type="submit", cls="request-confirm"),
                    cls="form-buttons"
                ),
                cls="event-form",
                id="smart-request-form",
                hx_post="/smartrequest",
                hx_indicator="#spinner",
                hx_target="#modal-content",
                hx_swap="innerHTML"
            ),
            Div(Img(src="static/loading.svg", id="spinner", cls="htmx-indicator")),
            cls="modal-content"
        ),
        cls="modal active",
        id="modal-content"
    )
        



def filter_events_day_or_days(auth, date: str, end_date: Optional[str] = None) -> List[Dict]:
    def is_valid_date(d: Optional[str]) -> bool:
        if not d:
            return False
        try:
            datetime.strptime(d, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    items = [o for o in events() if o.user_id == auth]
    filtered_items = []

    for item in items:
        if not is_valid_date(item.date):
            continue
        
        if end_date and is_valid_date(end_date):
            if date <= item.date <= end_date:
                filtered_items.append(item)
        elif item.date == date:
            filtered_items.append(item)

    event_list = []
    for item in filtered_items:
        if item.start_time and item.end_time:
            event_dict = {
                "id": item.id,
                "date": item.date,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "title": item.title if item.title else "No Title",
                "description": item.description
            }
            event_list.append(event_dict)

    return event_list

# Wrapper functions for CRUD operations
@rt
def add_new_event(auth, date: str, title: str, description: str, start_time: str, end_time: str):
    try:
        new_event = dict(user_id=auth, date=date, start_time=start_time, end_time=end_time, 
                         title=title, description=description)
        inserted_event = events.insert(new_event)
        print(f"Event added: {inserted_event}")
        # Trigger UI refresh without returning the result
        update_calendar_view(auth, date)
        # Return a concise message with event details for the LLM
        return f"Success: Event '{title}' added on {date} from {start_time} to {end_time}"
    except Exception as e:
        print(f"Error adding event: {str(e)}")
        return f"Failure: Could not add event '{title}' on {date}. Error: {str(e)}"
    
@rt
def update_existing_event(auth, event_id: int, date: str, title: str, description: str, start_time: str, end_time: str):
    try:
        events.update({'user_id':auth, 'date': date, 'start_time': start_time, 'end_time': end_time, 
                       'title': title, 'description': description}, event_id)
        print(f"Event {event_id} updated successfully")
        # Trigger UI refresh without returning the result
        update_calendar_view(auth, date)
        # Return a concise message with event details for the LLM
        return f"Success: Event '{title}' updated on {date} from {start_time} to {end_time}"
    except Exception as e:
        print(f"Error updating event: {str(e)}")
        return f"Failure: Could not update event '{title}' on {date}. Error: {str(e)}"
    
@rt
def delete_event(auth, event_id: int):
    try:
        event = events.get(event_id)
        if event:
            date = event.date
            title = event.title
            events.delete(event_id)
            print(f"Event {event_id} deleted successfully")
            # Trigger UI refresh without returning the result
            update_calendar_view(auth, date)
            # Return a concise message with event details for the LLM
            return f"Success: Event '{title}' deleted from {date}"
        else:
            return f"Failure: Event {event_id} not found"
    except Exception as e:
        print(f"Error deleting event: {str(e)}")
        return f"Failure: Could not delete event {event_id}. Error: {str(e)}"

@rt
def modify_many_date_events(auth, dates, action: str, **kwargs):
    results = []
    for date in dates:
        if action == "create":
            result = add_new_event(
                user_id = auth,
                date=date,
                title=kwargs.get('title'),
                description=kwargs.get('description'),
                start_time=kwargs.get('start_time'),
                end_time=kwargs.get('end_time')
            )
        elif action == "update":
            event_id = kwargs.get('event_id')
            result = update_existing_event(
                event_id=event_id,
                date=date,
                title=kwargs.get('title'),
                description=kwargs.get('description'),
                start_time=kwargs.get('start_time'),
                end_time=kwargs.get('end_time')
            )
        elif action == "delete":
            event_id = kwargs.get('event_id')
            result = delete_event(event_id)
        else:
            result = f"Invalid action: {action}"
        results.append(result)
    return f"Results: {'; '.join(results)}"

@rt
def update_calendar_view(auth, date):
    event_date = datetime.strptime(date, "%Y-%m-%d").date()
    today = datetime.now().date()
    week_offset = (event_date.isocalendar()[1] - today.isocalendar()[1])
    week_dates = get_week_dates(week_offset)
    week_events = []
    for day in week_dates:
        day_events = filter_events(auth, day.strftime("%Y-%m-%d"))
        week_events.extend(day_events)
    return create_calendar_grid(week_dates, week_events)



def get_weekday_dates(weekdays, end_date_str, start_date_str=None):
    # Convert weekday names to corresponding integers
    weekday_dict = {day.lower(): index for index, day in enumerate(calendar.day_name)}
    weekday_indices = [weekday_dict[day.lower()] for day in weekdays]

    # Parse the end date
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    # Parse the start date or use today's date if not provided
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = date.today()

    # Initialize a list to store the dates
    result_dates = []

    # Iterate through the dates from start to end
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in weekday_indices:
            result_dates.append(current_date)
        current_date += timedelta(days=1)

    return result_dates



# Create FunctionTools for these wrapper functions
date_time_now_tool = FunctionTool.from_defaults(fn=date_time_now)
weekday_dates_lookup_tool = FunctionTool.from_defaults(fn=get_weekday_dates)
filter_events_tool = FunctionTool.from_defaults(fn=filter_events_day_or_days)
add_event_tool = FunctionTool.from_defaults(fn=add_new_event)
modify_many_date_events_tool = FunctionTool.from_defaults(fn=modify_many_date_events)
update_event_tool = FunctionTool.from_defaults(fn=update_existing_event)
delete_event_tool = FunctionTool.from_defaults(fn=delete_event)

# Synchronous blocking function
def blocking_interact_with_llm(agent, modified_prompt, title):
    return agent.chat(modified_prompt.format(title=title))

# Async function that calls the blocking function using run_in_executor
async def async_interact_with_llm(agent, modified_prompt, title):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, blocking_interact_with_llm, agent, modified_prompt, title)
    return response


@rt('/smartrequest')
async def post(auth, title: str = Form(...)):
    print(f"Smart request: {title}")
    
    # Create the OpenAI instance with system instructions
    llm = OpenAI(
        model="gpt-4o-2024-08-06",
    )
    with open('lessprompt.txt', 'r') as file:
        prompt_instructions = file.read()
    modified_prompt = prompt_instructions + f"\nThe current user's auth value is: {str(auth)}. Always use this 'EXACT' auth value as a python string when calling tools that require it."
    # print(f"Auth on smart {auth}")
    print(f"modified prompt last {modified_prompt[-30:]}")

    agent = OpenAIAgent.from_tools(
        [filter_events_tool, date_time_now_tool, 
         add_event_tool, update_event_tool, delete_event_tool], 
        llm=llm, 
        verbose=True,
        prompt_template=modified_prompt
    )
    # llm2 = Groq(model="llama3-70b-8192", api_key=GROQ_API_KEY

    # agent2 = ReActAgent.from_tools(
    #     tools=[
    #         date_time_now_tool,
    #         filter_events_tool,
    #         date_time_now_tool,
    #         add_event_tool,
    #         modify_many_date_events_tool,
    #         update_event_tool,
    #         delete_event_tool
    #     ],
    #     llm=llm2,
    #     verbose=True,
    #     react_chat_prompt=prompt_instructions
    # )

    # response = agent.chat(modified_prompt.format(title=title))
    response = await async_interact_with_llm(agent, modified_prompt, title)

    # Check if any write operations were performed
    write_tools = [add_event_tool, update_event_tool, delete_event_tool]
    write_performed = any(str(tool) in str(response) for tool in write_tools)
    
    # Prepare the response content
    response_content = Div(
        H3("Smart Request", cls="form-title"),
        P(str(response)),
        Button("Close", type="button", id="cancel-button", hx_get="/smartform", hx_target="#modal-content", hx_swap="innerHTML"),
        cls="modal-content"
    )

    # If a write operation was performed, include a script to refresh the calendar
    if write_performed:
        refresh_script = Script("""
            htmx.ajax('GET', '/refresh_calendar', {target:'#calendar-container', swap:'innerHTML'});
        """)

    return Div(
        response_content,
        cls="modal active",
        id="modal-content"
    )


# Add a new route to refresh the calendar
@rt('/refresh_calendar')
def refresh_calendar(auth):
    today = datetime.now().date()
    week_dates = get_week_dates(0)  # Get current week
    week_events = []
    for day in week_dates:
        day_events = filter_events(auth, day.strftime("%Y-%m-%d"))
        week_events.extend(day_events)
    return create_calendar_grid(week_dates, week_events)

@app.get('/login')
def login():
    return Div(
        H3("Welcome to Your Smart Calendar", style="text-align: center; margin-bottom: 20px;"),
        P(A('Login with Google', 
            href=client.login_link(redirect_uri=GOOGLE_REDIRECT_URI),
            cls="login-goggle",
            style="display: block; text-align: center; padding: 10px 20px; text-decoration: none;"
        ),
        style="text-align: center;"),
        cls="login-container",
        style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh;"
    )

@app.get('/logout')
def logout(session):
    session.pop('user_id', None)
    return RedirectResponse('/login', status_code=303)

@app.get('/auth_redirect')
def auth_redirect(code: str, session):
    if not code:
        return "No code provided!"
    try:
        user_id = client.retr_id(code, redirect_uri=GOOGLE_REDIRECT_URI)  # Remove 'await' if this is not an async method
        session['user_id'] = str(user_id)
        if user_id not in events:
            events.insert(user_id=str(user_id))
        return RedirectResponse('/', status_code=303)
    except Exception as e:
        print(f"OAuth error: {str(e)}")
        return RedirectResponse('/login', status_code=303)

serve()
