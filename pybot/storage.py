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
import os
import pickle

class PickleStorage(object):
    """
    Base storage class. Uses Python's pickle library.

    Create a new storage class and override "read(f)" and "write(f)"
    to use a different adapter, e.g. text files, databases, etc.
    """

    def read(self, f):
        """
        Read method.

        Parameters
        ----------
        f : string
            Path to the .pkl file on disk.

        Returns
        -------
        PyBot state dictionary if the file exists; None otherwise.
        """
        if not os.path.exists(f):
            logging.info("%s does not exist." % f)
            return None

        logging.info("Retrieving state from %s." % f)
        fp = open(f, "rb")
        state = pickle.load(fp)
        fp.close()
        return state

    def write(self, f, s):
        """
        Write method.

        Parameters
        ----------
        f : string
            Path to the state file.
        s : dictionary
            Dict containing this PyBot's current state.
        """
        if os.path.exists(f):
            logging.info("Overwriting %s." % f)
        else:
            logging.info("Creating %s." % f)
        fp = open(f, "wb")
        pickle.dump(s, fp)
        fp.close()
