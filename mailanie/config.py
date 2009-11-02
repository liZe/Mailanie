# Mailanie - Cute Mailbox Explorator
# Copyright 2009 Guillaume Ayoub <guillaume.ayoub@kozea.fr>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

# Mailanie is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Mailanie.  If not, see <http://www.gnu.org/licenses/>.

import os
from ConfigParser import RawConfigParser as ConfigParser

_config = ConfigParser()
get = _config.get
set = _config.set
getboolean = _config.getboolean
getint = _config.getint
getfloat = _config.getfloat
write = _config.write
options = _config.options
sections = _config.sections
options = _config.options

_path = os.path.join(os.path.expanduser("~"), ".config", "mailanie")
_file = os.path.join(_path, "config")

def write():
    if not os.path.isdir(_path):
        os.makedirs(_path)
    with open(_file, "w") as fd:
        _config.write(fd)

def init():
    init_config = {
        "mailanie": {
            "version": "0.1",
            },
        "window": {
            "size": "600 400",
            },
        "path": {
            "mailbox": "file://%s" % os.path.join(_path, "mailbox"),
            "folder": "file://%s" % os.path.join(_path, "folders"),
            "part": "file://%s" % os.path.join(_path, "parts"),
            "addressbook": "file://%s" % os.path.join(_path, "addressbook"),
            },
        "mailbox": {
            "draft": "none",
            "sent": "none",
            },
        "smtp": {
            "ssl": "False",
            "port": "25",
            "server": "",
            "login": "",
            "password": "",
            "name": "",
            "address": "",
            }
        }

    for section, values in init_config.iteritems():
        _config.add_section(section)
        for key, value in values.iteritems():
            _config.set(section, key, value)

    _config.read(_file)
