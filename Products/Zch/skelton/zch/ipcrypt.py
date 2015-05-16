## Script (Python) "ipcrypt"
##title=Ip Crypt
##parameters=key=None,salt=None

salt=str(salt)[6:8]
salt=str(salt)
if key == '':
  return '???'
else:
  key=key[8:]
  return context.zchcrypt(key,salt)[5:]
