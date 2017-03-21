from __future__ import print_function
from __future__ import unicode_literals

from rtmbot.core import Plugin
from rtmbot.core import logging as logging

import re
import time
import config
import json
import cPickle as pickle


class ThreaderPlugin(Plugin):

    def __init__(self, name=None, slack_client=None, plugin_config=None):
        Plugin.__init__(self, name, slack_client, plugin_config)
        self.regex = re.compile(config.SEARCH_REGEX, re.IGNORECASE)
        self.threads = dict()
        try:
            with open(config.PICKLE_FILE, 'rb') as handle:
                self.threads = pickle.load(handle)
        except Exception as e:
            logging.error("Cloud not load pickle file at location %s" % config.PICKLE_FILE)

        # Find bot id for later
        auth = self.slack_client.api_call(
            "auth.test"
        )
        logging.debug("Auth info: %s" % auth)
        self.user = auth['user_id']

    def catch_all(self, data):
        logging.debug("Entered catch_all() with: %s" % data)

    def process_message(self, data):
        logging.debug("Entered process_message() with: %s" % data)
        # Make sure we can test type
        if 'subtype' not in data:
            logging.debug("I can't find subtype in data")
            return

        if data['subtype'] != 'bot_message':
            logging.debug("This is the wrong type of message for me to deal with")
            return

        # Ignore messages from this bot
        if data['bot_id'] == config.BOT_ID:
            logging.debug("Ignoring message from ourselves")
            return

        m = self.regex.search(json.dumps(data))

        # Force thread_key to None if search key is not found so that we post the message without threading it
        if m is None:
            thread_key = None
            logging.debug("Search string not found")
        else:
            thread_key = m.group(0)
            logging.debug("Thread key found: %s" % thread_key)

        if thread_key in self.threads:
            # Repost the message to the thread
            res = self.slack_client.api_call(
                "chat.postMessage",
                channel=config.POST_CHANNEL,
                text=data['text'],
                attachments=data['attachments'],
                thread_ts=self.threads[thread_key]['ts'],
                reply_broadcast=self.threads[thread_key]['updated'] < time.time() - config.BROADCAST_AFTER_SECONDS  # broadcast if updated over 60 seconds ago
                # icon_url=user['bot']['icons']['image_48'],
                # username=user['bot']['name']
            )
            logging.debug("Just posted a threaded message, got the response: %s" % res)

            # Update timestamp for broadcasting decision
            self.threads[thread_key]['updated'] = time.time()
        else:
            res = self.slack_client.api_call(
                "chat.postMessage",
                channel=config.POST_CHANNEL,
                text=data['text'],
                attachments=data['attachments']
                # icon_url=user['bot']['icons']['image_48'],
                # username=user['bot']['name']
            )
            logging.debug("Just posted a root message, got the response: %s" % res)

            if thread_key is not None:  # Don't set None as a key, else we will try to thread the next message without search_key
                self.threads[thread_key] = {'ts': res['ts'], 'updated': time.time()}

        try:
            with open(config.PICKLE_FILE, 'wb') as handle:
                pickle.dump(self.threads, handle, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            logging.error("Cloud not load pickle file at location %s" % config.PICKLE_FILE)
