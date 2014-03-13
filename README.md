PyBot, v0.1
===========

This is a port of [my previous attempt at a Twitterbot](https://github.com/magsol/Twitterbot), the primary difference being this is in Python instead of PHP. Arguably an improvement all by itself :)

PyBot is designed to be a modular and lightweight framework in which users can create and deploy autonomous bots that do all sorts of things on Twitter. PyBot helps you create the bots, but it's still largely up to you to implement how they work.

Installation
------------

Download the source. Yay!


Dependencies
------------

  - [Python v2.7+](http://www.python.org/) (untested with Python 3)
  - [SQLAlchemy v0.8+](http://www.sqlalchemy.org/)
  - [tweepy v2.2+](https://github.com/tweepy/tweepy)
  - Any other dependencies are bot-dependent

Documentation
-------------

**Creating new bots**: You can issue the command

    python pybot.py create -n <botname>

This will walk you through the process of creating a new bot, and in particular creating OAuth credentials (which you'll need for any kind of meaningful interaction with Twitter). Simply follow the instructions that appear. PyBot will generate a code template with all the basic information filled in; however, your bot won't do anything until you create the implementation.

All bots ultimately require the user to implement their `run()` methods. This is invoked when a bot is started. For those familiar with my previous PHP-based Twitterbot, these bots are *not* implicitly designed to be daemons (though they certainly can be). This decision was made so users could create very elaborate multithreaded and multiprocess bots without having to circumvent the main framework.

IMPORTANT: The name you give the bot on the command-line has *no intrinsic connection* to the Twitter username. As such, you are more than welcome to implement multiple bots that all use the same OAuth credentials (and therefore report to the same Twitter account). This is simply a mechanism by which PyBot distinguishes between bots.

**Installing existing bots**: Since there's no unifying architecture between bot implementations, you can simply drop a uniquely-named folder into the root `pybot` directory. As long as it adheres to the PyBot inheritance conventions, it should run just fine (e.g. see my [pybot-impls project](https://github.com/magsol/pybot-impls/)).

**Starting a bot**: Run the command

    python pybot.py start -n <botname>

This will start the specified bot. You have a couple of options in terms of how you want to do this.

 - You can implement your bot to run once and then stop. In this case, you could tie the bot to a cronjob (run `crontab -e`) that invokes this command repeatedly over regular intervals.
 - You can create a `while True` loop that runs your bot indefinitely. In this case, the console you invoke the command from will be tied up until you either CTRL+C or otherwise kill the process. Along these lines, you could also append a `&` to the end of the initial command, backgrounding the process so you can still use your console.
 - You can get really clever and make your bot into a daemon, detaching it from the console entirely.

**Stopping a bot**: Run the command

    python pybot.py stop -n <botname>

This will send a SIGTERM signal to your bot, hopefully killing it. This is really only applicable if you daemonized your bot, or if something went wrong and your bot is hanging when it should have stopped.

IMPORTANT: In some cases, SIGTERM actually won't kill the bot (it requires SIGKILL). I'm still working on this problem.

License
-------
    Copyright 2014 Shannon Quinn

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.