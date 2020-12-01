import mechanicalsoup
from re import match, findall, sub


class Scraper:
    def __init__(self, username, db):
        self.db = db

        useragent = 'Mozilla/5.0 (X11; U; Linux i686; en-US) ' \
                    'AppleWebKit/534.3 (KHTML, like Gecko) ' \
                    'Chrome/6.0.472.63 Safari/534.3'
        self.header = {
            'User-Agent': useragent
        }
        self.data = {
            "session[username_or_email]": username,
            "session[password]": "",
            "scribe_log": "",
            "redirect_after_login": "/",
            "remember_me": "1"
        }
        self.browser = mechanicalsoup.StatefulBrowser()

        self.base_url = burl = "https://mobile.twitter.com"
        self.ext_urls = {
            'login': f"{burl}/login",
            'session': "/sessions",
            'profile': f"/{username}",
            'followers': f"/{username}/followers",
            'following': f"/{username}/following",
            'notifications': "/notifications",
            'mentions': "/notifications/mentions"
        }


        self.username = username



    def login(self, password):
        """
        Open Login Page, Select login/sessions form, insert creds, and submit login.
        """
        self.browser.open(self.ext_urls['login'], headers=self.header)
        self.browser.select_form(f'form[action="{self.ext_urls["session"]}"]')

        # Print input form
        self.browser.get_current_form().print_summary()

        # Insert User & Pass, then Submit
        self.browser["session[username_or_email]"] = self.username
        self.browser["session[password]"] = password
        response = self.browser.submit_selected()

        try:
            self.goto_profile()
            self.db.insert_login_activity(self.username, True)
        except mechanicalsoup.utils.LinkNotFoundError:
            self.db.insert_login_activity(self.username, False)

    def goto_profile(self):
        """
        Access the User's profile.
        """
        self.browser.open(self.base_url + self.ext_urls['profile'], headers=self.header)
        self.browser.follow_link(self.ext_urls['profile'])
        self.print_current_loc()

    def goto_mentions(self, process_mentions=False):
        """
        Access the User's profile.
        """
        #self.browser.open(self.base_url + self.ext_urls['notifications'], headers=self.header)
        self.browser.follow_link('/i/connect')
        self.print_current_loc()

        process_mentions and self.identify_mentions()

    def identify_mentions(self):
        """
        Identify the mentions from users directed at the bot.
        """
        def __parse_html_for_mentions(__page_data):
            regex = r"\<table class=\"tweet\"(.*?)\<\/table"
            return findall(regex, repr(__page_data))

        mentions = []

        mentions_page_data = str(self.browser.get_current_page())
        notifications_data = __parse_html_for_mentions(mentions_page_data)

        for notification in notifications_data:
            tweet = Tweet(notification, self.db)

            if tweet.contains_mention:
                mentions.append(tweet)

                if tweet.is_new:
                    self.db.insert_notification(tweet)

        for mention in mentions:
            self.process_mention(mention)

        # self.print_current_page()
        # self.browser.find_link(mentions[0].reply_url)

    def process_mention(self, tweet):
        """
        Executes the commands according to the command found
        :param tweet:
        :return:
        """

        command_response = {
            'invalid': [
                self.reply_to_mention,
                "Invalid Command Detected:\n\nTweet \"Help\" "
                "for available commands."
                ],
            'help': [
                self.reply_to_mention,
                "Available Commands:\n"
                "   1. Find Frens - Fren Request is retweeted\n"
                "   2. RIP - Banned Acc notice is retweeted"
                ],
            'findfrens': [
                self.retweet_mention,
                None
            ],
            'rip': [
                self.retweet_mention,
                None
            ],
        }

        command_response[tweet.command_found][0](
            tweet,
            command_response[tweet.command_found][1]
        )
        self.db.update_notification_is_done(tweet.id)

    def reply_to_mention(self, tweet, response):
        form_identifier = 'form[action="/compose/tweet"]'

        print(f"Attempting to reply to {tweet}")
        print(f"Following Link: {tweet.reply_url}")

        self.browser.follow_link(tweet.reply_url)
        self.print_current_loc()
        #self.print_current_page()

        self.browser.select_form(form_identifier)
        self.browser.get_current_form().print_summary()
        self.browser["tweet[text]"] = response
        response = self.browser.submit_selected()
        print(f"Response from form submit: {response}")
        self.goto_mentions()


    def retweet_mention(self, tweet, *args):
        form_identifier = f'form[action="/statuses/{tweet.id}/retweet"]'

        print(f"Attempting to reply to {tweet}")
        print(f"Following Link: {tweet.retweet_url}")

        self.browser.follow_link(tweet.retweet_url)
        self.print_current_loc()
        #self.print_current_page()

        try:
            self.browser.select_form(form_identifier)
            self.browser.get_current_form().print_summary()
            response = self.browser.submit_selected()
            print(f"Response from form submit: {response}")
        except mechanicalsoup.utils.LinkNotFoundError:
            print(f"{tweet.id} from {tweet.sender} has already been retweeted.")
        self.goto_mentions()

    def print_current_loc(self):
        print(f"------------------------------------------------------")
        print(self.browser.get_url())
        print(f"------------------------------------------------------")

    def print_current_page(self):
        print(f"------------------------------------------------------")
        print(self.browser.get_current_page())
        print(f"------------------------------------------------------")


