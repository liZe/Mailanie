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
import gtk

from mailanie import config

_license = _("""\
Mailanie is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 3 of the License, or (at your option)
any later version.

Mailanie is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with Mailanie; if not, write to the Free Software Foundation, Inc., 51
Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.""")

_authors = ("Guillaume Ayoub <guillaume.ayoub@kozea.fr>",)

class About(gtk.AboutDialog):
    def __init__(self, *args):
        super(About, self).__init__()

        self.set_name("Mailanie")
        self.set_version(config.get("mailanie", "version"))
        self.set_comments(_("Small and Cute Mailbox Explorer"))
        self.set_copyright(u"Copyright \u00a9 2009 Guillaume Ayoub")
        self.set_license(_license)
        self.set_authors(_authors)
        self.connect("response", lambda widget, data: self.destroy())
        # Note for translators:
        # Please translate "translator-credits" in
        # "Your Name (Nick) <your.adress@something.org>"
        self.set_translator_credits(_("translator-credits"))
        self.show_all()

        self.set_website("http://www.mailanie.org/")
