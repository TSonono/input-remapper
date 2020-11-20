#!/usr/bin/python3
# -*- coding: utf-8 -*-
# key-mapper - GUI for device specific keyboard mappings
# Copyright (C) 2020 sezanzeb <proxima@hip70890b.de>
#
# This file is part of key-mapper.
#
# key-mapper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# key-mapper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with key-mapper.  If not, see <https://www.gnu.org/licenses/>.


"""Starts injecting keycodes based on the configuration."""


from dbus import service
import dbus.mainloop.glib

from keymapper.logger import logger
from keymapper.config import config
from keymapper.injector import KeycodeInjector
from keymapper.mapping import Mapping


class Daemon(service.Object):
    def __init__(self, *args, **kwargs):
        """Constructs the daemon. You still need to run the GLib mainloop."""
        self.injectors = {}
        for device, preset in config.iterate_autoload_presets():
            mapping = Mapping()
            mapping.load(device, preset)
            self.injectors[device] = KeycodeInjector(device, mapping)

        super().__init__(*args, **kwargs)

    @dbus.service.method(
        'com.keymapper.control',
        in_signature='s'
    )
    def stop_injecting(self, device):
        """Stop injecting the mapping for a single device."""
        if self.injectors.get(device) is None:
            logger.error('No injector running for device %s', device)
            return

        self.injectors[device].stop_injecting()

    # TODO if ss is the correct signature for multiple parameters, add an
    #  example to https://gitlab.freedesktop.org/dbus/dbus-python/-/blob/master/doc/tutorial.txt # noqa
    @dbus.service.method(
        'com.keymapper.control',
        in_signature='ss'
    )
    def start_injecting(self, device, preset):
        """Start injecting the preset for the device."""
        if self.injectors.get(device) is not None:
            self.injectors[device].stop_injecting()

        mapping = Mapping()
        mapping.load(device, preset)
        self.injectors[device] = KeycodeInjector(device, mapping)

    @dbus.service.method(
        'com.keymapper.control'
    )
    def stop(self):
        """Properly stop the daemon."""
        for injector in self.injectors.values():
            injector.stop_injecting()