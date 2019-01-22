#!/usr/bin/python3
import os,json
from pathlib import Path

INPUTDIR='matches'

for match in os.walk(INPUTDIR):
  data=json.load(open(Path(INPUTDIR,match[2][0])))
  print(data)
