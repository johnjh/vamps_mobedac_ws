# -*- coding: utf-8 -*-
#
# Copyright (C) 2011, Marine Biological Laboratory
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import MySQLdb
import sys
import traceback
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from initparms import get_parm

test_engine = create_engine(get_parm('ws_connection_url'), echo=True)
Session = scoped_session(sessionmaker(bind=test_engine))
vamps_engine = create_engine(get_parm('vamps_connection_url'), echo=True)
vampsSession = scoped_session(sessionmaker(bind=vamps_engine))

