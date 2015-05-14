############################################################################## 
# 
# This software is released under the Zope Public License (ZPL) Version 1.0
#
# Copyright (c) Digital Creations. All rights reserved. 
# Portions Copyright (c) 1999 by Butch Landingin.
# Portions Copyright (c) 2000-2001 by Chris Withers.
# Portions Copyright (c) 2002 by KANDA Hiroshi.
# Portions Copyright (c) 2004-2005 by Hajime Nakagami
# 
############################################################################## 
__version__='$Revision: 1.12 $'[11:-2]  
import Globals
from AccessControl import ClassSecurityInfo

from ZchPermissions import View, ManageZch
from Posting import Posting


# Comment has to be in this file to stop import infinite recursion
class Comment(Posting):     
    """ Kindof small, isn't it ;-)"""     
    security = ClassSecurityInfo()

    meta_type  ='Comment'     
    icon       ='misc_/Zch/comment_img'

    security.declarePrivate('__init__')
    def __init__(self, id, parent_id):     
        Posting.__init__(self, id)
        self.parent_id = int(parent_id)
     
    security.declareProtected(View, 'relative_path')
    def relative_path(self):
        return str(self.parent_id) + '/' + self.id

    security.declareProtected(ManageZch, 'postingValues')
    def postingValues(self):     
        """ return child items """     
        return None

Globals.InitializeClass(Comment)


