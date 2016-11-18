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

from pybot import PyBot

class PyBotTemplate(PyBot):

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

        # Posts a tweet every 30 minutes.
        self.config['tweet_interval'] = 30 * 60
        self.config['bot_name'] = 'PyBotTemplate'

        #############################
        #                           #
        #   Customize your bot's    #
        #      behavior here.       #
        #                           #
        #############################

        # Custom state variables for your bot can be created here, using the
        # self.state dictionary. Note: any previous state loaded by the bot
        # will overwrite state values made here. In effect, these values
        # are initializations only.

        # self.state['echo_counter'] = 0

        # User-provided functions to more fully customize bot behavior can
        # be registered here. By providing a function, a runtime interval,
        # and a boolean condition, you can effectively have your bot do
        # anything above and beyond the core actions provided.

        # If, in addition to echoing any replies this bot receives, you want
        # it to post the number of replies it's received so far every 24 hours,
        # you could register a function like this.

        # self.register_custom_callback(self.count_replies, 24 * 60 * 60)

        # count_replies() gives the current count of replies.
        # (yes this is something you could also do with `tweet_interval`)

    def on_tweet(self):
        """
        Handler for posting a tweet to the bot's public timeline.

        Use the `self.update_status` method to post a tweet.

        Set `self.config['tweet_interval']` to something other than 0 to set
        the interval in which this method is called (or keep at 0 to disable).
        """
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
        pass

    def on_timeline(self, tweet, prefix):
        """
        Handler for responding to tweets that appear in the bot's timeline.

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
        pass

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
        pass

    def on_follow(self, friend):
        """
        Handler when a new follower is / new followers are detected.

        For basic uses, the configuration options provided will suffice. If you
        also want the bot to do other things when a new follower is acquired, you
        will need to override this method (though you can avoid replicating the
        code that processes auto-follows by keeping super.on_follow()).

        Parameters
        ----------
        friend : string
            Twitter user ID of the new follower.
        """
        pass

if __name__ == "__main__":
    bot = PyBotTemplate()  # In this case, a basic Echo bot.
    bot.run()
