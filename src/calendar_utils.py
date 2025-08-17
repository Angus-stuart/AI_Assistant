import datetime

def create_event(service, title, start_time, end_time, description=None, timezone="Australia/Sydney"):
    """
    Create a new event in the Google Calendar.
    
    Args:
        service (googleapiclient.discovery.Resource): The Google Calendar service object.
        title (str): The title of the event.
        start_time (str): The start time of the event in ISO format.
        end_time (str): The end time of the event in ISO format.
        description (str, optional): Description of the event.
        timezone (str, optional): Timezone for the event. Defaults to "Australia/Sydney".
        
    Returns:
        dict: The created event details.
    """
    
    event = {
        "summary": title,
        "start": {"dateTime": start_time, "timeZone": timezone},
        "end": {"dateTime": end_time, "timeZone": timezone},
    }
    
    if description:
        event["description"] = description
    
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    
    print(f"Event created: {created_event.get('htmlLink')}")
    return created_event
