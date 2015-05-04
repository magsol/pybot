"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import signal
import time

import tweepy

import PickleStorage

class PyBot(object):

    def __init__(self):
        # Basic configuration and state variables for the bot.
        self.config = {}
        self.state = {}

        # List of custom callbacks that are user-defined.
        self.custom_callbacks = []

        # # # # # # # # # # # # # # # # # # # # # # #
        # Configuration options and their defaults. #
        # # # # # # # # # # # # # # # # # # # # # # #

        # Action intervals. Set any of these to 0 to disable them entirely.
        # Otherwise, the integer indicates the number of seconds between
        # heartbeats. Alternatively, these can be callables that return
        # some number (integer) of seconds.
        self.config['timeline_interval'] = 0
        self.config['mention_interval'] = 0
        self.config['search_interval'] = 0
        self.config['follow_interval'] = 0
        self.config['tweet_interval'] = 0

        # If True, this bot replies ONLY in response to direct mentions.
        self.config['reply_direct_mention_only'] = False

        # If True, this bot issues direct replies ONLY to accounts it follows.
        self.config['reply_followers_only'] = False

        # If True, automatically favorites all direct mentions.
        self.config['autofav_direct_mentions'] = False

        # If the bot detects tweets that contain the listed keywords, those
        # tweets are automatically favorite'd.
        self.config['autofav_keywords'] = []

        # If True, this bot automatically follows any account that follows it.
        self.config['autofollow'] = False

        # Logging level. See https://docs.python.org/2/library/logging.html#logging-levels
        # for more details.
        self.config['logging_level'] = logging.DEBUG

        # Adapter for saving/loading this PyBot's state.
        self.config['storage'] = PickleStorage()

        # Denotes users the bot will never mention.
        self.config['blacklist'] = []

        # Denotes terms that, if encountered, their tweets are ignored.
        self.config['exclude'] = []

        #
        # End configuration options.
        #
        # Now we start initializing the bot.
        #

        # Set up a signal handler so a bot can gracefully exit.
        signal.signal(signal.SIGINT, self._handler)

        # Set up logging.
        logging.basicConfig(format = '%(asctime)s | %(levelname)s: %(message)s',
            datefmt = '%m/%d/%Y %I:%M:%S %p',
            filename = '%s.log' % self.screen_name,
            level = self.config['logging_level'])

        # Required implementation by all subclasses. Produces an error if it
        # is not implemented.
        self.bot_init()

        # Set up OAuth with Twitter and pull down some basic identities.
        logging.info("Authenticating through Twitter OAuth...")
        auth = tweepy.OAuthHandler(self.config['api_key'], self.config['api_secret'])
        auth.set_access_token(self.config['access_key'], self.config['access_secret'])
        self.api = tweepy.API(auth)
        self.id = self.api.me().id
        self.screen_name = self.api.me().screen_name
        logging.info("Authentication complete.")

        # Try to load any previous state.
        logging.info("Setting bot state...")
        self.state = self.config['storage'].read('%s_state.pkl' % self.screen_name)
        if self.state is None:
            # No previous state to load? Initialize everything.
            self.state = {}

            # Wait time for the next action.
            self.state['next_action'] = 0

            # Timeline configuration options. Set timeline_interval to 0 to
            # disable checking the bot's timeline.
            self.state['last_timeline_id'] = 1
            self.state['last_timeline_time'] = 0
            self.state['next_timeline_time'] = 0
            self.state['recent_timeline'] = []

            # Mention configuration options. Set mention_interval to 0 to
            # disable checking the bot's mentions.
            self.state['last_mention_id'] = 1
            self.state['last_mention_time'] = 0
            self.state['next_mention_time'] = 0
            self.state['recent_mentions'] = []

            # Keyword search configuration options. Set search_interval to 0 to
            # disable searching for keywords in the public timeline.
            self.state['last_search_id'] = 1
            self.state['last_search_time'] = 0
            self.state['next_search_time'] = 0

            # Active tweeting configuration. Set tweet_interval to 0 to
            # disable posting otherwise-unprovoked tweets.
            self.state['last_tweet_id'] = 1
            self.state['last_tweet_time'] = 0
            self.state['next_tweet_time'] = 0

            # List of user IDs you follow.
            self.state['friends'] = self.api.friends_ids(self.id)

            # List of user IDs that follow you.
            self.state['followers'] = self.api.followers_ids(self.id)

            # List of new followers since the last check (internal) timestamp.
            self.state['new_followers'] = []
            self.state['last_follow_time'] = time.time()
            self.state['next_follow_time'] = 0

        logging.info("Bot state set.")

    def register_custom_callback(self, action, condition, interval):
        """
        Registers a user-defined callback action. Tests if the given condition
        is True after the specified interval, and if so, performs the action.

        Parameters
        ----------
        action : function
            Function which specifies the custom action to take.
        condition : function
            Function which evaluates to True or False.
        interval : integer or callable
            Number of seconds to wait before checking the condition, or a
            callable that returns the number of seconds to wait.
        """
        callback = {
            'action': action,
            'condition': condition,
            'interval': interval,
            'last_run': 0,
            'next_run': 0,
        }
        self.custom_callbacks.append(callback)

    def on_scheduled_tweet(self):
        raise NotImplementedError("Need to implement (or pass) 'on_scheduled_tweet'.")

    def on_mention(self):
        raise NotImplementedError("Need to implement (or pass) 'on_mention'.")

    def on_timeline(self):
        raise NotImplementedError("Need to implement (or pass) 'on_timeline'.")

    def on_follow(self, f_id):
        """
        Handler when a new follower is / new followers are detected.

        For basic uses, the configuration options provided will suffice. If you
        also want the bot to do other things when a new follower is acquired, you
        will need to override this method (though you can avoid replicating the
        code here by invoking super.on_follow()).

        Parameters
        ----------
        f_id : string
            Twitter user ID of the new follower.
        """
        self.state['followers'].append(f_id)

        # Do we automatically follow back?
        if self.config['autofollow']:
            try:
                self.api.create_friendship(f_id, follow = True)
                self.state['friends'].append(f_id)
                logging.info("Followed user id '%s'" % f_id)
            except tweepy.TweepyError as e:
                logging.error("Error following user '%s': %s, %s" % (f_id, e.message[0]['code'], e.message[0]['message']))

    def on_search(self):
        raise NotImplementedError("Need to implement (or pass) 'on_search'.")

    def bot_init(self):
        """
        Custom initialization. Specify any configuration options you want to
        override, as in particular your OAuth credentials.

        ** Use the provided scripts to generate a template for you to fill in. **
        """
        raise NotImplementedError("D'oh, you didn't implement the 'bot_init()' method.")

    def run(self):
        """
        PyBot's main run method. This activates ALL the things.
        """
        self.running = True
        while self.running:
            intervals = []
            current_time = time.time()

            # Check followers.
            if self.config['follow_interval'] != 0 and \
                    current_time > self.state['next_follow_time']:

                # Update.
                self.state['last_follow_time'] = current_time
                self.state['next_follow_time'] = self._increment(current_time, self.config['follow_interval'])

            # Check timeline.
            if self.config['timeline_interval'] != 0 and \
                    current_time > self.state['next_timeline_time']:

                # Update.
                self.state['last_timeline_time'] = current_time
                self.state['next_timeline_time'] = self._increment(current_time, self.config['timeline_interval'])

            # Check mentions.
            if self.config['mention_interval'] != 0 and \
                    current_time > self.state['next_mention_time']:

                # Update.
                self.state['last_mention_time'] = current_time
                self.state['next_mention_time'] = self._increment(current_time, self.config['mention_interval'])

            # Check keywords.
            if self.config['search_interval'] != 0 and \
                    current_time > self.state['next_search_time']:

                # Update.
                self.state['last_search_time'] = current_time
                self.state['next_search_time'] = self._increment(current_time, self.config['search_interval'])

            # Check tweets.
            if self.config['tweet_interval'] != 0 and \
                    current_time > self.state['next_tweet_time']:

                # Update.
                self.state['last_tweet_time'] = current_time
                self.state['next_tweet_time'] = self._increment(current_time, self.config['tweet_interval'])

            # Check custom handlers.
            for callback in self.custom_callbacks:
                if callback['condition']() and current_time > callback['next_run']:
                    # Invoke the action!
                    callback['action']()

                    # Update the interval for the next run.
                    callback['last_run'] = current_time
                    callback['next_run'] = self._increment(current_time, callback['interval'])
                    intervals.append(callback['next_run'])

            # Save the current state.
            self._save_state()

            # Find the next timestamp.
            next_action = min(intervals)
            if current_time < next_action:
                time.sleep(next_action - current_time)

        # If the loop breaks, someone hit CTRL+C.
        logging.info("Shutdown complete!")

    def _increment(self, previous, interval):
        """
        Helper method for dealing with callable time intervals.
        """
        update = previous
        if hasattr(interval, '__call__'):
            update += interval()
        else:
            update += interval
        return update

    def _handler(self, signum, frame):
        """
        Signal handler. Gracefully exits.
        """
        logging.info("SIGINT caught, beginning shutdown...")
        self.running = False

    def _save_state(self):
        """
        Serializes the current bot's state in case we halt.
        """
        self.config['storage'].write('%s_state.pkl' % self.screen_name, self.state)
        logging.info("Bot state saved.")
