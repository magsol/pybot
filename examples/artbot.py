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

import datetime

from stravalib import Client
from stravalib import unithelper

class artbot(PyBot):

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

        self.config['api_key'] = 'your_api_key'
        self.config['api_secret'] = 'your_api_secret'
        self.config['access_key'] = 'your_access_key'
        self.config['access_secret'] = 'your_access_secret'

        #############################
        #                           #
        #   Other config options    #
        #                           #
        # Fill these in if you want #
        #   or otherwise need to.   #
        #                           #
        #############################

        self.config['bot_name'] = 'artbot'

        self.config['strava_access_token'] = 'your_strava_token'
        self.config['update_day'] = 0
        self.config['update_hour'] = 13
        self.config['update_minute'] = 13
        self.config['tweet_interval'] = self._compute_interval

        # Create the Strava client.
        self.client = Client(access_token = self.config['strava_access_token'])

    def on_tweet(self):
        # First, pull in the stats from Strava.
        current = datetime.datetime.now()
        last_week = current + datetime.timedelta(weeks = -1)
        after = datetime.datetime(last_week.year, last_week.month, last_week.day)
        activities = self.client.get_activities(after = after)

        # Second, filter by activity type and time frame.
        lf = [a for a in activities if a.start_date_local.day != current.day]
        num_activities = len(lf)
        l = [a.id for a in lf if a.type == 'Run']

        # Third, tabulate up the stats for mileage and calories.
        mileage = 0.0
        calories = 0.0
        for activity_id in l:
            activity = self.client.get_activity(activity_id)
            distance = unithelper.miles(activity.distance)
            mileage += round(distance.num, 2)  # Rounds to 2 sig figs.
            calories += activity.calories
        calories = int(calories)

        # Finally, use the stats to craft a tweet. This can be any format
        # you want, but I'll use the example one from the start of the post.
        tweet = "My training last week: {:d} workouts for {:.2f} miles and {:d} calories burned.".format(num_activities, mileage, calories)
        self.update_status(tweet)

    def _compute_interval(self):
        """
        This is a little more sophisticated than the method in the original
        blog post. This is to provide for *exactly* specifying when we want
        a post to be made, down to the minute.
        """
        now = datetime.datetime.now()
        target = datetime.datetime(year = now.year, month = now.month, day = now.day,
            hour = self.config['update_hour'], minute = self.config['update_minute'])
        days_ahead = self.config['update_day'] - now.weekday()
        if (days_ahead < 0) or (days_ahead == 0 and (target - now).days < 0):
            days_ahead += 7
        td = target + datetime.timedelta(days = days_ahead)
        interval = int((td - datetime.datetime.now()).total_seconds())
        return interval

if __name__ == "__main__":
    bot = artbot()
    bot.run()
