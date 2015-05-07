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
        pass

    def on_mention(self):
        pass

    def on_timeline(self):
        pass

    def on_search(self):
        pass

if __name__ == "__main__":
    bot = PyBotTemplate()  # In this case, a basic Echo bot.
    bot.run()
