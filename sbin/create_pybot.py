#!/usr/bin/env python
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

import argparse
import os
import os.path
import tweepy
import tweepy.error

def valid_name(name):
    if not name.isalnum() or name.find(" ") > -1 or not name[0].isalpha() or name.lower() == "lib":
        raise argparse.ArgumentTypeError("""\"{}\" is an invalid bot name. It
must not contain spaces, non-alphanumeric characters, or start with a number.
""".format(name))
    return name

def _consumer_tokens():
    """
    Handles prompting the user with directions for obtaining and inputting
    the OAuth consumer tokens.
    """
    print("""First, you'll need to create a Twitter app here:

https://dev.twitter.com/apps/new

This will provide you with "consumer key" and "consumer secret" tokens. When
you have these tokens, make sure you're logged into Twitter with the account
you want to use as your bot, and enter your tokens below.
""")
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
    print("""\nWe'll need to create access tokens specific to your bot. To
do that, please visit the following URL:

{}

Once you have authorized the app with your bot account, you will receive a PIN.
""".format(oauth.get_authorization_url()))

    check = "n"
    while check.lower() != "y":
        pin = raw_input("Enter your PIN here: ")
        check = raw_input("Was that correct? [y/n]: ")
    token = None
    try:
        token = oauth.get_access_token(verifier = pin)
    except tweepy.error.TweepError as e:
        print('Unable to authenticate! Check your OAuth credentials and run this script again.')
        quit(e.reason)

    # Everything worked!
    print("""Authentication successful! Wait just a minute while the rest of your
bot's internals are set up...
""")
    return token

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Welcome to PyBot!",
        epilog = "lol tw33tz", add_help = "How to use",
        prog = "create_pybot.py")
    parser.add_argument("-n", "--name", required = True, type = valid_name,
        help = "Unique identifier for the new bot (REQUIRED).")
    parser.add_argument("--api_key", default = None,
        help = "OAuth Consumer Key. This can be used across multiple bots.")
    parser.add_argument("--api_secret", default = None,
        help = "OAuth Consumer Secret. This can be used across multiple bots.")
    parser.add_argument("--access_key", default = None,
        help = "Access token. Unique to a specific bot.")
    parser.add_argument("--access_secret", default = None,
        help = "Access token secret. Unique to a specific bot.")

    args = vars(parser.parse_args())

    print("""
*********************
* Welcome to PyBot! *
*********************

This script will help you set things up.

""")
    botname = args['name']
    consumer_key = args['api_key']
    consumer_secret = args['api_secret']
    access_token = args['access_key']
    access_token_secret = args['access_secret']

    if consumer_key is None or consumer_secret is None:
        # Case 1: Nothing is provided.
        consumer_key, consumer_secret = _consumer_tokens()
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token, access_token_secret = _access_tokens(auth)
    elif access_token is None or access_token_secret is None:
        # Case 2: Consumer* is provided.
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token, access_token_secret = _access_tokens(auth)

    # Create a couple of paths:
    # 1) To the root pybot directory, where this bot will reside
    # 2) To the pybot subdirectory, where the skeleton template is
    root = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
    tfile = os.path.join(os.path.join(root, "pybot"), "template.py")

    # Grab all the contents of the template.
    f = open(tfile, "r")
    template = f.read()
    f.close()

    # Replace all instances of "PyBotTemplate" with the bot's name.
    template = template.replace("PyBotTemplate", botname)

    # Also, add in all the OAuth stuff.
    ck_idx = template.find("''")
    template = template[:ck_idx + 1] + "%s" % consumer_key + template[ck_idx + 1:]
    cs_idx = template.find("''")
    template = template[:cs_idx + 1] + "%s" % consumer_secret + template[cs_idx + 1:]
    at_idx = template.find("''")
    template = template[:at_idx + 1] + "%s" % access_token + template[at_idx + 1:]
    as_idx = template.find("''")
    template = template[:as_idx + 1] + "%s" % access_token_secret + template[as_idx + 1:]

    # Write the botfile!
    f = open(os.path.join(root, "{}.py".format(botname.lower())), "w")
    f.write(template)
    f.close()

    print("""Your bot \"{}\" is ready to rock! Start it up with the following command:

        python {}.py
    """.format(botname, botname.lower()))
