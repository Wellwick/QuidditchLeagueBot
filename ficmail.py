import os, pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import email
import base64
import json
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
import asyncio

class FicMail():
    def __init__(self):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        # This is just "id/chapter"
        with open("tracked-stories.json", "r") as tracked:
            self.tracked = json.load(tracked)

        self.gmail = build('gmail', 'v1', credentials=creds)
        request = {
            'labelIds': ['INBOX'],
            'topicName': 'projects/ultimate-realm-178810/topics/gmail'
        }
        # This following line will make the unacked message count rise!
        results = self.refresh_watch()
        if "historyId" not in self.tracked:
            self.tracked["historyId"] = results["historyId"]

    def save_tracked(self):
        with open("tracked-stories.json", "w") as tracked:
            json.dump(self.tracked, tracked)

    def add_story(self, s_list, id, chapter):
        new_id = str(id) + "/" + str(chapter)
        if new_id in self.tracked["data"]:
            # We have already done this one before!
            return s_list
        
        # We don't save tracked here because we know that this will happen just
        # before things are sent off!
        self.tracked["data"] += [new_id]
        
        # Not encountered duplicate, send it off!
        s_list += [{
            "id": id,
            "chapter": chapter
        }]
        return s_list

    def refresh_watch(self):
        return self.gmail.users().watch(userId='me', body=request).execute()

    def get_latest(self):
        """
            Checks how many emails have been received since the last check and,
            if there are new ones, packed up the info of fic id and link.
        """
        new_stories = []
        history = self.gmail.users().history().list(userId='me', startHistoryId=self.tracked["historyId"]).execute()
        if "history" not in history:
            # This means there is no emails to process!
            # We aren't going to be acknowledging any stoppages of the service,
            # but who really cares? They aren't real and should only happen
            # on expiry, which should only happen if the bot shuts down
            self.tracked["history"] = history["historyId"]
            return new_stories
        
        # If we've got to this point, we need to read some emails.
        # They might not be from fanfiction.net, but we can get the text from
        # them and if it contains www.fanfiction.net/s/, we can assume it's for
        # a story post!
        print("Have some new emails!")
        for i in history["history"]:
            for j in i["messages"]:
                message = self.gmail.users().messages().get(userId='me', id=j['id'], format="raw").execute()
                msg_str = base64.urlsafe_b64decode(message['raw'].encode("ASCII")).decode("ASCII")
                mime_msg = email.message_from_string(msg_str)
                text = mime_msg.as_string()
                text = text.split("\n")
                for line in text:
                    if "://www.fanfiction.net/s/" not in line:
                        continue
                    split = line.strip().split("/")
                    storyid = split[4]
                    if len(split) > 5:
                        chapter = split[5]
                    else:
                        # In only one occurance, it can for some reason not include a chapter
                        "chapter = 1"
                    try:
                        int(chapter.strip())
                    except:
                        chapter = "1"
                    new_stories = self.add_story(new_stories, storyid, chapter)
                    # We shouldn't have more than one link in an email
                    break
        
        # This is not the end of the work, but it is all that will be done in
        # this class. The parsing of the information will have to be done
        # elsewhere!
        self.tracked["history"] = history["historyId"]
        self.save_tracked()
        self.ack_messages()
        return new_stories

    def callback(self, message):
        message.ack()

    def ack_messages(self):
        self.tracked["project-id"]
        self.tracked["subscription-id"]
        self.tracked["timeout"]
        print("Building a subscriber client to acknowledge messages")
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(self.tracked["project-id"], self.tracked["subscription-id"])

        streaming_pull_future = subscriber.subscribe(subscription_path, callback=self.callback)
        print(f"Listening for messages on {subscription_path} for " + str(self.tracked["timeout"]) + "seconds...\n")
        with subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                streaming_pull_future.result(timeout=timeout)
            except TimeoutError:
                streaming_pull_future.cancel()

        print("Messages acknowledged!")

    async def refresh_watch_loop(self):
        while True:
            # The watch subscription expires after 7 days, so we can safely wait
            # for 5 days and refresh
            await asyncio.sleep(60*60*24*5)
            self.refresh_watch()
            
