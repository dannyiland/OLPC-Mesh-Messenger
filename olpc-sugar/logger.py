# Copyright (C) 2007 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""Logging service setup.

STABLE.
"""

import errno
import sys
import os
import logging

# Let's keep this self contained so that it can be easily
# pasted in external sugar service like the datastore.

def get_logs_dir():
    profile = os.environ.get('SUGAR_PROFILE', 'default')
    logs_dir = os.environ.get('SUGAR_LOGS_DIR',
                              os.path.join(os.path.expanduser('~'),
                                           '.sugar', profile, 'logs'))
    return logs_dir

def set_level(level):
    levels = { 'error'   : logging.ERROR,
               'warning' : logging.WARNING,
               'debug'   : logging.DEBUG,
               'info'    : logging.INFO }
    if levels.has_key(level):
        logging.getLogger('').setLevel(levels[level])

# pylint: disable-msg=E1101,F0401
def _except_hook(exctype, value, traceback):
    # Attempt to provide verbose IPython tracebacks.
    # Importing IPython is slow, so we import it lazily.
    try:
        from IPython.ultraTB import AutoFormattedTB
        sys.excepthook = AutoFormattedTB(mode='Verbose', color_scheme='NoColor')
    except ImportError:
        sys.excepthook = sys.__excepthook__

    sys.excepthook(exctype, value, traceback)
        
def start(log_filename=None):
    # remove existing handlers, or logging.basicConfig() won't have no effect.
    root_logger = logging.getLogger('')
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    class SafeLogWrapper(object):
        """Small file-like wrapper to gracefully handle ENOSPC errors when
        logging."""

        def __init__(self, stream):
            self._stream = stream

        def write(self, s):
            try:
                self._stream.write(s)
            except IOError, e:
                # gracefully deal w/ disk full
                if e.errno != errno.ENOSPC:
                    raise e

        def flush(self):
            try:
                self._stream.flush()
            except IOError, e:
                # gracefully deal w/ disk full
                if e.errno != errno.ENOSPC:
                    raise e

    logging.basicConfig(level=logging.WARNING,
            format="%(created)f %(levelname)s %(name)s: %(message)s",
                        stream=SafeLogWrapper(sys.stderr))

    if os.environ.has_key('SUGAR_LOGGER_LEVEL'):
        set_level(os.environ['SUGAR_LOGGER_LEVEL'])

    if log_filename:
        try:
            log_path = os.path.join(get_logs_dir(), log_filename + '.log')

            log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT)
            os.dup2(log_fd, sys.stdout.fileno())
            os.dup2(log_fd, sys.stderr.fileno())
            os.close(log_fd)

            sys.stdout = SafeLogWrapper(sys.stdout)
            sys.stderr = SafeLogWrapper(sys.stderr)
        except OSError, e:
            # if we're out of space, just continue
            if e.errno != errno.ENOSPC:
                raise e

    sys.excepthook = _except_hook

