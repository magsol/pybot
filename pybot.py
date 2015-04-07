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
import lib.bootstrap

def valid_name(name):
    if not name.isalnum() or name.find(" ") > -1 or not name[0].isalpha() or name.lower() == "lib":
        raise argparse.ArgumentTypeError("""\"%s\" is an invalid bot name. It
must not contain spaces, non-alphanumeric characters, or start with a number.
""" % name)
    return name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Welcome to PyBot!",
        epilog = "lol tw33tz", add_help = "How to use",
        prog = "python create.py")
    subparsers = parser.add_subparsers(dest = "sub_name")

    # "create" command
    create_p = subparsers.add_parser("create")
    create_p.add_argument("-n", "--name", required = True, type = valid_name,
        help = "Unique identifier for the new bot (REQUIRED).")
    create_p.add_argument("--consumer_key", default = None,
        help = "OAuth Consumer Key. This can be used across multiple bots.")
    create_p.add_argument("--consumer_secret", default = None,
        help = "OAuth Consumer Secret. This can be used across multiple bots.")
    create_p.add_argument("--access_token", default = None,
        help = "Access token. Unique to a specific bot.")
    create_p.add_argument("--access_token_secret", default = None,
        help = "Access token secret. Unique to a specific bot.")

    # "start" command
    start_p = subparsers.add_parser("start")
    start_p.add_argument("-n", "--name", required = True,
        help = "Name of the bot to start.")

    # "stop" command
    stop_p = subparsers.add_parser("stop")
    stop_p.add_argument("-n", "--name", required = True,
        help = "Name of the bot to halt.")

    # "list" command
    status_p = subparsers.add_parser("list",
        help = "List all installed bots, plus some helpful info.")

    args = vars(parser.parse_args())
    if args["sub_name"] == "create":
        lib.bootstrap.create(args["name"], args["consumer_key"], args["consumer_secret"],
            args["access_token"], args["access_token_secret"])
    elif args["sub_name"] == "start":
        lib.bootstrap.start(args["name"])
    elif args["sub_name"] == "stop":
        lib.bootstrap.stop(args["name"])
    elif args["sub_name"] == "list":
        lib.bootstrap.list()
    else:
        print 'Command "%s" not recognized.' % args['sub_name']
