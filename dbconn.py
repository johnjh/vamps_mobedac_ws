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


test_engine = create_engine('mysql://john:oweneego@localhost/test', echo=True)
Session = scoped_session(sessionmaker(bind=test_engine))
vamps_engine = create_engine('mysql://vamps_r:3l35Ant@vampsdev.mbl.edu/vamps', echo=True)
vampsSession = scoped_session(sessionmaker(bind=vamps_engine))

