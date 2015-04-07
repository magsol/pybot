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

from abc import ABCMeta, abstractmethod
import fcntl
import logging
import os
import signal

class Bot(object):

    __metaclass__ = ABCMeta

    def __init__(self, cfg, api):
        self.cfg = cfg
        self.name = self.cfg.get('bot', 'name')
        self.api = api
        self.lockfile = None

        # Set up the logger.
        level = self.cfg.getint('bot', 'debug')
        handler = logging.NullHandler()
        if level >= 0:
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(level)
            self.logger.propagate = False
            handler = logging.FileHandler(self.cfg.get('bot', 'logfile'))
            handler.setLevel(level)
            formatter = logging.Formatter("%(asctime)s %(name)s: %(message)s",
                "%b %e %H:%M:%S")
            handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # All set up!
        self.logger.info("Initialized.")

    def __del__(self):
        # Clean up.
        try:
            os.remove(self.cfg.get('bot', 'pidfile'))
            self.logger.info("Terminated.")
        except:
            # Only reason this fails is if the object was instantiated,
            # but then the program crashed before run() could be invoked.
            # In which case, adding an extra error wouldn't help anything.
            pass

    @abstractmethod
    def run(self):
        """
        This is an abstract method that should be implemented in all bot
        subclasses. This is the method that is invoked when the bot is run.

        This method sets up the pid lockfile. It should be invoked before
        the specific bot's run() method is. As long as the bot is started
        through the pybot.py command interface, this will be called.
        """
        self.lockfile = open(self.cfg.get('bot', 'pidfile'), "w")
        fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.lockfile.write("%s" % (os.getpid()))
        self.lockfile.flush()

        # Also set up the signal handler.
        signal.signal(signal.SIGTERM, self._sigterm)

    def _sigterm(self, signum, frame):
        """
        This is invoked when the process is explicitly told to exit.
        """
        self.__del__()

    """
    What follows are some wrapper functions for the Tweepy API object. They
    are named identically for your convenience. These are by no means
    exhaustive, but they do cover the more common use-cases. Check out the
    Tweepy documentation for the full API.
    """

    def me(self):
        """
        Returns the User object associated with the logged-in account. This
        is a good way to test that authentication was successful.
        """
        return self.api.me()

    def home_timeline(self, since_id = None, max_id = None, count = None):
        """
        Returns the timeline for the currently logged-in user.

        Parameters
        ----------
        since_id : integer
            Returns results with an ID greater than (more recent than) the
            specified ID. This is subject to the limits of how many tweets
            can be returned at once.

        max_id : integer
            Returns results with an ID less than (older than) or equal to the
            specified ID.

        count : integer
            Specifies the number of tweets to receive. Must be less than or
            equal to 200. [DEFAULT: 20]
        """
        return self.api.host_timeline(since_id = since_id, max_id = max_id, count = count)

    def update_status(self, status, in_reply_to_status_id = None, lat = None, long = None, place_id = None):
        """
        Posts an update on the timeline of the currently logged-in user.

        Parameters
        ----------
        status : string
            Text of the status update, up to 140 characters in length. URL
            encode as necessary.

        in_reply_to_status_id : integer
            The ID of an existing status that the update is in reply to.

        lat : float
            The latitude of the location this tweet refers to.

        long : float
            The longitude of the location this tweet refers to.

        place_id : hash
            A place in the world. These IDs can be retrieved from
            https://dev.twitter.com/docs/api/1/get/geo/reverse_geocode .
        """
        return self.api.update_status(status = status,
            in_reply_to_status_id = in_reply_to_status_id,
            lat = lat, long = long, place_id = place_id)