class Tweet:

    id = None
    sender = None
    timestamp = None
    text = None
    extras = []
    contains_mention = None
    is_queued = None
    is_new = None
    command_found = None
    retweet_url = None
    reply_url = None

    def __init__(self, data, db):
        raw_header = self.__parse_for_header(data)
        self.db = db
        self.id = self.__parse_for_id(raw_header)

        in_db, is_queued = db.query_notification_for_tweet_id(self.id)

        if in_db:
            is_queued and self.get_tweet_attributes(
                raw_header, data
            )
        else:
            self.get_tweet_attributes(
                raw_header, data, is_new=True
            )
        # self.__parse_raw_tweet_data()

    def __str__(self):
        return f"{self.id},{self.sender},{self.timestamp},\n{self.text}"

    def get_tweet_attributes(self, raw_header, data, is_new=False):
        self.sender = self.__parse_for_sender(raw_header)
        self.timestamp = self.__parse_for_timestamp(data)
        self.text, self.extras, self.contains_mention = self.__parse_for_text(data)
        self.is_queued = True
        self.command_found = self.__search_for_cmd_in_text(
            self.text, self.extras
        )
        self.retweet_url = f"/statuses/{self.id}/retweet\?p=t"
        self.reply_url = f"/{self.sender}/reply/{self.id}\?p=r"
        self.is_new = is_new

    @classmethod
    def __parse_for_header(cls, data):
        regex = [r"href=\"(.*?)\?p\=v\""]
        return cls.__parse_data(regex, data)

    @classmethod
    def __parse_for_id(cls, header_data):
        header_segments = header_data.split('/')
        return header_segments[3]

    @classmethod
    def __parse_for_sender(cls, header_data):
        header_segments = header_data.split('/')
        return header_segments[1]

    @classmethod
    def __parse_for_timestamp(cls, data):
        regex = [
            r'\<td class=\"timestamp\"\>(.*?)\<\/td\>',
            r'\>(.*?)\<\/a\>',
        ]
        return cls.__parse_data(regex, data)

    @classmethod
    def __parse_for_text(cls, data):
        raw_text = None
        text = None
        raw_extras = []
        extras = None
        contains_mention = False

        regex_raw_text = [
            r'\<div class=\"tweet\-text\"(.*a class=\"twitter\-atreply dir\-ltr\".*\<\/div\>.*?)\<\/div\>',
            r'\<\/a\>(.*?)\<\/div\>'
        ]
        regex_text = r'\<a class=\"twitter.*'

        regex_raw_extras = [
            r'\<a class=\"twitter.?(.*?)\<\/a\>'
        ]

        try:
            raw_text = cls.__parse_data(regex_raw_text, data)
            contains_mention = True
            print(raw_text)
        except IndexError:
            return text, extras, contains_mention

        text = cls.__slice_data(regex_text, raw_text)

        raw_extras = cls.__parse_data(regex_raw_extras, raw_text, return_list=True)
        len(raw_extras) > 0 and [print(e + '\n') for e in raw_extras]

        return text, extras, contains_mention

    @staticmethod
    def __search_for_cmd_in_text(text, extras):
        """
        Searches for valid command within tweet's text.

        Available Commands
            #. Help - Display available commands

            #. Find Frens - Broadcast "Help me find my frens"

            #. RIP - Broadcast "Fren has been suspended/banned"


        :param text: string found within tweet.
        :type text: str
        :param extras: extra links/media within tweet.
        :type extras: dict
        :return:
        """
        def _find_text_in_cmd_pos():
            max_init_words_to_find = 2

            raw_text = sub(
                r'^[ \n\:\,\'\"\(\)\[\]\{\}\;\?\!\=]*([a-zA-Z].*$)',
                r'\1',
                sub(r'\n|\\n', ' ', text)
            )
            print(f"ORI Text: {text}")
            print(f"RAW Text:{raw_text}")

            command_text = raw_text.lower().split(' ')[
                           0:max_init_words_to_find
                           ]

            return command_text[0] \
                if len(command_text) == 1 \
                else f"{command_text[0]}{command_text[1]}"

        def _determine_command():
            command_text = _find_text_in_cmd_pos()
            print(f"Initial Words Found: {command_text}")

            for cmd_id, command in enumerate(available_commands):

                if match(command + r'.*', command_text):
                    return cmd_id
                print(f"txt({command_text})!=({command})")
            else:
                return 0

        available_commands = [
            'invalid',
            'help',
            'findfrens',
            'rip',
        ]
        try:
            command_found = available_commands[_determine_command()]
        except TypeError:
            print(f"!!!!! ERROR {text}")
            command_found = available_commands[0]

        print(f"COMMAND FOUND: {command_found}")

        return command_found

    @staticmethod
    def __slice_data(regex, data):
        return sub(regex, '', data)

    @staticmethod
    def __parse_data(regex_list, data, return_list=False):
        num_of_steps = len(regex_list)
        is_multistep = False if num_of_steps == 1 else True
        tmp_result = str()
        result = []

        for index, regex in enumerate(regex_list):
            if is_multistep and index == 0:
                tmp_result = findall(regex, data)[0]
            elif is_multistep:
                result = findall(regex, tmp_result)
            else:
                result = findall(regex, data)

        return result if return_list else result[0]