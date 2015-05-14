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
__version__='$Revision: 1.41 $'[11:-2]  
     
from time import time, localtime, strftime, gmtime
from string import strip,split,join,atoi
from urllib import quote, unquote
from types import IntType
import re

from Globals import Persistent     
from Globals import HTMLFile
import Globals
from Acquisition import Implicit
from ZchPermissions import ManageZch,View
from DateTime import DateTime
from OFS.Traversable import Traversable
from DocumentTemplate.DT_Util import html_quote
from AccessControl import ClassSecurityInfo

from Zchfile import Zchfile     

class Posting(Persistent, Implicit, Traversable):     
    """Zch Posting"""
    
    security = ClassSecurityInfo()

    security.setDefaultAccess("allow")
    
    meta_type='Posting'     
    icon   ='misc_/Zch/posting_img'     
    
    security.declareProtected(ManageZch, 'manage_editPostingForm')
    manage_editPostingForm=HTMLFile('dtml/editPostingForm', globals())
    
    # Aliases for manage_editPostingForm
    manage=HTMLFile('dtml/editPostingForm', globals())
    manage_main=HTMLFile('dtml/editPostingForm', globals())

    security.declarePrivate('__init__')
    def __init__(self, id):     
        self.id      =str(id)     
        self.created =id     
        self.modified=id     
     
    security.declarePrivate('index')
    def index(self):
        # index this posting is the Zch site that contains it.
        self.catalog_object(self,join(self.getPhysicalPath(),'/'))

    security.declareProtected(View, '__getitem__')
    def __getitem__(self,id):
        """ Get a posting from the ZchSite data store """
    
        # make sure id is an integer
        try:
            if not isinstance(id,IntType):
                id=atoi(id)
        except ValueError:
            raise KeyError, id
    
        # make sure it's in our list of children
        if not self.ids.has_key(id):
            raise KeyError, id
            
        # return the posting
        return self.data[id].__of__(self)
     
    security.declareProtected(View, 'date_posted')
    def date_posted(self,fmstr='%y/%m/%d %H:%M'):     
        # """ date when article was posted """     
        ltime = localtime(self.created)         
        return strftime(fmstr,ltime)     
             
    # deprecated methods
    date_created = time_created = date_posted

    security.declareProtected(View, 'date_modified')
    def date_modified(self,fmstr='%y/%m/%d %H:%M'):     
        # """ date when article was posted """     
        ltime = localtime(self.modified)         
        return strftime(fmstr,ltime)     

    security.declareProtected(View, 'date')
    def date(self):
        """return the date of creation for indexing purposes"""
        return DateTime(self.created)
    
    security.declareProtected(View, 'tpId')
    def tpId(self):     
        return self.id     
     
    security.declareProtected(View, 'tpURL')
    def tpURL(self):     
        return self.id     
     
    security.declareProtected(View, 'this')
    def this(self): return self     
         
    security.declareProtected(View, 'has_items')
    def has_items(self):     
        return len(self.ids)     
     
    security.declareProtected(View, 'attachment')
    def attachment(self):     
        # """ file attachment """     
        file=self.file
        return file and (file,) or None     
     
    security.declareProtected(View, 'index_html')
    def index_html(self,REQUEST):     
        """ Zch article main page (the read more page) """    
        return self.posting_html(self,REQUEST)     

    security.declarePrivate('_validation')
    def _validation(self,REQUEST,RESPONSE, delete_attachment=None,new_attachment=''):
        CRLF=re.compile('\r\n|\n\r')    
        CRLFCUT=re.compile('(\n\r|\r\n)*\Z')
    
        err, sage, attributes, cookies=self.validatePosting(raw=REQUEST)

        have_new_file = (hasattr(new_attachment,'filename') and new_attachment.filename)
     
        if delete_attachment or have_new_file:
            # delete the old file
            try:
                delattr(self,self.aq_base.file.file_name())
            except AttributeError:
                pass
            self.file=''

        if have_new_file:
            # store the new file
            file=Zchfile(new_attachment)     
            setattr(self,file.file_name(),file)     
            self.file=file

        # change the created date
        date = REQUEST.get('date')
        if date is not None:
            self.created=int(date.timeTime())

        # change the modified value
        self.modified = time()
     
        
        if err is not None:
            return err
        for attr in attributes:
            value = attributes.get(attr,'')
            if attr == 'body':
                value=CRLFCUT.sub('',value)
                value=CRLF.sub('\n', value)
            setattr(self,attr,value)

        if RESPONSE:
            gtime = gmtime(int(self.id))     
            glist = list(gtime)     
            glist[0] = glist[0] + 1 # add 1 year to expiry date     
            glist[1] = 12     
            glist[2] = 31     
            glist[3] = 23     
            glist[4] = 59     
            glist[5] = 59     
            glist[6] = 0     
            glist[7] = 365     
            glist[8] = 0     
            gtime = tuple(glist)     
            e = strftime('%A, %d-%b-%y %H:%M:%S GMT',gtime)     

            for cookie in cookies:
                RESPONSE.setCookie(cookie, cookies[cookie], expires=e, path='/')
        return err, sage

    security.declareProtected(ManageZch, 'edit')
    def edit(self,REQUEST=None,RESPONSE=None,delete_attachment=None,new_attachment='',index=1):     
        """ edit replies """     
        err, sage = self._validation(REQUEST, RESPONSE, delete_attachment, new_attachment)
        # re-catalog this posting
        if index:
            self.index()
     
        # should only get here if someone is editing a posting during moderation
        if RESPONSE:     
            RESPONSE.redirect(self.REQUEST.HTTP_REFERER)     
     
    # Used to display the body of the posting with the appropriate formatting
    security.declareProtected(View, 'cooked_body_2ch')
    def cooked_body_2ch(self):
        value=join(map(html_quote,split(self.body, '\n')),'<BR>\n') # html quote
        HTTPLINK=re.compile('(https?|ftp|gopher|telnet|whois|news)\:([\w|\:\!\#\$\%\=\&\-\^\`\\\|\@\~\[\{\]\}\;\+\*\,\.\?\/]+)')
        LINK2=re.compile('&gt;&gt;([\d]+)-([\d]+)') #>>?-?
        LINK1=re.compile('&gt;&gt;([\d]+)(?!&shy;)') #>>?
        if self.meta_type == 'Article':
            url = self.site_url() + '/' + str(self.id)
        else:
            url = self.site_url() + '/' + str(self.parent_id)
        value=HTTPLINK.sub('<a href="\\1:\\2" target="_blank">\\1:\\2</a>',value)
        value=LINK2.sub('<a href="' + url + '/comments_html?from_tnum=\\1&to_tnum=\\2" target="_blank">&gt;&gt;\\1&shy;\\2</a>', value)
        value=LINK1.sub('<a href="' + url + '/\\1" target="_blank">&gt;&gt;\\1</a>',value)
        return value
     
    security.declarePublic('getId')
    def getId(self):
         return self.id
     
    security.declareProtected(View, 'raw_body')
    def raw_body(self):
        return self.body

    security.declareProtected(View, 'raw_author')
    def raw_author(self):
        return self.author

Globals.InitializeClass(Posting)


