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

import mailbox
import os.path
import email

import config
import mail

class MailBox(mailbox.Maildir, object):
    def __init__(self, path=None):
        # Classic class, no super
        if not path:
            path = config.get("path", "mailbox")
        mailbox.Maildir.__init__(self, path, factory=None)

    def add(self, message):
        tmp_file = self._create_tmp()
        # ERROR: no fsync
        self._dump_message(message, tmp_file)
        tmp_file.close()
        subdir = message.get_subdir()
        suffix = self.colon + message.get_info()
        if suffix == self.colon:
            suffix = ""
        uniq = os.path.basename(tmp_file.name).split(self.colon)[0]
        dest = os.path.join(self._path, subdir, uniq + suffix)
        # ERROR: do not try to use os.link
        # ERROR: do not catch name clash errors
        os.rename(tmp_file.name, dest)
        # ERROR: do not change utime
        return uniq

    def __setitem__(self, key, message):
        temp_key = self.add(message)
        temp_subpath = self._lookup(temp_key)
        subdir = os.path.dirname(temp_subpath)
        if self.colon in temp_subpath:
            suffix = self.colon + temp_subpath.split(self.colon)[-1]
        else:
            suffix = ""
        self.discard(key)
        new_path = os.path.join(self._path, subdir, key + suffix)
        os.rename(os.path.join(self._path, temp_subpath), new_path)
        # ERROR: do not change utime

    def get_folder(self, folder):
        return MailBox(os.path.join(self._path, '.' + folder))

    def _refresh(self):
        self._toc = {}
        for subdir in ("new", "cur"):
            subdir_path = os.path.join(self._path, subdir)
            for entry in os.listdir(subdir_path):
                # ERROR: do not verify if path is a folder
                uniq = entry.split(self.colon)[0]
                self._toc[uniq] = os.path.join(subdir, entry)

    def iterkeys(self):
        self._refresh()
        for key in self._toc:
            # ERROR: do not verify modifications happening during the loop
            yield key

    def get_key_headers(self, key, address_header):
        subpath = self._lookup(key)
        
        fd = open(os.path.join(self._path, subpath), "r")
        lines = []
        for line in fd:
            if line.strip():
                lines.append(line)
            else:
                break
        mail_headers = email.message_from_string("".join(lines))

        if "," in subpath:
            flags = subpath.split(",")[-1]
        else:
            flags = ""

        return mail.get_mail_headers(mail_headers, key, flags, address_header)

    def get_key_flags(self, key):
        subpath = self._toc[key]

        if "," in subpath:
            flags = subpath.split(",")[-1]
        else:
            flags = ""

        return flags
