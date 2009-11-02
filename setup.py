#!/usr/bin/python

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
import sys
import shutil
from distutils.core import setup, Command
from distutils.dir_util import remove_tree



class Clean(Command):
    description = "clean up package temporary files"
    user_options = []

    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        if os.path.isdir(os.path.join("po", "mo")):
            remove_tree(os.path.join("po", "mo"))

        if os.path.isfile(os.path.join("po", "mailanie.pot")):
            os.unlink(os.path.join("po", "mailanie.pot"))

        if os.path.isfile("mailanie.desktop"):
            os.unlink("mailanie.desktop")

        path = os.path.abspath(os.path.dirname(__file__))
        for pathname, _, files in os.walk(path):
            for filename in filter(self._should_remove, files):
                os.unlink(os.path.join(pathname, filename))

        for folder in ("build", "dist"):
            if os.path.isdir(os.path.join(path, folder)):
                shutil.rmtree(os.path.join(path, folder))

        if os.path.isfile(os.path.join(path, "MANIFEST")):
            os.unlink(os.path.join(path, "MANIFEST"))

    @staticmethod
    def _should_remove(filename):
        return (os.path.splitext(filename)[1] == ".pyc" or
                os.path.splitext(filename)[1] == ".pyo" or
                filename.endswith("~") or
                (filename.startswith("#") and filename.endswith("#")))
    


class I18n(Command):
    description = "build i18n files"
    user_options = []
    
    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        os.system("cd po && intltool-update --pot --gettext-package=mailanie")
        po_files = filter(lambda file: file.endswith(".po"), os.listdir("po"))
        for po_file in po_files:
            lang = os.path.splitext(po_file)[0]
            mo_folder = os.path.join("po", "mo", lang, "LC_MESSAGES")
            if not os.path.isdir(mo_folder):
                os.makedirs(mo_folder)
            os.system("msgfmt -o %s %s" % (
                    os.path.join(mo_folder, "mailanie.mo"),
                    os.path.join("po", po_file)))
        os.system("intltool-merge -d po mailanie.desktop.in mailanie.desktop")



data_files = [(os.path.join(sys.prefix, "share", "pixmaps"),
               [os.path.join("mailanie", "ui", "mailanie.svg")])]

if os.path.isdir(os.path.join("po", "mo")):
    data_files.extend([
            (os.path.join(sys.prefix, "share", "locale", lang, "LC_MESSAGES"),
             [os.path.join("po", "mo", lang, "LC_MESSAGES", "mailanie.mo")])
            for lang in os.listdir(os.path.join("po", "mo"))])

if os.path.isfile("mailanie.desktop"):
    data_files.extend([
            (os.path.join(sys.prefix, "share", "applications"),
             ["mailanie.desktop"])])

setup(
    name="Mailanie",
    version="0.1",
    description="Mailanie, Cute Mailbox Explorator",
    author="Guillaume Ayoub",
    author_email="guillaume.ayoub@kozea.fr",
    url="http://www.mailanie.org/",
    license="GNU GPL v3",
    requires=["pynotify"],
    packages=["mailanie", "mailanie.ui"],
    scripts=[os.path.join("bin", "mailanie")],
    package_data={"mailanie.ui": ["mailanie.svg"]},
    data_files=data_files,
    cmdclass={"clean": Clean, "i18n": I18n})
