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
__version__='$Revision: 1.6 $'[11:-2]  
  
from AccessControl import ClassSecurityInfo
from OFS.Image import File, cookId
import Globals

from ZchPermissions import View

class Zchfile(File):  
    """ Zch File """  

    security = ClassSecurityInfo()

    meta_type = "Zch File"
    
    security.declarePrivate('__init__')
    def __init__(self,file=None):        
        if file:
            id, title = cookId(None,None,file)
            File.__init__(self,id,title,file)
  
    security.declareProtected(View, 'icon')
    def icon(self):
        return 'misc_/Zch/Zchfile_img'

    security.declareProtected(View, 'file_path')
    def file_path(self):
        return self.relative_path() + '/' + self.file_name()

    security.declareProtected(View, 'file_name')
    def file_name(self):
        return self.getId()
  
    security.declareProtected(View, 'file_bytes')
    def file_bytes(self):  
        return self.get_size()
  
    security.declareProtected(View, 'file_kbytes')
    def file_kbytes(self):  
        return int(self.get_size()/1024)  
  
Globals.InitializeClass(Zchfile)
