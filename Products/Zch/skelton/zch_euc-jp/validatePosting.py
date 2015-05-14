## Script (Python) "validate"
##title=Validate Postings
##parameters=raw=None
from Products.PythonScripts.standard import html_quote
import string

posting = context
sage = 0
attributes = {}
cookies = {}

#HTTP_REFERER
if context.REQUEST.BASE0 != context.REQUEST.HTTP_REFERER[0:len(context.REQUEST.BASE0)]:
    return '£Å£Ò£Ò£Ï£Ò¡§HTTP_REFERER¤¬ÉÔÀµ¤Ç¤¹¡ª!', sage, attributes, cookies

#Cookies (Stored as is)
cookies['_suggest_author'] = raw.get('author')
cookies['_suggest_email'] = raw.get('email')

#Title
if not raw.get('title'):
    return '£Å£Ò£Ò£Ï£Ò¡§¥¿¥¤¥È¥ë¤¬¤¢¤ê¤Þ¤»¤ó!', sage, attributes, cookies
else:
    attributes['title'] = raw.get('title')

#Body
value=string.replace(raw.get('body'),'\n','')
value=string.replace(value,'\r','')
if len(value) == 0:
    return attributes,'£Å£Ò£Ò£Ï£Ò¡§ËÜÊ¸¤¬¤¢¤ê¤Þ¤»¤ó!', sage, attributes, cookies
attributes['body'] = raw.get('body')

#Author
value=raw.get('author')
value=html_quote(value)
value=string.replace(value,'¢¡','¡þ')
value=string.replace(value,'¡ú','¡ù')
value=string.replace(value,'¡ü','¡û')
value=string.replace(value,'ºï½ü','"ºï½ü"')
value=string.replace(value,'sakujyo','"sakujyo"')
value=string.replace(value,'ÀßÃÖ¿Í','"ÀßÃÖ¿Í"')
value=string.replace(value,'´ÉÍý¿Í','"´ÉÍý¿Í"')
value=string.replace(value,'´ÉÄ¾¿Í','"´ÉÄ¾¿Í"')
value=string.replace(value,'¿ûÄ¾¿Í','"¿ûÄ¾¿Í"')
if string.find(value,"fusianasan") >= 0: # fusianasan
  value=string.replace(value,'fusianasan',
        '<B>' + context.zchfqdn(context.REQUEST.getClientAddr()) + '</B>')
if string.find(value,"#") >= 0: # trip
  value1=value[:string.find(value,"#")]
  value2=value[(string.find(value,"#")+1):]
  value3=context.zchcrypt(value2,"TP")
  value=value1+"<B>¢¡"+value3[3:11]+"</B>"
if value=="":
  value=context.NONAME_NAME
attributes['author']=value

#Email
attributes['email']=raw.get('email')

#Remote address
attributes['remote_addr']=context.REQUEST.getClientAddr()

#sage
if attributes['email']=='sage':
  sage = 1

return None, sage, attributes, cookies
