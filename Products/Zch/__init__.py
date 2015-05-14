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
__version__='$Revision: 1.13 $'[11:-2]  
import os

from Globals import HTMLFile, package_home
try:
    from App.ImageFile import ImageFile
except:
    from ImageFile import ImageFile  

from Products.Zch.ZchSite import ZchSite
from Products.Zch.ZchSite import __doc__

#import ZCTextIndex constructors...
try:
    from Products.ZCTextIndex.PipelineFactory import element_factory

    def getElementGroups(self):
        return element_factory.getFactoryGroups()

    def getElementNames(self, group):
        return element_factory.getFactoryNames(group)

except:
    pass

def list_skelton(self):
    skelton = []
    for item in os.listdir(os.path.join(package_home(globals()), 'skelton')):
        if item == 'CVS':
            continue
        skelton.append(item)
    return skelton

# Register the Zch Site class
def initialize(context):

        context.registerClass(
            ZchSite,
            meta_type='Zch Site',
            constructors = (
                manage_addZchForm,
                manage_addZch,
                getElementGroups, getElementNames, 
                list_skelton
            )
        )            
        
# Load addZchForm from disk
manage_addZchForm = HTMLFile('dtml/addZchForm', globals())

# method to construct a Zch Site
def manage_addZch(self,id,title='', skelton='zch', fileattache=0, REQUEST=None):     
    """Create Zch Site"""     
    elm = []
    if REQUEST.form.has_key('createlexicon'):
        elm = REQUEST.form["elements"]

    ob=ZchSite(id, title, skelton, fileattache, parent=self, elements=elm)         
    self._setObject(id, ob)     
     
    if REQUEST: return self.manage_main(self,REQUEST,update_menu=1)  

# Load images from disk and make them accessible
misc_={'Zch_img':  ImageFile('images/Zch.gif',globals()),  
       'posting_img':    ImageFile('images/posting.gif',globals()),  
       'comment_img':    ImageFile('images/comment.gif',globals()),  
       'Zchfile_img': ImageFile('images/Zchfile.gif',globals()),  
      }  


