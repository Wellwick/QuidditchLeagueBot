import poplib
from email import parser
from email.header import decode_header
from email.utils import parseaddr
import json

class Email():
    def __init__(self):
        SERVER = "pop.gmail.com"
        with open("email.json", "r") as email_file:
            email_data = json.load(email_file)

        # connect to server
        print('connecting to ' + SERVER)
        self.pop_conn = poplib.POP3_SSL(SERVER)

        # login
        print('logging in')
        self.pop_conn.user(email_data["USER"])
        self.pop_conn.pass_(email_data["PASSWORD"])

        with open("email-info.json", "r") as email_info_file:
            self.info = json.load(email_info_file)
        
        if not "count" in self.info:
            self.info["count"] = len(self.pop_conn.list()[1])

    def get_latest(self):
        """
            Checks how many emails have been received since the last check and,
            if there are new ones, packed up the info of fic id and link.
        """
        latest_emails = []
        email_count = len(self.pop_conn.list()[1])
        if self.info["count"] == email_count:
            return latest_emails
        
        # If we've got to this point, we need to read some emails.
        # They might not be from fanfiction.net though
        messages = [pop_conn.retr(i) for i in range(self.info["count"], email_count + 1)]
        n_messages = []
        for message in messages:
            new = [mssg.decode("utf-8") for mssg in message[1]]
            n_messages += [new]

        messages = n_messages
        # Concat message pieces:
        messages = ["\n".join(mssg) for mssg in messages]
        #Parse message intom an email object:
        messages = [parser.Parser().parsestr(mssg) for mssg in messages]
        for message in messages:
            if "Chapter:" in message['subject'] or "Story:" in message['subject']:
                # Should also make sure it's from the bot, but not for now
                # Get the fanfiction page address
                #text = str(message)
                text = self.get_text(message)
                index = text.index("https://www.fanfiction.net/s/")
                text = text[index:]
                index = text.index("\n")
                text = text[:index]
                split = text.split("/")
                storyid = split[4]
                chapter = split[5]
                latest_emails += [ {
                    "id": storyid,
                    "chapter": chapter
                }]
        self.info["count"] = email_count
        # This is not the end of the work, but it is all that will be done in
        # this class. The parsing of the information will have to be done
        # elsewhere!
        return latest_emails

    # The next three methods are shamelessly stolen from 
    # https://www.code-learner.com/python-use-pop3-to-read-email-example/
    # Praise the real heroes

    # check email content string encoding charset.
    def guess_charset(self, msg):
        # get charset from message object.
        charset = msg.get_charset()
        # if can not get charset
        if charset is None:
            # get message header content-type value and retrieve the charset from the value.
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
        return charset

    # The Subject of the message or the name contained in the Email is encoded string
    # , which must decode for it to display properly, this function just provide the feature.
    def decode_str(self, s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value

    # variable indent_number is used to decide number of indent of each level in the mail multiple bory part.
    def get_text(self, msg, indent_number=0):
        if indent_number == 0:
            # loop to retrieve from, to, subject from email header.
            for header in ['From', 'To', 'Subject']:
                # get header value
                value = msg.get(header, '')
                if value:
                    # for subject header.
                    if header=='Subject':
                        # decode the subject value
                        value = self.decode_str(value)
                    # for from and to header. 
                    else:
                        # parse email address
                        hdr, addr = parseaddr(value)
                        # decode the name value.
                        name = self.decode_str(hdr)
                        value = u'%s <%s>' % (name, addr)
                #print('%s%s: %s' % (' ' * indent_number, header, value))
        # if message has multiple part. 
        if (msg.is_multipart()):
            # get multiple parts from message body.
            parts = msg.get_payload()
            # loop for each part
            for n, part in enumerate(parts):
                #print('%spart %s' % (' ' * indent_number, n))
                #print('%s--------------------' % (' ' * indent_number))
                # print multiple part information by invoke print_info function recursively.
                print_info(part, indent + 1)
        # if not multiple part. 
        else:
            # get message content mime type
            content_type = msg.get_content_type() 
            # if plain text or html content type.
            if content_type=='text/plain' or content_type=='text/html':
                # get email content
                content = msg.get_payload(decode=True)
                # get content string charset
                charset = self.guess_charset(msg)
                # decode the content with charset if provided.
                if charset:
                    content = content.decode(charset)
                return content
                #print('%sText: %s' % (' ' * indent_number, content + '...'))
            else:
                pass
                #print('%sAttachment: %s' % (' ' * indent_number, content_type))

            
