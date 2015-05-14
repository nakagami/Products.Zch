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
__version__='$Revision: 1.34 $'[11:-2]  
     
from time import time, localtime, strftime, gmtime
from urllib import quote
from string import join, atoi
from types import IntType

import Globals
from AccessControl import ClassSecurityInfo
from BTrees.IIBTree import IISet

from ZchPermissions import ManageZch,AddCommentZch,View
from Posting import Posting
from Comment import Comment


class Article(Posting):     
    """ """

    security = ClassSecurityInfo()
    
    meta_type  ='Article'     
    icon   ='misc_/Zch/posting_img'

    security.declarePrivate('__init__')
    def __init__(self, id):     
        Posting.__init__(self, id)
        self.ids     =IISet()     #Article has sub ids.
     
    
    security.declareProtected(View, 'relative_path')
    def relative_path(self):
        return self.id

    security.declareProtected(View, 'index_html')
    def index_html(self,REQUEST):     
        """ Zch article main page (the read more page) """    
        return self.article_html(self,REQUEST)     
     
    security.declareProtected(ManageZch, 'postingValues')
    def postingValues(self):     
        """ return all replies """     
        return self.data_map(self.ids)     
     
    security.declareProtected(View, 'comment_list_size')
    def comment_list_size(self, start=0, size=0):
        """ returns comment items  """                          
        if start:
            start = int(start)
        else:
            start = 0
        if size:
            size = int(size)
        else:
            size = 0

        # Adjust start to tnum
        if start == 1:
            start = 2
            if size:
                size = size-1
        # Convert to ids[] index number
        if start:
            start = start -2
    
            if size == 0:
                ids = [id for id in self.ids][start:]
            else:
                ids = [id for id in self.ids][start:start+size]
        else:
            if size == 0:
                ids = [id for id in self.ids][:]
            else:
                ids = [id for id in self.ids][size*-1:]
    
        return self.data_map(ids)

    security.declareProtected(View, 'comment_list_from_to')
    def comment_list_from_to(self, from_tnum=0, to_tnum=0):
        """ returns comment items  """                          
        from_tnum = int(from_tnum)
        to_tnum = int(to_tnum)
        ids = [id for id in self.ids if (from_tnum == 0 or int(self.data[id].tnum) >= from_tnum) and (to_tnum == 0 or int(self.data[id].tnum) <= to_tnum)]
        return self.data_map(ids)
    
    security.declareProtected(AddCommentZch, 'addPosting')
    def addPosting(self, file='', REQUEST=None,RESPONSE=None):     
        """ add a Comment """
        index=1
        id=self.createId()
        msg=Comment(id, self.id)
        err, sage = msg.__of__(self)._validation(REQUEST,RESPONSE,'delete attachment',file)
        if err:
            return err
        # Set thread number. 
        msg.tnum = str(len(self.ids) + 2)

        if sage==0:
            self.modified=id     

        self.ids.insert(id)     
        self.data[id]=msg

        if index:
            msg.__of__(self).index()
          
        if RESPONSE:
            return self.showMessage(self, REQUEST=REQUEST, 
                                title='Comment Posted',
                                message  ='Your reply has been posted',
                                action=self.absolute_url()     
                                )

        return id
     
    security.declareProtected(View, 'recent_entry')
    def recent_entry(self):
        if len (self.ids) != 0:
            return self.data[self.ids[-1]].body
        else:
            return self.body

    security.declareProtected(View, 'recent_creator')
    def recent_creator(self):
        if len (self.ids) != 0:
            return self.data[self.ids[-1]].author
        else:
            return self.author

    security.declarePublic('__len__')
    def __len__(self):
        return len(self.ids) + 1

    security.declareProtected(View, '__getitem__')
    def __getitem__(self,id):
        """ Get a posting from the ZchSite data store """
        # make sure id is an integer
        try:
            if not isinstance(id,IntType):
                id=atoi(id)
        except ValueError:
            raise KeyError, id

        try:
            return Posting.__getitem__(self,id)
        except KeyError:
            try:
                return self.data[self.ids[id-2]].__of__(self)
            except:
                raise KeyError, id


Globals.InitializeClass(Article)

