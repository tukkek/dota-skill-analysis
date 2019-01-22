#!/usr/bin/python3
import urllib.request as url
import time,sys,os
from pathlib import Path

if len(sys.argv)<2:
  raise Exception('Usage: retrieve.py match_id [match_id ...]')

OPENDOTA='https://api.opendota.com/api/'
MATCHES=sys.argv[1:]
OUTPUT='matches'
  
def get(call,prefix=OPENDOTA):
  time.sleep(1) #as per OpenDota rate limit (60/min)
  return url.urlopen(prefix+call).read()

os.makedirs(OUTPUT,exist_ok=True)
for match in MATCHES:
  p=Path(OUTPUT,match+'.json')
  if not p.exists():
    open(p,'wb').write(get('matches/'+match))
