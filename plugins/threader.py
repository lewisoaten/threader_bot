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

        # Setup the defaults with our bot id and bot alias data in config
        username = config.BOT_ALIAS[config.BOT_ID]['username']
        icon_url = config.BOT_ALIAS[config.BOT_ID]['icon_url']

        # Ignore messages from this bot
        if data['bot_id'] == config.BOT_ID:
            logging.debug("Ignoring message from ourselves")
            return
        elif data['bot_id'] in config.BOT_ALIAS:  # For other bots, assign an alias if we have one configured
            username = config.BOT_ALIAS[data['bot_id']]['username']
            icon_url = config.BOT_ALIAS[data['bot_id']]['icon_url']

        # Find all the matches we can and produce a non-duplicated dict of them
        it = self.regex.finditer(json.dumps(data))
        search_keys = {match.group(0): None for match in it}

        # Find the intersection of self.threads and search_keys and update the search_keys with thread info
        for intersection_key in search_keys.viewkeys() & self.threads.viewkeys():
            search_keys[intersection_key] = self.threads[intersection_key]

        # Now loop over all search keys, whether they have thread data or None
        for thread_key, thread_id in search_keys.iteritems():
            logging.debug("Thread key found: %s with thread id: %s, last updated: %s" % thread_key, thread_id['ts'], thread_id['updated'])

            if thread_id is None:  # None means that we have not seen this thread_key before so we should post a root message and log the thread_key
                res = self.slack_client.api_call(
                    "chat.postMessage",
                    channel=config.POST_CHANNEL,
                    text=data['text'],
                    attachments=data['attachments'],
                    icon_url=icon_url,
                    username=username
                )
                logging.debug("Just posted a root message, got the response: %s" % res)

                self.threads[thread_key] = {'ts': res['ts'], 'updated': time.time()}
            else:  # We have a thread for this thread_key, so lets post it in there and update the last-post time
                res = self.slack_client.api_call(
                    "chat.postMessage",
                    channel=config.POST_CHANNEL,
                    text=data['text'],
                    attachments=data['attachments'],
                    thread_ts=self.threads[thread_key]['ts'],
                    reply_broadcast=self.threads[thread_key]['updated'] < time.time() - config.BROADCAST_AFTER_SECONDS,  # broadcast if updated over 60 seconds ago
                    icon_url=icon_url,
                    username=username
                )
                logging.debug("Just posted a threaded message, got the response: %s" % res)

                # Update timestamp for broadcasting decision
                self.threads[thread_key]['updated'] = time.time()

        if len(search_keys) = 0:  # This mneans that we were unable to find a search_key, so just re-post to the channel
            res = self.slack_client.api_call(
                "chat.postMessage",
                channel=config.POST_CHANNEL,
                text=data['text'],
                attachments=data['attachments'],
                icon_url=icon_url,
                username=username
            )
            logging.debug("Just posted an unkeyed message, got the response: %s" % res)

        try:
            with open(config.PICKLE_FILE, 'wb') as handle:
                pickle.dump(self.threads, handle, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            logging.error("Cloud not load pickle file at location %s" % config.PICKLE_FILE)
