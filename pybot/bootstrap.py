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

import ConfigParser
import importlib
import os
import os.path
import tweepy
import tweepy.error

def start(botname):
    module = _bot_exists(botname)
    instance = module.__getattribute__(botname.capitalize())()

    # Invokes the parent run() method first. This sets up the pidfile in case
    # the process is daemonized or set to run indefinitely.
    super(type(instance), instance).run()
    instance.run()

def stop(botname):
    """
    This method of stopping a bot is only required if you have backgrounded
    or otherwise daemonized its process, and it would run indefinitely otherwise.
    """
    _bot_exists(botname)
    cfg = ConfigParser.SafeConfigParser()
    cfg.read('%s/settings.cfg' % botname)
    pidfile = cfg.get('bot', 'pidfile')
    if os.path.exists(pidfile):
        # Delete the pidfile. This will message the process
        pid = -1
        try:
            f = open(pidfile, "r")
            pid = int(f.readline().strip())
            f.close()
            os.remove(pidfile)
        except IOError:
            print 'Unable to read PID file. Perhaps "%s" is not running?' % botname
        except OSError, err:
            err = str(err)
            print err
        print 'Sent process %s a halt signal.' % pid
    else:
        print 'PID file "%s" does not exist. Perhaps "%s" is not running?' % (pidfile, botname)

def list():
    bots = 0
    running = 0
    harddirs = ['lib', 'test']
    for item in os.listdir("."):
        if os.path.isdir(item) and item.lower() not in harddirs and item[0] != ".":
            bots += 1
            _bot_exists(item)
            cfg = ConfigParser.SafeConfigParser()
            cfg.read('%s/settings.cfg' % item)
            pid = ''
            if os.path.exists(cfg.get("bot", "pidfile")):
                running += 1
                f = open(cfg.get("bot", "pidfile"), "r")
                pid = ' (running: %s)' % int(f.readline().strip())
                f.close()
            print '[%s] %s%s' % (bots, cfg.get("bot", "name"), pid)
    print '\n%s bot%s found (%s running).' % (bots, 's' if bots != 1 else '', running)

def create(botname, consumer_key, consumer_secret, access_token, access_token_secret):
    """
    Creates a new bot and takes the user through the initialization and setup process.

    While potentially any combination of consumer* and access* can be None,
    the only cases supported here are:
    - all are provided
    - consumer* are provided
    - none are provided

    Parameters
    ----------
    botname : string
        Name of the bot the user wishes to create. Must be unique.
    consumer_key : string or None
    consumer_secret : string or None
        Consumer key and secret for the app. The same pairing can be used across
        many bots. These need to be obtained from dev.twitter.com. If either of
        these is None, the user will be prompted to enter both.
    access_token : string or None
    access_token_secret : string or None
        Access token and secret. A unique pair must be generated for each bot.
        If either of these is None, a new pair will be generated automatically.
    """

    print """*********************
* Welcome to PyBot! *
*********************

This script will help you set things up.

"""
    if consumer_key is None or consumer_secret is None:
        # Case 1: Nothing is provided.
        consumer_key, consumer_secret = _consumer_tokens()
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token, access_token_secret = _access_tokens(auth)
    elif access_token is None or access_token_secret is None:
        # Case 2: Consumer* is provided.
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token, access_token_secret = _access_tokens(auth)

    # Create the directory, configuration file, and skeleton bot script."""
    botdir = "%s/%s" % (os.path.abspath("."), botname)
    _write_bot(botname, botdir, consumer_key, consumer_secret, access_token, access_token_secret)

    print """Your bot \"%s\" is ready to rock! Start it up with the following command:

        python pybot.py start -n %s""" % (botname, botname)


def _bot_exists(botname):
    """
    Utility method to import a bot.
    """
    module = None
    try:
        module = importlib.import_module('%s.%s' % (botname, botname))
    except ImportError as e:
        quit('Unable to import bot "%s.%s": %s' % (botname, botname, str(e)))

    return module

