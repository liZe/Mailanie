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
import email
import mailbox
import tempfile
import time

import mailanie
import config
import smtp

def get_mail_headers(mail, key, flags, address_header):
    subject = decode_mail_header(mail, "Subject")
    try:
        date = email.utils.mktime_tz(
            email.utils.parsedate_tz(decode_mail_header(mail, "Date")))
    except:
        date = None

    addresses = []
    for address in mail.get_all(address_header, []):
        for address_split in address.split(","):
            address_parse = email.utils.parseaddr(address_split.strip())
            addresses.append(list(decode(string) for string in address_parse))

    copies = []
    for copie in mail.get_all("Cc", []):
        for copie_split in copie.split(","):
            copie_parse = email.utils.parseaddr(copie_split.strip())
            copies.append(list(decode(string) for string in copie_parse))

    return MailHeaders(key, subject, addresses, date, flags, copies)

def decode_mail_header(mail, header_key):
    header = mail[header_key]
    if header:
        return decode(header)
    else:
        return u""

def decode(string):
    values = email.header.decode_header(string)
    return u" ".join(value[0].decode(value[1] or "latin-1")
                     for value in values)



class MailHeaders(object):
    def __init__(self, key, subject, addresses, date, flags, copies):
        self._key = key
        self._subject = subject
        self._address = addresses
        self._date = date
        self._flags = flags
        self._copie = copies
        self._mail = None

    def get_mail(self, mailbox):
        if not self._mail:
            message = mailbox.get_message(self.get_key())
            message.set_flags(self.get_flags())
            
            self._mail = ReadMail(message, self.get_key())
        return self._mail
        
    def get_key(self):
        return self._key

    def get_header(self, name):
        if name in ("Subject", "Address", "Date", "Copie"):
            return getattr(self, "_%s" % name.lower())

    def get_info(self):
        return "2,%s" % self._flags

    def get_flags(self):
        return self._flags

    def add_flag(self, name):
        self._flags = "".join(sorted(set(self._flags + name)))
        if self._mail:
            self._mail.set_flags(self._flags)

    def set_flags(self, flags):
        self._flags = "".join(sorted(set(flags)))
        if self._mail:
            self._mail.set_flags(self._flags)

    def remove_flag(self, name):
        self._flags = self._flags.replace(name, "")
        if self._mail:
            self._mail.set_flags(self._flags)

    def clean(self):
        self._mail = None



class Mail(mailbox.MaildirMessage, object):
    def __init__(self, message="", key="", address_header="From"):
        # Classic class, no super
        mailbox.MaildirMessage.__init__(self, message)

        self._address_header = address_header
        self.message = message
        self.key = key

        self._loaded = False

    def get_headers(self):
        return get_mail_headers(
            self, self.key, self.get_flags(), self._address_header)

    def load(self, cache_path=None):
        if self._loaded:
            return

        self.label = self.decode("Subject") or "[%s]" % _("Untitled")
        
        if not cache_path:
            path = config.get("path", "part")
            folder = self.key
            cache_path = os.path.join(path, folder)

        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        self._loaded = True

    def decode(self, key):
        return decode_mail_header(self, key)



class ReadMail(Mail):
    pass



class WriteMail(Mail):
    def send(self):
        addresses = []
        for header_name in ("To", "Cc", "Bcc"):
            for header in self.get_all(header_name, []):
                addresses.append(email.utils.parseaddr(decode(header))[1])

        del self["Bcc"]

        name, address = email.utils.parseaddr(u"Guillaume Ayoub <guillaume.ayoub@kozea.fr>".encode("utf-8"))
        if name:
            name = email.header.Header(name, "utf-8").encode()
            self["From"] = email.utils.formataddr((name, address))
        else:
            self["From"] = address

        self["Date"] = email.utils.formatdate(time.time(), True)
        self["X-Mailer"] = "Mailanie %s" % config.get("mailanie", "version")

        server = config.get("smtp", "server")
        port = config.getint("smtp", "port")
        if config.getboolean("smtp", "ssl"):
            client = smtp.SMTP_SSL(server, port)
        else:
            client = smtp.SMTP(server, port)

        login = config.get("smtp", "login")
        if login:
            password = config.get("smtp", "password")
            client.login(login, password)

        name = config.get("smtp", "name")
        address = config.get("smtp", "address")
        if name:
            sender = "%s <%s>" % (name, address)
        else:
            sender = address
        client.sendmail(sender, addresses, self.as_string())

        sent_folder = mailanie.mailbox.get_folder(config.get("mailbox", "sent"))
        sent_folder.add(self)
