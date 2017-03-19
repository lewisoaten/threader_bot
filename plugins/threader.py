from __future__ import print_function
from __future__ import unicode_literals

from rtmbot.core import Plugin
from rtmbot.core import logging as logging

import re
import time
import config
import json


class ThreaderPlugin(Plugin):

    def __init__(self, name=None, slack_client=None, plugin_config=None):
        Plugin.__init__(self, name, slack_client, plugin_config)
        self.regex = re.compile(config.SEARCH_REGEX, re.IGNORECASE)
        self.threads = dict()

        # Find bot id for later
        auth = self.slack_client.api_call(
            "auth.test"
        )
        logging.debug("Auth info: %s" % auth)
        self.user = auth['user_id']

        # Find our posting channel in channel list and store id for later
        channels = self.slack_client.api_call(
            "channels.list"
        )
        for channel in channels['channels']:
            if channel['name'] == config.POST_CHANNEL:
                self.channel = channel['id']
        if self.channel is None:
            logging.error('Can\'t find channel: %s' % config.POST_CHANNEL)

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

        # Stop function if no search key found
        if m is None:
            logging.debug("Search string not found")
            return

        thread_key = m.group(0)
        logging.debug("Thread key found: %s" % thread_key)

        # Get the poster user info
        # user = self.slack_client.api_call(
        #     "bots.info",
        #     user=data['bot_id']
        # )
        # logging.debug("Found user data: %s" % user)

        if thread_key in self.threads:
            # Repost the message to the thread
            res = self.slack_client.api_call(
                "chat.postMessage",
                channel=self.channel,
                text=data['text'],
                attachments=data['attachments'],
                thread_ts=self.threads[thread_key]['ts'],
                reply_broadcast=self.threads[thread_key]['updated'] < time.time() - config.BROADCAST_AFTER_SECONDS  # broadcast if updated over 60 seconds ago
                # icon_url=user['bot']['icons']['image_48'],
                # username=user['bot']['name']
            )
            logging.debug(res)

            # Update timestamp for broadcasting decision
            self.threads[thread_key]['updated'] = time.time()
        else:
            res = self.slack_client.api_call(
                "chat.postMessage",
                channel=self.channel,
                text=data['text'],
                attachments=data['attachments']
                # icon_url=user['bot']['icons']['image_48'],
                # username=user['bot']['name']
            )
            logging.debug(res)
            self.threads[thread_key] = {'ts': res['ts'], 'updated': time.time()}
