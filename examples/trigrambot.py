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
import numpy as np

from pybot import PyBot

class TrigramBot(PyBot):

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

        # Custom variables.
        self.config['trigram_s1'] = '_START1_'
        self.config['trigram_s2'] = '_START2_'
        self.config['trigram_end'] = '_STOP_'

        # Posts a tweet every 45-ish minutes.
        self.config['normal_mean'] = 45
        self.config['normal_std'] = 5
        self.config['tweet_interval'] = lambda: np.random.normal(
            loc = self.config['normal_mean'], scale = self.config['normal_std'])

        # Custom override--sampling the public timeline continuously.
        self.stream.sample(languages = self.config['languages'], async = True)

    def on_tweet(self):
        """
        Handler for posting a tweet to the bot's public timeline.

        Use the `self.update_status` method to post a tweet.

        Set `self.config['tweet_interval']` to something other than 0 to set
        the interval in which this method is called (or keep at 0 to disable).
        """
        # Check out the list of tweets from the buffer.
        tweets = list(reversed(self.buffer))

        # Clear out the buffer.
        self.lock.acquire()
        self.buffer = []
        self.lock.release()

        # Now let's process the tweets into a glorified 2nd-order Markov chain.
        model = {}
        for tweet in tweets:
            processed = '%s %s %s %s' % (self.config['trigram_s1'],
                self.config['trigram_s2'], tweet.text.strip(),
                self.config['trigram_end'])
            tokens = processed.split()
            triples = [[tokens[i], tokens[i + 1], tokens[i + 2]] for i in range(len(tokens) - 2)]
            for w1, w2, w3 in triples:
                key = (w1, w2)
                if key in model:
                    model[key].append(w3)
                else:
                    model[key] = [w3]

        # We have the model. Let's sample from it to build a post.
        post = ""
        k1 = self.config['trigram_s1']
        k2 = self.config['trigram_s2']
        key = (k1, k2)
        nextToken = model[key][np.random.randint(0, len(model[key]))]
        while nextToken != self.config['trigram_end'] and len('%s %s' % (post, nextToken)) < 140:
            post = '%s%s' % (post, nextToken)
            k1 = k2
            k2 = nextToken
            key = (k1, k2)
            nextToken = model[key][np.random.randint(0, len(model[key]))]

        # Post the tweet!
        self.update_status(post)

        # As a sanity check, make sure the streaming API is still running.
        if not self.stream.running:
            logging.error("Streaming API crashed for some reason! Quitting...")
            self.running = False

    def on_mention(self, tweet, prefix):
        pass

    def on_timeline(self, tweet, prefix):
        pass

    def on_search(self, tweet):
        pass

    def on_follow(self, friend):
        pass

if __name__ == "__main__":
    bot = TrigramBot()
    bot.run()
