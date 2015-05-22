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

from pybot import PyBot

class CPCB(PyBot):

    def bot_init(self):
        """
        Custom initialization. Specify any configuration options you want to
        override, as in particular your OAuth credentials.
        """

        #############################
        #                           #
        # Twitter OAuth Credentials #
        #                           #
        #      FILL THESE IN!       #
        #                           #
        #############################

        self.config['api_key'] = ''
        self.config['api_secret'] = ''
        self.config['access_key'] = ''
        self.config['access_secret'] = ''

        #############################
        #                           #
        #   Other config options    #
        #                           #
        # Fill these in if you want #
        #   or otherwise need to.   #
        #                           #
        #############################

        # Look for replies every 60 minutes.
        self.config['mention_interval'] = 60 * 60

        # List of authorized users.
        self.config['authorized_accounts'] = ['twitter']

    def on_tweet(self):
        pass

    def on_mention(self, tweet, prefix):
        """
        Handler for responding to mentions at the bot.

        When calling `self.update_status`, make sure you set the `reply_to`
        parameter to point to the tweet object, or Twitter will not recognize
        this tweet as a reply to the original.

        Parameters
        ----------
        tweet : tweepy.Status object
            Contains the status update pertaining to the mention. The fields in
            this object mimic Twitter's Tweet object:
            https://dev.twitter.com/overview/api/tweets
        prefix : string
            String containing all the mentions from the original tweet, excluding
            your bot's screen name, any users in the blacklist, and any users
            you do not follow IF self.config['reply_followers_only'] is True.
        """
        # Is the author of the tweet in the authorized users' list?
        if tweet.author.screen_name.lower() in self.config['authorized_accounts']:
            # Retweet the status.
            self.api.retweet(tweet.id)
            logging.info("Retweeted status %s" % self._tweet_url(tweet))

    def on_timeline(self, tweet, prefix):
        pass

    def on_search(self, tweet):
        pass

    def on_follow(self, friend):
        pass

if __name__ == "__main__":
    bot = CPCB()
    bot.run()
