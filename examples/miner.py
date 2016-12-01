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

import json
import re

from pybot import PyBot

class Miner(PyBot):

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

        # Listens to the streaming timeline and filters on keywords
        self.config['bot_name'] = 'Miner'
        self.config['search_keywords'] = []
        self.config['search_interval'] = 10

        #############################
        #                           #
        #   Customize your bot's    #
        #      behavior here.       #
        #                           #
        #############################

        self.state['buffer'] = []

    def on_search(self, tweet):
        """
        Handler for responding to public tweets that contain certain keywords,
        as specified in self.config['search_keywords'].

        Parameters
        ----------
        tweet : tweepy.Status object
            Contains the status update pertaining to the mention. The fields in
            this object mimic Twitter's Tweet object:
            https://dev.twitter.com/overview/api/tweets
        """
        if 'RT @' in tweet.text:
            return None

        # Some filtering and preprocessing.
        text = tweet.text.replace("\n", " ").lower()
        text = re.sub(r"http\S+", "", text)
        d = {
            'user_name': tweet.user.screen_name,
            'user_created': str(tweet.user.created_at),
            'user_profile': tweet.user.description,
            'user_followers': tweet.user.followers_count,
            'user_friends': tweet.user.friends_count,
            'user_id': tweet.user.id_str,
            'user_tweets': tweet.user.statuses_count,
            'tweet_text': text,
            'tweet_coords': tweet.coordinates['coordinates'] if tweet.coordinates is not None else '',
            'tweet_created': str(tweet.created_at),
            'tweet_favorited': tweet.favorite_count,
            'tweet_retweeted': tweet.retweet_count,
            'tweet_id': tweet.id_str,
            'in_reply_to_screen_name': tweet.in_reply_to_screen_name,
        }
        with open("tweets.json", "a") as f:
            f.write("{}\n".format(json.dumps(d)))

    def on_tweet(self):
        pass

    def on_mention(self, tweet, prefix):
        pass

    def on_timeline(self, tweet, prefix):
        pass

    def on_follow(self, friend):
        pass

if __name__ == "__main__":
    bot = Miner()  # In this case, a basic listener bot.
    bot.run()
