""" btu.hooks.py """

from . import __version__ as app_version

# pylint: disable=invalid-name
app_name = "btu"
app_title = "Background Tasks Unleashed"
app_publisher = "Datahenge LLC"
app_description = "Background Tasks Unleashed"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "brian@datahenge.com"
app_license = "MIT"

# Hooks is sometimes executed by Workers, which have no idea about Web Server's global state.
# Code running here will not know about Frappe Flags.

"""
Regarding extending 'bootinfo'

This doesn't behave like you'd expect.  The code will trigger on Webpage logins or refreshes.
The bootinfo code does -not- trigger on Web Server initialization.
It is a poorly-named feature.

# extend_bootinfo = "btu.boot.boot_session"
"""
