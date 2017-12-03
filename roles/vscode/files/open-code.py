# -*- coding: UTF-8 -*-
# This example is contributed by Martin Enlund
# Example modified for Code
# Shortcuts Provider was inspired by captain nemo extension

from gettext import gettext, textdomain
from subprocess import PIPE, call
from urllib import unquote
from urlparse import urlparse

from gi import require_version
require_version('Gtk', '3.0')
require_version('Nautilus', '3.0')
from gi.repository import Gio, GObject, Gtk, Nautilus


TERMINAL = "code"
TILIX_KEYBINDINGS = "com.microsoft.Code.Keybindings"
GSETTINGS_OPEN_TERMINAL = "nautilus-open"
REMOTE_URI_SCHEME = ['ftp', 'sftp']
textdomain("code")
_ = gettext


def open_terminal_in_file(filename):
  if filename:
    call('{0} -w "{1}" &'.format(TERMINAL, filename), shell=True)
  else:
    call("{0} &".format(TERMINAL), shell=True)


class OpenCodeShortcutProvider(GObject.GObject,
                                Nautilus.LocationWidgetProvider):

  def __init__(self):
    source = Gio.SettingsSchemaSource.get_default()
    if source.lookup(TILIX_KEYBINDINGS, True):
      self._gsettings = Gio.Settings.new(TILIX_KEYBINDINGS)
      self._gsettings.connect("changed", self._bind_shortcut)
      self._create_accel_group()
    self._window = None
    self._uri = None

  def _create_accel_group(self):
    self._accel_group = Gtk.AccelGroup()
    shortcut = self._gsettings.get_string(GSETTINGS_OPEN_TERMINAL)
    key, mod = Gtk.accelerator_parse(shortcut)
    self._accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE,
                              self._open_terminal)

  def _bind_shortcut(self, gsettings, key):
    if key == GSETTINGS_OPEN_TERMINAL:
      self._accel_group.disconnect(self._open_terminal)
      self._create_accel_group()

  def _open_terminal(self, *args):
    filename = unquote(self._uri[7:])
    open_terminal_in_file(filename)

  def get_widget(self, uri, window):
    self._uri = uri
    if self._window:
      self._window.remove_accel_group(self._accel_group)
    if self._gsettings:
      window.add_accel_group(self._accel_group)
    self._window = window
    return None


class OpenCodeExtension(GObject.GObject, Nautilus.MenuProvider):

  def _open_terminal(self, file_):
    if file_.get_uri_scheme() in REMOTE_URI_SCHEME:
      result = urlparse(file_.get_uri())
      if result.username:
        value = 'ssh -t {0}@{1}'.format(result.username,
                                        result.hostname)
      else:
        value = 'ssh -t {0}'.format(result.hostname)
      if result.port:
        value = "{0} -p {1}".format(value, result.port)
      if file_.is_directory():
        value = '{0} cd "{1}" ; $SHELL'.format(value, result.path)

      call('{0} -e "{1}" &'.format(TERMINAL, value), shell=True)
    else:
      filename = Gio.File.new_for_uri(file_.get_uri()).get_path()
      open_terminal_in_file(filename)

  def _menu_activate_cb(self, menu, file_):
    self._open_terminal(file_)

  def _menu_background_activate_cb(self, menu, file_):
    self._open_terminal(file_)

  def get_file_items(self, window, files):
    if len(files) != 1:
      return
    items = []
    file_ = files[0]
    print("Handling file: ", file_.get_uri())
    print("file scheme: ", file_.get_uri_scheme())

    if file_.is_directory():

      if file_.get_uri_scheme() in REMOTE_URI_SCHEME:
        uri = file_.get_uri().decode('utf-8')
        item = Nautilus.MenuItem(name='NautilusPython::open_remote_item',
                                 label=_(u'Open Remote Code'),
                                 tip=_(u'Open Remote Code '
                                       'In').format(uri))
        item.connect('activate', self._menu_activate_cb, file_)
        items.append(item)

      filename = file_.get_name().decode('utf-8')
      item = Nautilus.MenuItem(name='NautilusPython::open_file_item',
                               label=_(u'Open In Code'),
                               tip=_(u'Open Code In {}').format(filename))
      item.connect('activate', self._menu_activate_cb, file_)
      items.append(item)

    return items

  def get_background_items(self, window, file_):
    items = []
    if file_.get_uri_scheme() in REMOTE_URI_SCHEME:
      item = Nautilus.MenuItem(name='NautilusPython::open_bg_remote_item',
                               label=_(u'Open Remote Code Here'),
                               tip=_(u'Open Remote Code In This Directory'))
      item.connect('activate', self._menu_activate_cb, file_)
      items.append(item)

    item = Nautilus.MenuItem(name='NautilusPython::open_bg_file_item',
                             label=_(u'Open Code Here'),
                             tip=_(u'Open Code In This Directory'))
    item.connect('activate', self._menu_background_activate_cb, file_)
    items.append(item)
    return items