def _consumer_tokens():
    """
    Handles prompting the user with directions for obtaining and inputting
    the OAuth consumer tokens.
    """
    print """First, you'll need to create a Twitter app here:

https://dev.twitter.com/apps/new

This will provide you with "consumer key" and "consumer secret" tokens. When
you have these tokens, make sure you're logged into Twitter with the account
you want to use as your bot, and enter your tokens below.
"""
    consumer_key = None
    consumer_secret = None
    check = "n"
    while check.lower() != "y":
        consumer_key = raw_input("Consumer key: ")
        check = raw_input("Was that correct? [y/n]: ")
    check = "n"
    while check.lower() != "y":
        consumer_secret = raw_input("Consumer secret: ")
        check = raw_input("Was that correct? [y/n]: ")
    return [consumer_key, consumer_secret]

def _access_tokens(oauth):
    """
    Handles prompting the user for creating and inputting the OAuth access tokens.
    """
    print """\nWe'll need to create access tokens specific to your bot. To
do that, please visit the following URL:

%s

Once you have authorized the app with your bot account, you will receive a PIN.
""" % oauth.get_authorization_url()
    check = "n"
    while check.lower() != "y":
        pin = raw_input("Enter your PIN here: ")
        check = raw_input("Was that correct? [y/n]: ")
    token = None
    try:
        token = oauth.get_access_token(verifier = pin)
    except tweepy.error.TweepError as e:
        print 'Unable to authenticate! Check your OAuth credentials and run this script again.'
        quit(e.reason)

    # Everything worked!
    print """Authentication successful! Wait just a minute while the rest of your
bot's internals are set up...
"""
    return token

def _write_bot(botname, botdir, c_key, c_secret, a_token, a_secret):
    """
    Handles creating the bot directory and writing all the components of the bot:
    configuration, models, and the main driver.
    """
    os.mkdir(botdir)
    os.chdir(botdir)
    f = open("./settings.cfg", "w")
    c = """# Sets the configuration options of the bot itself.

[bot]
# Name of the bot. DO NOT CHANGE.
name = %s

# Path to the pid file for the process. DO NOT CHANGE.
pidfile = %s/%s.pid

# Debug level for your bot. To disable logging, set to -1. For a list of levels, see: http://docs.python.org/2/library/logging.html#levels
debug = 10

# Log file. Set this to whatever you like, but make sure you have write permissions.
logfile = %s/%s.log

# Path to the SQLite database. If you're not using a database, leave this blank.
dbfile = sqlite:///%s/sqlite3.db

# Comma-separated list of Twitter handles to avoid. This can be left blank.
blacklist =

# The consumer key and secret come from your Twitter app. The access tokens are
# account-specific and need to be regenerated if you decide to deauthorize and
# re-authorize the app to access your bot's twitter account.

[oauth]
consumer_key = %s
consumer_secret = %s
access_token = %s
access_token_secret = %s""" % (botname, botdir, botname, botdir, botname, botdir, c_key, c_secret, a_token, a_secret)
    f.write(c)
    f.close()
    f = open('./%s.py' % botname, "w")
    script = """import tweepy
import ConfigParser
import sqlalchemy
import sqlalchemy.orm

from lib.bot import Bot
import models


class %s(Bot):

    def __init__(self):
        # Read the configuration file.
        cfg = ConfigParser.SafeConfigParser()
        cfg.read('%s/%s/settings.cfg')

        # Create an OAuth object and initialize the Tweepy API.
        auth = tweepy.OAuthHandler(
            cfg.get('oauth', 'consumer_key'), cfg.get('oauth', 'consumer_secret'))
        auth.set_access_token(
            cfg.get('oauth', 'access_token'), cfg.get('oauth', 'access_token_secret'))
        api = tweepy.API(auth)

        # Set up the database.
        dbfile = cfg.get('bot', 'dbfile')
        if len(dbfile) > 0:
            _engine = sqlalchemy.create_engine(dbfile,
                echo = True if cfg.getint('bot', 'debug') > 10 else False)
            self._session_factory = sqlalchemy.orm.sessionmaker(bind = _engine)
            models.Base.metadata.create_all(_engine)

        # Invoke the parent constructor.
        super(%s, self).__init__(cfg, api)

    def run(self):
        ### Implement this method! ###
        pass
""" % (botname.capitalize(), os.path.dirname(os.path.abspath('.')),
        botname, botname.capitalize())
    f.write(script)
    f.close()
    f = open("./models.py", "w")
    script = """import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# If you want to define any database constructs, you may do so here. Otherwise,
# feel free to leave this file unedited. CHOOSE WISELY."""
    f.write(script)
    f.close()
    open("./__init__.py", "w").close()
