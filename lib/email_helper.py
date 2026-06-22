import os
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import asyncio
import logging

log = logging.getLogger("friday.email_helper")

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly'
]

CREDENTIALS_PATH = Path(__file__).parent.parent / "data" / "credentials.json"
TOKEN_PATH = Path(__file__).parent.parent / "data" / "token.json"

def _get_gmail_service():
    """Retrieve or build the Gmail API service. Auto-refreshes tokens or boots local auth flow."""
    import os
    if os.getenv("GMAIL_INTEGRATION", "false").lower() not in ("1", "true", "yes"):
        raise ValueError("Gmail integration is disabled in .env")
    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            log.warning(f"Could not load token.json: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                log.warning(f"Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "credentials.json is missing in data/ folder. "
                    "Please set up OAuth credentials on Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


async def get_recent_emails(count: int = 5) -> list[dict]:
    """Read the top N recent emails from the Gmail inbox."""
    def _do():
        service = _get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=count).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', 
                id=msg['id'], 
                format='metadata', 
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            
            label_ids = msg_data.get('labelIds', [])
            email_info = {
                "id": msg['id'], 
                "sender": "Unknown Sender", 
                "subject": "(No Subject)", 
                "date": "", 
                "snippet": msg_data.get('snippet', ''),
                "read": 'UNREAD' not in label_ids
            }
            
            for header in headers:
                name = header.get('name', '')
                val = header.get('value', '')
                if name == 'From':
                    email_info['sender'] = val
                elif name == 'Subject':
                    email_info['subject'] = val
                elif name == 'Date':
                    email_info['date'] = val
                    
            emails.append(email_info)
        return emails

    try:
        return await asyncio.to_thread(_do)
    except Exception as e:
        log.error(f"Failed to get Gmail emails: {e}")
        raise e


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email to a recipient with subject and body."""
    def _do():
        service = _get_gmail_service()
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}
        
        sent_msg = service.users().messages().send(userId='me', body=create_message).execute()
        return sent_msg

    try:
        res = await asyncio.to_thread(_do)
        return {"success": True, "message_id": res.get("id")}
    except Exception as e:
        log.error(f"Failed to send Gmail email: {e}")
        return {"success": False, "error": str(e)}


async def get_todays_calendar_events() -> list[dict]:
    """Retrieve today's events from Google Calendar."""
    import os
    if os.getenv("GMAIL_INTEGRATION", "false").lower() not in ("1", "true", "yes"):
        return []
    def _do():
        try:
            # Reuses the same credentials file/mechanism
            creds = None
            if TOKEN_PATH.exists():
                creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not CREDENTIALS_PATH.exists():
                        return []
                    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
                    
            service = build('calendar', 'v3', credentials=creds)
            
            # Query from start of today to end of today (UTC)
            now = datetime.utcnow()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            items = events_result.get('items', [])
            events = []
            
            for item in items:
                start = item['start'].get('dateTime', item['start'].get('date'))
                all_day = 'dateTime' not in item['start']
                
                # Parse datetime
                if all_day:
                    start_dt = datetime.strptime(start, '%Y-%m-%d')
                    start_str = "All Day"
                else:
                    # e.g., '2026-06-18T14:30:00+05:30'
                    try:
                        clean_start = start.split('+')[0]
                        # Handle '-' timezone offset cases (e.g. 2026-06-18T14:30:00-07:00)
                        if clean_start.count('-') > 2:
                            # It has negative offset
                            clean_start = clean_start.rsplit('-', 1)[0]
                        start_dt = datetime.fromisoformat(clean_start)
                    except Exception:
                        start_dt = datetime.utcnow()
                    start_str = start_dt.strftime('%I:%M %p')
                
                events.append({
                    "title": item.get('summary', '(No Title)'),
                    "all_day": all_day,
                    "start": start_str,
                    "start_dt": start_dt,
                    "calendar": "Primary"
                })
            return events
        except Exception as e:
            log.error(f"Failed to fetch Google Calendar events: {e}")
            return []
            
    try:
        return await asyncio.to_thread(_do)
    except Exception as e:
        log.error(f"Failed to get calendar events: {e}")
        return []


async def get_gmail_unread_count() -> dict:
    """Retrieve the number of unread emails in Gmail."""
    import os
    if os.getenv("GMAIL_INTEGRATION", "false").lower() not in ("1", "true", "yes"):
        return {"total": 0, "accounts": {}}
    def _do():
        service = _get_gmail_service()
        result = service.users().labels().get(userId='me', id='UNREAD').execute()
        unread_count = result.get('messagesUnread', 0)
        return {"total": unread_count, "accounts": {"Gmail": unread_count}}

    try:
        return await asyncio.to_thread(_do)
    except Exception as e:
        log.error(f"Failed to get Gmail unread count: {e}")
        return {"total": 0, "accounts": {}}


async def search_gmail(query: str, count: int = 10) -> list[dict]:
    """Search Gmail messages matching the query string."""
    import os
    if os.getenv("GMAIL_INTEGRATION", "false").lower() not in ("1", "true", "yes"):
        return []
    def _do():
        service = _get_gmail_service()
        results = service.users().messages().list(userId='me', q=query, maxResults=count).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', 
                id=msg['id'], 
                format='metadata', 
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            label_ids = msg_data.get('labelIds', [])
            
            email_info = {
                "id": msg['id'], 
                "sender": "Unknown Sender", 
                "subject": "(No Subject)", 
                "date": "", 
                "snippet": msg_data.get('snippet', ''),
                "read": 'UNREAD' not in label_ids
            }
            
            for header in headers:
                name = header.get('name', '')
                val = header.get('value', '')
                if name == 'From':
                    email_info['sender'] = val
                elif name == 'Subject':
                    email_info['subject'] = val
                elif name == 'Date':
                    email_info['date'] = val
                    
            emails.append(email_info)
        return emails

    try:
        return await asyncio.to_thread(_do)
    except Exception as e:
        log.error(f"Failed to search Gmail: {e}")
        return []
