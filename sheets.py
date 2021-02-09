import pickle, os.path, datetime, random, difflib
from googleapiclient.discovery import build
from google.oauth2 import service_account as s_a

SECRET = os.path.join(os.getcwd(), "gsecret.json")
SCOPES = ['https://www.googleapis.com/auth/drive']

c = s_a.Credentials.from_service_account_file(SECRET, scopes=SCOPES)

service = build('sheets', 'v4', credentials=c)
drive_service = build('drive', 'v3', credentials=c)

#  - - - - Stuff specific to each google sheet below here