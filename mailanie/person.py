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

class Person(dict):
    def __init__(self, filename=None):
        super(Person, self).__init__()

        # TODO: manage None filename
        self._filename = filename

        with open(self._filename, "r") as fd:
            self._parse(fd)

    def _parse(self, fd):
        for line in fd:
            if line.startswith("N:"):
                self["n"] = line[2:].strip()
            if line.startswith("FN:"):
                self["fn"] = line[3:].strip()

    def write(self):
        text = u"BEGIN:VCARD\nVERSION:3.0\n"

        if "n" in self:
            text += "N:%s\n" % self["n"]
        if "fn" in self:
            text += "FN:%s\n" % self["fn"]

        text += "END:VCARD"

        with open(self._filename, "w") as fd:
            fd.write(text)
