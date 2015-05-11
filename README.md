PyBot, v0.2.0
=============

This is a port of [my previous attempt at a Twitterbot](https://github.com/magsol/Twitterbot), the primary difference being this is in Python instead of PHP. Arguably an improvement all by itself :)

PyBot is designed to be a modular and lightweight framework in which users can create and deploy autonomous bots that do all sorts of things on Twitter. PyBot helps you create the bots, but it's still largely up to you to implement how they work.

Installation
------------

Download the source. Make sure the dependencies are satisfied. Yay!

Dependencies
------------

  - [Python v2.7+](http://www.python.org/) (untested with Python 3)
  - [tweepy v3.3+](https://github.com/tweepy/tweepy)
  - Any other dependencies are bot-dependent

Documentation
-------------

**v0.2.0 is a significant overhaul of the source from v0.1.0.** Please read the following documentation carefully, especially if you are familiar with PyBot's previous architecture.

**Creating new bots**: You can use the provided script in the `sbin` folder to create new bots:

    sbin/create_pybot.py

This will give you a list of arguments you can provide. The only required argument is the bot's name; this can be anything you want, and it bears no intrinsic connection to the Twitter user you connect the bot to. The name you give this script is purely to distinguish between your PyBots.

Optionally, you can provide your OAuth credentials if you have them already (`api_key`, `api_secret`, `access_key`, and `access_secret`). Otherwise, the script will take you through the process of registering an app on Twitter, generating the necessary credentials, and integrating them with your bot.

**Implementing an action**: The core functionality of PyBot revolves around the concept of an *action*. Activities such as posting a tweet, reading a reply, "favorite-ing" a tweet, or searching for keywords all constitute different types of actions.

There are two phases to an action: a *delay interval* and a *callback*. During the delay interval, or waiting time between handling time of actions, your bot essentially sleeps. Depending on the action, it may still be doing something behind the scenes (e.g. reading from Twitter's Streaming API), but for all practical purposes it is sleeping.

Once the delay interval has elapsed, the callback phase kicks in. This is where the action is explicitly handled.

As an example, let's say you want your bot to post the time every hour. Our `HourlyBot` will have a 1-hour tweet interval, set using this configuration option:

    def bot_init(self):

        self.config['tweet_interval'] = 60 * 60

        # ...
        # Other configuration options here
        # ...

(the intervals are in seconds, so to get 60 minutes we need 3,600 seconds, or 60 * 60)

By itself, this means `HourlyBot` will activate a *tweet* callback every 60 minutes. With the interval in place, now we have to implement the actual callback. This is done with the `on_tweet()` method.

    def on_tweet(self):
        from datetime import datetime
        self.update_status("It is %s." % datetime.strftime(datetime.now(), "%I:%M%p"))

And that's it! The PyBot internals take care of logging, saving state, putting the bot to sleep between callbacks, and waking it up at the correct intervals. See the `examples/` folder for more examples.

**Starting a bot**: Run the command

    python your_bot.py

This will start the specified bot. The above script generates a bot that has a single action defined; you can specify more if you want. However, if you remove all actions, this will be detected and the bot will automatically terminate. Otherwise, it will simply run forever.

**Stopping a bot**: A simple CTRL+C should do the trick! This will send a SIGTERM signal to your bot, which has a handler in place to catch the termination signal and gracefully shut down.

Acknowledgements
----------------

The original inspiration for this bot came from [Rob Hall's postmaster9001](https://twitter.com/postmaster9001) in the late 2000s, and gave birth to the (now-deprecated) PHP version linked above.

Architectural aspects of PyBot were inspired in part from [muffinista's chatterbot](https://github.com/muffinista/chatterbot/) and [thricedotted's twitterbot](https://github.com/thricedotted/twitterbot). In particular, the blacklist and DSL aspects come from muffinista, while the object-oriented design and functional callbacks are taken from thricedotted.

If you are familiar with thricedotted's Python twitterbot, you will find many similarities in PyBot. I chose not to make PyBot a direct fork of twitterbot, as it is not backwards-compatible at all. Still, it retains enough architectural similarity to warrant mention.

License
-------
    Copyright 2015 Shannon Quinn

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.