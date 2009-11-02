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

import smtplib

class SMTP(smtplib.SMTP):
    pass

class SMTP_SSL(smtplib.SMTP_SSL):
    pass
