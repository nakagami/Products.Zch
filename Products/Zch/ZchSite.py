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
__version__='$Revision: 1.62 $'[11:-2]  
__doc__ = """Zch - 2ch like web-log system"""

import re, os
from types import IntType
from time import time, localtime, strftime, gmtime
from string import strip,join,atoi,replace
from urllib import quote, unquote     
from socket import getfqdn

from AccessControl import ClassSecurityInfo
from Globals import PersistentMapping, HTMLFile, MessageDialog, InitializeClass, package_home
from Acquisition import aq_base
from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IISet
from OFS.Document import Document
from OFS.ObjectManager import REPLACEABLE
from Products.ZCatalog import ZCatalog
from Products.PythonScripts.PythonScript import manage_addPythonScript
from Products.PageTemplates.ZopePageTemplate import manage_addPageTemplate

from ZchPermissions import ManageZch,AddArticleZch,AddCommentZch,View
from Article import Article

class EmptyClass: pass

class ZchSite(ZCatalog.ZCatalog):     
    """A Zch Site is a self contained web-based news publishing and discussion system"""     
    meta_type  ='Zch Site'     
    description='Zch Site'     
     
    security = ClassSecurityInfo()
    security.setPermissionDefault(ManageZch,('Manager',))
    security.setPermissionDefault(AddArticleZch,('Manager',))
    security.setPermissionDefault(AddCommentZch,('Anonymous','Manager',))
    security.setPermissionDefault(View,('Anonymous','Manager',))

    icon       ='misc_/Zch/Zch_img'     
    
    _properties=({'id':'title', 'type':'string','mode':'w'},)     
     
    fileattache=0
    sage=0

    manage_options=({'label':'Contents', 'icon':icon, 'action':'manage_main', 'target':'manage_main'},     
                    {'label':'View', 'icon':'', 'action':'index_html', 'target':'manage_main'},     
                    {'label':'Postings', 'icon':'', 'action':'manage_postings', 'target':'manage_main'},     
                    {'label':'Options', 'icon':'', 'action':'manage_editForm', 'target':'manage_main'},     
                    {'label':'Properties', 'icon':'', 'action':'manage_propertiesForm', 'target':'manage_main'},
                    {'label':'Catalog', 'icon':'', 'action':'manage_catalogView', 'target':'manage_main'},
                    {'label':'Indexes', 'icon':'', 'action':'manage_catalogIndexes', 'target':'manage_main'},
                    {'label':'Security', 'icon':'', 'action':'manage_access', 'target':'manage_main'},
                    {'label':'Undo', 'icon':'', 'action':'manage_UndoForm', 'target':'manage_main'}
                    )     

    security.declareProtected(ManageZch, 'manage_postings')
    manage_postings   = HTMLFile('dtml/manage_postings', globals())

    security.declareProtected(ManageZch, 'manage_editForm')
    manage_editForm   = HTMLFile('dtml/editForm', globals())     

    security.declarePrivate('_buildIndexing')
    def _buildIndexing(self, id, title):
        # Initialise ZCatalog
        if not hasattr(self,'_catalog'):
            ZCatalog.ZCatalog.__init__(self, id, title)

        # delete any existing indexes
        for name in self.indexes():
            self.delIndex(name)
            
        # add the default indexes
        for (name,index_type) in [('meta_type', 'FieldIndex'),
                                  ('author', 'FieldIndex'),
                                  ('body', 'ZCTextIndex'),
                                  ('title', 'ZCTextIndex'),
                                  ('date', 'FieldIndex')]:
            if index_type == 'ZCTextIndex':
                extras = EmptyClass()
                extras.doc_attr = name
                extras.index_type = 'Okapi BM25 Rank'
                extras.lexicon_id = 'lexicon'
                self.addIndex(name, index_type, extra=extras)
            else:
                self.addIndex(name,index_type)
                          
        # delete the default metadata columns
        for name in self.schema():
            self.delColumn(name)

        # Add the meta data columns for search results
        for name in ['id','title','absolute_url','author','date_posted','date','body', 'tnum']:
            self.addColumn(name,'')
      
    security.declareProtected(ManageZch, 'recatalogPostings')
    def recatalogPostings(self,REQUEST=None):
        """ Clear the Catalog and then Index all the postings. """
        self._catalog.clear()
        for article_id in self.ids:
            article = self.data[article_id].__of__(self)
            if type(article.body)==type([]):
                article.body = join(article.body, '\n')
            for comment_id in article.ids:
                comment = self.data[comment_id].__of__(article)
                if type(comment.body)==type([]):
                    comment.body = join(comment.body, '\n')
                self.catalog_object(comment, join(comment.getPhysicalPath(), '/'))
            
            self.catalog_object(article, join(article.getPhysicalPath(), '/'))
                
        if REQUEST is not None:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(ManageZch, 'loadSkelton')
    def loadSkelton(self, REQUEST, skelton='zch'):
        "Add Page Template PythonScript, DTMLMethod and Image read from skelton directory."
        for entry in os.listdir(os.path.join(package_home(globals()), 'skelton', skelton)):
            if entry[-3:] == '.pt' or entry[-4:]=='.pys' or entry[-5:]=='.dtml' or entry[-4:]=='.gif':
                f=open(os.path.join(package_home(globals()), 'skelton', skelton, entry), 'rb') 
                file=f.read()     
                f.close()     
                try:
                    if entry[-3:] == '.pt':
                        id = entry[:-3]
                        manage_addPageTemplate(self, id, '', file, encoding='utf-8')
                    elif entry[-4:] == '.pys':
                        id = entry[:-4]
                        manage_addPythonScript(self,id)
                        self._getOb(id).write(file)
                    elif entry[-5:] == '.dtml':
                        id = entry[:-5]
                        self.manage_addDTMLMethod(id,'',file)     
                    elif entry[-4:] == '.gif':
                        id = entry[:-4]
                        self.manage_addImage(id,file,content_type='image/gif')
                except:
                    pass
        if REQUEST is not None:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declarePrivate('loadProperties')
    def loadProperties(self, skelton):
        "Add properties from 'properties' file."
        p = re.compile(r'(\w+?):(\w+?)=\s*(.*)\s*')
        newprop = list(self._properties)
        f = open(os.path.join(package_home(globals()), 'skelton', skelton, 'properties'), 'r')
        for s in f:
            if s[0] == '#':
                continue
            m = p.match(s)
            if m:
                newprop.append({'id':m.group(1), 'type':m.group(2), 'mode': 'wd'})
        f.close()
        self._properties = tuple(newprop)     
        f = open(os.path.join(package_home(globals()), 'skelton', skelton, 'properties'), 'r')
        for s in f:
            if s[0] == '#':
                continue
            m = p.match(s)
            if m:
                self._updateProperty(m.group(1), m.group(3))
        f.close()
    

    security.declarePrivate('__init__')
    def __init__(self, id, title, skelton, fileattache, parent, elements):
        if elements:
            from Products.ZCTextIndex.ZCTextIndex import manage_addLexicon
            manage_addLexicon(self,id='lexicon',elements = elements)

        self.__of__(parent)._buildIndexing(id,title)

        t=time()     
        self.created  = t     
        self.modified = t     

        self.fileattache = fileattache

        self.data     =IOBTree()  # id -> Message     
        self.ids      =IISet() # ids of children

        self.loadSkelton(None, skelton)
        self.loadProperties(skelton)
        self.skelton = skelton

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
    
        # make sure it's in our list of children
        if not self.ids.has_key(id):
            raise KeyError, id
            
        # return the posting
        return self.data[id].__of__(self)
     
    security.declareProtected(View, 'zchcrypt')
    def zchcrypt(self,word,key):        
        import hmac, base64
        h = hmac.new(key)
        h.update(word)
        return base64.encodestring(h.digest())[:-3]

    security.declareProtected(View, 'zchfqdn')
    def zchfqdn(self,n):        
        return getfqdn(n)

    security.declarePrivate('delItem')
    def delItem(self,id):
        if not self.data.has_key(id):
            return

        if self.ids.has_key(id): # article
            article = self.data[id].__of__(self)
            for comment_id in article.ids:     
                obj = self.data[comment_id].__of__(article)
                self.uncatalog_object(obj.getPhysicalPath())
                del self.data[comment_id]
            self.uncatalog_object(article.getPhysicalPath())
            del self.data[id]
            self.ids.remove(id)
        else: # comment
            parent = self.data[self.data[id].parent_id].__of__(self)
            # remove it from it's parents list of ids
            obj = self.data[id].__of__(parent)
            self.uncatalog_object(obj.getPhysicalPath())
            del self.data[id]
            parent.ids.remove(id)
     
    security.declarePrivate('createId')
    def createId(self):     
        id=int(time())     
        while self.data.has_key(id):     
            id=id+1     
        return id     
     
    security.declarePrivate('data_map')
    def data_map(self,ids):
        result=[]
        for id in ids:
            result.append(self.data[id].__of__(self))
        return result
    
    security.declareProtected(View, 'article_list')
    def article_list(self, size=None):
        """ returns article items  """                          
        def cmp_by_modified(x, y):
          return cmp(y.modified, x.modified)
        items = self.data_map(self.ids)
        items.sort(cmp_by_modified)
        if size:
            items = items[:size]
        for i in range(len(items)):
            items[i].sequence_number = i + 1
            items[i].sn_title = str(i+1) + ':'
            items[i].title_count = items[i].title
            items[i].prev_link = '#'+str(i)
            items[i].next_link = '#'+str(i+2)
        return items

    security.declareProtected(ManageZch, 'postingValues')
    postingValues = article_list

    security.declareProtected(View, 'tpId')
    def tpId(self):     
        return self.id     
     
    security.declareProtected(View, 'tpURL')
    def tpURL(self):     
        return self.id     
     
    security.declareProtected(View, 'this')
    def this(self):     
        return self     
     
    security.declareProtected(View, 'site_url')
    def site_url(self):    
        # """ url of the Zch main page """ 
        return self.absolute_url()
     
    security.declareProtected(View, 'has_items')
    def has_items(self):     
        return len(self.ids)     
     
    security.declareProtected(View, 'item_count')
    def item_count(self):     
        return len(self.data)     
     
    security.declareProtected(AddArticleZch, 'addPosting')
    def addPosting(self,file='',REQUEST=None,RESPONSE=None, index=1):
        """ add an article """
        
        id=self.createId()     
     
        msg=Article(id)
        err, sage = msg.__of__(self)._validation(REQUEST,RESPONSE,'delete attachment',file)
        if err:
            return err

        # Set thread number. 
        msg.tnum = '1'

        self.ids.insert(id)     
        self.data[id]=msg

        if index:
            msg.__of__(self).index()

        if RESPONSE:
            return self.showMessage(self, REQUEST=REQUEST, 
                                title='Article Posted',     
                                message  ='Your article has been posted',
                                action=self.absolute_url()
                                )

        return id
     
    security.declareProtected(View, 'search')
    def search(self,REQUEST):     
        """ fulfill a search request """
        if REQUEST.has_key('op') and REQUEST['op']=='articles':
            REQUEST.set('meta_type','Article')
    
        sr=self.__call__(REQUEST)     
        rc=len(sr)     
        return self.showSearchResults(self,REQUEST,search_results=sr,     
                                  result_count=rc)     
     
    security.declareProtected(ManageZch, 'manage_edit')
    def manage_edit(self, REQUEST=None, fileattache=0):     
        """ edit Zch options  """     
        self.fileattache = fileattache

        if REQUEST is not None:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])
     
    security.declareProtected(ManageZch, 'manage_delete')
    def manage_delete(self,ids=[],REQUEST=None):     
        """ delete selected articles from a Zch site """     
        ids=map(atoi, ids)     
        for id in ids:     
            self.delItem(id)
        if REQUEST is not None:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declarePrivate('list_skelton')
    def list_skelton(self):
        skelton = []
        for item in os.listdir(os.path.join(package_home(globals()), 'skelton')):
            skelton.append(item)
        return skelton

        
    # Searchable interface     
    security.declareProtected(View, '__call__')
    def __call__(self, REQUEST=None, internal=0, **kw):        
        brains = apply(self.searchResults,(REQUEST,),kw)
	if internal:
	    return map(lambda x: x.getObject(), brains)
	return brains

InitializeClass(ZchSite)


