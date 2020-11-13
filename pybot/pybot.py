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

import http.client
import logging
import multiprocessing as mp
import re
import signal
import sys
import time

import tweepy

from .storage import PickleStorage

class PyBot(tweepy.StreamListener):

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
        self.actions = ['timeline',  # Something shows up on the home timeline.
                        'mention',   # This bot gets mentioned.
                        'search',    # Something appears in a keyword search.
                        'follow',    # This bot gets a new follower.
                        'tweet',     # This bot posts a tweet.
                        ]
        self.config = {'%s_interval' % action: 0 for action in self.actions}

        # Number of tweets allowed to be buffered in-memory from the streaming
        # API. Increasing this number gives you a larger sample of tweets, but
        # it can potentially crash your machine if the number is too high.
        # If an incoming status would overflow the buffer, the oldest status in
        # the buffer is discarded.
        self.config['streaming_buffer_length'] = 100000

        # List of keywords to search for and take action on when found.
        # NOTE: This is a completely separate list of keywords from the
        # `autofav_keywords` list below.
        self.config['search_keywords'] = []

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

        # If True, this bot discards any timeline tweets with mentions (to any user).
        self.config['ignore_timeline_mentions'] = False

        # Logging level. See https://docs.python.org/2/library/logging.html#logging-levels
        # for more details.
        self.config['logging_level'] = logging.DEBUG

        # Adapter for saving/loading this PyBot's state.
        self.config['storage'] = PickleStorage()

        # Denotes users the bot will never mention or respond to.
        self.config['blacklist'] = []

        # Languages to filter on when conducting searches.
        self.config['languages'] = ['en']

        #
        # End configuration options.
        #
        # Now we start initializing the bot.
        #

        # Required implementation by all subclasses. Produces an error if it
        # is not implemented.
        self.bot_init()

        # Set up a signal handler so a bot can gracefully exit.
        signal.signal(signal.SIGINT, self._handler)

        # Set up OAuth with Twitter and pull down some basic identities.
        auth = tweepy.OAuthHandler(self.config['api_key'], self.config['api_secret'])
        auth.set_access_token(self.config['access_key'], self.config['access_secret'])
        self.api = tweepy.API(auth)
        self.id = self.api.me().id
        self.screen_name = self.api.me().screen_name

        # Set up the streaming API. May or may not need this.
        self.stream = tweepy.Stream(auth, self)
        self.lock = mp.Lock()
        self.buffer = []

        # Set up logging.
        logging.basicConfig(format = '%(asctime)s | %(levelname)s: %(message)s',
            datefmt = '%m/%d/%Y %I:%M:%S %p',
            filename = '{}.log'.format(self.config['bot_name']),
            level = self.config['logging_level'])

        # Try to load any previous state.
        logging.info("---STARTUP---")
        logging.info("Setting bot state...")
        s = self.config['storage'].read('{}_state.pkl'.format(self.config['bot_name']))
        if s is None:
            # No previous state to load? Initialize everything.
            curr_t = time.time()

            # Timeline configuration options. Set timeline_interval to 0 to
            # disable checking the bot's timeline.
            self.state['last_timeline_id'] = 1
            self.state['last_timeline_time'] = curr_t
            self.state['next_timeline_time'] = self._increment(curr_t, self.config['timeline_interval'])

            # Mention configuration options. Set mention_interval to 0 to
            # disable checking the bot's mentions.
            self.state['last_mention_id'] = 1
            self.state['last_mention_time'] = curr_t
            self.state['next_mention_time'] = self._increment(curr_t, self.config['mention_interval'])

            # Keyword search configuration options. Set search_interval to 0 to
            # disable searching for keywords in the public timeline.
            self.state['last_search_id'] = 1
            self.state['last_search_time'] = curr_t
            self.state['next_search_time'] = self._increment(curr_t, self.config['search_interval'])
            self.state['search_hits'] = []

            # Active tweeting configuration. Set tweet_interval to 0 to
            # disable posting otherwise-unprovoked tweets.
            self.state['last_tweet_id'] = 1
            self.state['last_tweet_time'] = curr_t
            self.state['next_tweet_time'] = self._increment(curr_t, self.config['tweet_interval'])

            # List of user IDs you follow.
            self.state['friends'] = self.api.friends_ids(self.id)

            # List of user IDs that follow you.
            self.state['followers'] = self.api.followers_ids(self.id)

            # List of new followers since the last check (internal) timestamp.
            self.state['new_followers'] = []
            self.state['last_follow_time'] = curr_t
            self.state['next_follow_time'] = self._increment(curr_t, self.config['follow_interval'])
        else:
            # Use loaded state.
            self.state = s

        logging.info("Bot state set.")

    # # # # # # # # # # # # # # # # # # # # # # #
    #       Available should the user wish.     #
    # # # # # # # # # # # # # # # # # # # # # # #

    def register_custom_callback(self, action, interval):
        """
        Registers a user-defined callback action. Performs the action after
        the specified interval.

        Parameters
        ----------
        action : function
            Function which specifies the custom action to take.
        interval : integer or callable
            Number of seconds to wait before execution, or a
            callable that returns the number of seconds to wait.
        """
        callback = {
            'action': action,
            'interval': interval,
            'last_run': 0,
            'next_run': 0,
        }
        self.custom_callbacks.append(callback)

    # # # # # # # # # # # # # # # # # # # # # # #
    #      Methods that MUST be implemented.    #
    # # # # # # # # # # # # # # # # # # # # # # #

    def on_tweet(self):
        raise NotImplementedError("Need to implement (or pass) 'on_tweet'.")

    def on_mention(self, tweet, prefix):
        raise NotImplementedError("Need to implement (or pass) 'on_mention'.")

    def on_timeline(self, tweet, prefix):
        raise NotImplementedError("Need to implement (or pass) 'on_timeline'.")

    def on_follow(self, friend):
        raise NotImplementedError("Need to implement (or pass) 'on_follow'.")

    def on_search(self, tweet):
        raise NotImplementedError("Need to implement (or pass) 'on_search'.")

    def bot_init(self):
        raise NotImplementedError("D'oh, you didn't implement the 'bot_init()' method.")

    # # # # # # # # # # # # # # # # # # # # # # #
    #        Call this to start your bot.       #
    # # # # # # # # # # # # # # # # # # # # # # #

    def run(self):
        """
        PyBot's main run method. This activates ALL the things.
        """
        self.running = True
        while self.running:
            intervals = []
            current_time = time.time()

            # Check all the built-in actions.
            for action in self.actions:
                if self.config['%s_interval' % action] != 0 and \
                        current_time > self.state['next_%s_time' % action]:

                    # Do something.
                    getattr(self, '_handle_%s' % action)()

                    # Update state.
                    self.state['last_%s_time' % action] = current_time
                    self.state['next_%s_time' % action] = self._increment(current_time, self.config['%s_interval' % action])
                if self.config['%s_interval' % action] != 0:
                    intervals.append(self.state['next_%s_time' % action])

            # Check custom handlers.
            for callback in self.custom_callbacks:
                if current_time > callback['next_run']:
                    # Invoke the action!
                    callback['action']()

                    # Update the interval for the next run.
                    callback['last_run'] = current_time
                    callback['next_run'] = self._increment(current_time, callback['interval'])
                intervals.append(callback['next_run'])

            # Are there any more actions?
            if len(intervals) == 0:
                logging.warn("No actions are set! Switching bot OFF.")
                self.running = False
            else:
                # Save the current state.
                self._save_state()

                # Find the next timestamp.
                next_action = min(intervals)
                if current_time < next_action:
                    logging.info("Sleeping for %.4f seconds." % (next_action - current_time))
                    time.sleep(next_action - current_time)

        # If the loop breaks, someone hit CTRL+C.
        logging.info("---SHUTDOWN---")

    # # # # # # # # # # # # # # # # # # # # # # #
    #   Twitter DSL methods. Use these often.   #
    # # # # # # # # # # # # # # # # # # # # # # #

    def update_status(self, status, reply_to = None, lat = None, lon = None):
        """
        Basic DSL method for posting a status update to Twitter.

        Parameters
        ----------
        status : string
            Text of the update. Truncated to 140 characters, so make sure
            it's the right length.
        reply_to : tweepy.Status or None
            Implements the threaded tweets on Twitter, marking this as a reply.
        lat, lon : float or None
            Latitude and longitude of the tweet location.

        Returns
        -------
        True on success, False on failure.
        """
        status = status.format('utf8', 'ignore')
        kwargs = {'status': status}

        try:
            logging.info("Tweeting: '%s'" % status)
            if reply_to is not None:
                logging.info("--Response to %s" % self._tweet_url(reply_to))
                kwargs['in_reply_to_status_id'] = reply_to.id

            # Push out the tweet.
            tweet = self.api.update_status(**kwargs)

            # Log the URL.
            logging.info("Tweet posted at %s" % self._tweet_url(tweet))
            return True

        except tweepy.TweepError as e:
            logging.error("Unable to post tweet: %s" % e[0][0]['message'])
            return False

    def create_favorite(self, tweet):
        """
        Basic DSL for favorite-ing a tweet.

        Parameters
        ----------
        tweet : tweepy.Status
            tweepy Status object.

        Returns
        -------
        True on success, False on failure.
        """
        try:
            logging.info("Favoriting %s" % self._tweet_url(tweet))
            self.api.create_favorite(tweet.id)
            return True
        except tweepy.TweepError as e:
            logging.error("Unable to favorite tweet: %s" % e[0][0]['message'])
            return False

    def create_friendship(self, friend):
        """
        Basic DSL for following a twitter user.

        Parameters
        ----------
        friend : integer
            Twitter ID of the user to follow.

        Returns
        -------
        True on success, False on failure.
        """
        try:
            logging.info("Following user %s" % friend)
            self.api.create_friendship(friend, follow = True)
            self.state['friends'].append(friend)
            return True
        except tweepy.TweepError as e:
            logging.error("Unable to follow user '%s': %s" % (friend, e[0][0]['message']))
            return False

    # # # # # # # # # # # # # # # # # # # # # # #
    #     Helper methods. Leave these alone.    #
    # # # # # # # # # # # # # # # # # # # # # # #

    def _handle_tweet(self):
        """
        Processes posting a tweet.
        """
        logging.info("Preparing for posting a new tweet...")
        self.on_tweet()
        logging.info("Tweet completed")

    def _handle_timeline(self):
        """
        Processes the home timeline for the bot (excludes mentions).
        """
        logging.info("Reading current timeline...")
        try:
            # Retrieve the last 500 posts on the timeline.
            timeline = self.api.home_timeline(
                since_id = self.state['last_timeline_id'], count = 500)

            # Delete tweets this bot posted, tweets that mention this bot, and blacklisted users.
            current_timeline = []
            for t in timeline:
                if t.author.screen_name.lower() != self.screen_name.lower() and \
                        t.author.screen_name.lower() not in self.blacklist and \
                        not re.search('@%s' % self.screen_name, t.text, flags = re.IGNORECASE):
                    current_timeline.append(t)

            # Do we ignore ALL mentions (tweets that mention OTHER users, NOT the bot)?
            if self.config['ignore_timeline_mentions']:
                current_timeline = [t for t in current_timeline if '@' not in t.text]

            # Process what's left over.
            if len(current_timeline) > 0:
                self.state['last_timeline_id'] = current_timeline[0].id
                for tweet in list(reversed(current_timeline)):
                    # Run the tweet through the timeline callback.
                    prefix = self._mention_prefix(tweet)
                    self.on_timeline(tweet, prefix)

                    # Check the tokens in the tweet for keywords.
                    words = tweet.text.lower().split()
                    if any(w in words for w in self.config['autofav_keywords']):
                        self.create_favorite(tweet)

        except tweepy.TweepError as e:
            logging.error("Unable to retrieve timeline: %s" % e[0][0]['message'])
        except http.client.IncompleteRead as e:
            logging.error("IncompleteRead error, aborting timeline update.")

        logging.info("Finished processing timeline.")

    def _handle_mention(self):
        """
        Processes the list of mentions for the bot.
        """
        logging.info("Checking for new mentions...")
        try:
            # Snag the last 100 mentions.
            mentions = self.api.mentions_timeline(
                since_id = self.state['last_mention_id'], count = 100)

            # Do we only look at direct mentions?
            if self.config['reply_direct_mention_only']:
                mentions = [t for t in mentions if re.split('[^@\w]', t.text)[0] == '@%s' % self.screen_name]

            # Process remaining mentions.
            if len(mentions) > 0:
                self.state['last_mention_id'] = mentions[0].id
                for mention in list(reversed(mentions)):

                    # Send the tweet to the callback.
                    prefix = self._mention_prefix(mention)
                    self.on_mention(mention, prefix)

                    # Do we autofav?
                    if self.config['autofav_direct_mentions']:
                        self.create_favorite(mention)

        except tweepy.TweepError as e:
            logging.error("Unable to retrieve mentions: %s" % e[0][0]['message'])
        except http.client.IncompleteRead as e:
            logging.error("IncompleteRead error, aborting mentions.")

        logging.info("Finished processing mentions.")

    def _handle_search(self):
        """
        Conducts a keyword search.
        """
        logging.info("Searching for keywords...")

        # Is the streamer even running?
        if not self.stream.running:
            # Are there any keywords we should be filtering on?
            if len(self.config['search_keywords']) > 0:
                # Yes, do a filter on the keywords.
                logging.info("Starting the streaming filter.")
                self.stream.filter(languages = self.config['languages'],
                    track = self.config['search_keywords'],
                    is_async = True)
            else:
                # Nope, just do a sample.
                self.stream.sample(languages = self.config['languages'], is_async = True)
                logging.info("Starting the streaming sample.")
        else:
            # Grab the static snapshot of the current buffer.
            tweets = list(reversed(self.buffer))

            # Clear out the buffer.
            self.lock.acquire()
            self.buffer = []
            self.lock.release()

            # Process the tweets.
            logging.info("Received %s tweets from the streaming API, now processing." % len(tweets))
            for tweet in tweets:
                if tweet.author.screen_name in self.config['blacklist']: continue
                self.on_search(tweet)

                # Test for autofav keywords.
                # Check the tokens in the tweet for keywords.
                words = tweet.text.lower().split()
                if any(w in words for w in self.config['autofav_keywords']):
                    self.create_favorite(tweet)

        logging.info("Search complete.")

    def _handle_followers(self):
        """
        Processes new followers and invokes the appropriate callback.
        """
        logging.info("Checking for new followers...")

        # Grab the list of new followers.
        try:
            self.state['new_followers'] = [fid for fid in self.api.followers_ids(self.id) if fid not in self.state['followers'] and self.api.get_user(fid).screen_name not in self.blacklist]
        except tweepy.TweepError as e:
            logging.error("Unable to update followers: %s (%s)" % (e[0]['message'], e[0]['code']))

        # Invoke the callback.
        for f in self.state['new_followers']:
            self.state['followers'].append(f)

            # Do we automatically follow back?
            if self.config['autofollow']:
                self.create_friendship(f)

            # Callback.
            self.on_follow(f)

        # Update the timestamps.
        logging.info("Followers updated")
        if len(self.state['new_followers']) > 0:
            logging.info("--%s new followers processed" % len(self.state['new_followers']))
            self.state['new_followers'] = []

    def _mention_prefix(self, tweet):
        """
        Helper method to get the list of mentions in a tweet for responding.
        """
        respond = ['@%s' % tweet.author.screen_name]
        respond += [s for s in re.split('[^@\w]', tweet.text) if len(s) > 2 and s[0] == '@' and s[1:].lower() != self.screen_name.lower() and s[1:].lower() not in self.blacklist]

        if self.config['reply_followers_only']:
            # Delete any users who aren't a follower.
            respond = [s for s in respond if s[1:].lower() in self.state['followers'] or s == '@%s' % tweet.author.screen_name]

        # Return the list as a string.
        return ' '.join(respond)

    def _tweet_url(self, tweet):
        """
        Helper method for constructing a URL to a specific tweet.
        """
        return "https://twitter.com/%s/status/%s" % (tweet.author.screen_name, str(tweet.id))

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
        logging.info("SIGINT caught, shutting down.")
        self.running = False
        if self.stream.running:
            self.stream.disconnect()
        self._save_state()
        sys.exit()

    def _save_state(self):
        """
        Serializes the current bot's state in case we halt.
        """
        self.config['storage'].write('{}_state.pkl'.format(self.config['bot_name']), self.state)
        logging.info("Bot state saved.")

    # # # # # # # # # # # # # # # # # # # # # # #
    #    Streaming methods. Leave these alone.  #
    # # # # # # # # # # # # # # # # # # # # # # #

    def on_status(self, status):
        """
        Invoked whenever a new status arrives through the streaming listener,
        whether from sample() or filter(). The status is appended to the buffer;
        if the buffer length exceeds its limit, the oldest status is dropped.
        """
        # Acquire the lock.
        self.lock.acquire()

        # Would adding this tweet to the buffer overflow it?
        while len(self.buffer) >= self.config['streaming_buffer_length']:
            self.buffer.pop(0)

        # Append the new status
        self.buffer.append(status)

        # Release the lock.
        self.lock.release()

    def on_error(self, status_code):
        pass

    def on_exception(self, exception):
        pass
