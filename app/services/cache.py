import json,time
try: import redis
except ImportError: redis=None
from app.core.config import settings
class Cache:
 def __init__(self):
  self._mem={}; self._client=None
  if redis and settings.REDIS_URL:
   try: self._client=redis.from_url(settings.REDIS_URL,decode_responses=True); self._client.ping()
   except Exception: self._client=None
 def get(self,key):
  if self._client:
   raw=self._client.get(key); return json.loads(raw) if raw else None
  item=self._mem.get(key)
  if not item:return None
  expires,raw=item
  if expires<time.time():self._mem.pop(key,None);return None
  return json.loads(raw)
 def set(self,key,value,ttl=3600):
  raw=json.dumps(value,default=str)
  if self._client:self._client.setex(key,ttl,raw)
  else:self._mem[key]=(time.time()+ttl,raw)
 def delete(self,key):
  if self._client:self._client.delete(key)
  else:self._mem.pop(key,None)
cache=Cache()
