#!/usr/bin/python3
import os,json,statistics
from pathlib import Path

INPUTDIR='matches'
HEROES={hero['id']:hero for hero in json.load(open('heroes.json'))}
MATCHES=[]
PLAYERS=[]
GLOBAL={} #global stats

class Player:
  def __init__(self,data):
    self.hero=HEROES[data['hero_id']]
    self.kills=data['kills']
    self.deaths=data['deaths']
    self.assists=data['assists']
    self.kdc=self.kills+self.assists/10-self.deaths
    self.gpm=data['gold_per_min']
    self.xpm=data['xp_per_min']
    #self.level=data['level']
    self.score=0
  
  def __repr__(self):
    r=''
    r+=f'  {self.hero["localized_name"]}\n'
    #r+=f'    Level {self.level}\n'
    r+=f'    KDA {self.kills}/{self.deaths}/{self.assists}\n'
    r+=f'    cKPD {self.kdc:.1f}\n'
    r+=f'    GPM {self.gpm}\n'
    r+=f'    XPM {self.xpm}\n'
    r+=f'    Score {self.score:.0f}\n'
    return r[:-1]

class Team:
  def __init__(self):
    self.players=[]
    self.won=False
  
  def __repr__(self):
    r=''
    for p in self.players:
      r+=repr(p)+'\n'
    return r
  
  def win(self):
    return " (winner)" if self.won else ""

class Match:
  def __init__(self,data):
    #self.duration=int(data['duration']/60)
    self.radiant=Team()
    self.dire=Team()
    winner=self.radiant if data['radiant_win'] else self.dire
    winner.won=True
    for p in data['players']:
      team=self.radiant if p['isRadiant'] else self.dire
      p=Player(p)
      team.players.append(p)
      PLAYERS.append(p)
    
  def __repr__(self):
    r=''
    #r+=f'Duration: {self.duration}m\n'
    r+=f'Radiant{self.radiant.win()}: \n{repr(self.radiant)}';
    r+=f'Dire{self.dire.win()}: \n{repr(self.dire)}';
    return r
  
  def getplayers(self):
    for p in self.radiant.players:
      yield p
    for p in self.dire.players:
      yield p
    
class Summary:
  def __init__(self,population,rounding=1):
    self.size=len(population)
    self.rounding=rounding
    self.median=statistics.median(population)
    #self.mean=statistics.mean(population)
    self.deviation=statistics.median([abs(p-self.median) for p in population])
    '''self.outliers=0
    for p in population:
      if not (self.median-self.deviation<=p<=self.median+self.deviation):
        self.outliers+=1'''
  
  def round(self,value):
    r=round(value,self.rounding)
    return int(r) if self.rounding==0 else r
  
  def __repr__(self):
    r=''
    r+=f'median {self.round(self.median)}\t'
    #r+=f'average {self.round(self.mean)}\t'
    r+=f'median deviation {self.round(self.deviation)}\t'
    #r+=f'outliers {round(100*self.outliers/self.size)}%\t'
    return r[:-1]
  
  def score(self,p):
    #print((p-self.median)/self.deviation)
    return (p-self.median)/self.deviation

def validate(match):
  for p in match['players']:
    if p['leaver_status']!=0:
      return False
  return match['human_players']==10

def read():
  for walk in os.walk(INPUTDIR):
    for match in walk[2]:
      try:
        match=json.load(open(Path(INPUTDIR,match)))
      except Exception:
        raise Exception('Error reading '+match)
      if validate(match):
        MATCHES.append(Match(match))

def printall():
  for m in MATCHES:
    print(m)

def examinemetrics():
  GLOBAL['kdc']=Summary([p.kdc for p in PLAYERS])
  GLOBAL['gpm']=Summary([p.gpm for p in PLAYERS],rounding=0)
  GLOBAL['xpm']=Summary([p.xpm for p in PLAYERS],rounding=0)
  print(f'cKPD\t{GLOBAL["kdc"]}')
  print(f'GPM\t{GLOBAL["gpm"]}')
  print(f'XPM\t{GLOBAL["xpm"]}')

def examinematches(output=False,localstats=True,globalstats=False,herostats=False): #TODO
  for m in MATCHES:
    players=[p for p in m.getplayers()]
    kdc=Summary([p.kdc for p in players])
    gpm=Summary([p.gpm for p in players],rounding=0)
    xpm=Summary([p.xpm for p in players],rounding=0)
    for p in players:
      if localstats:
        p.score+=kdc.score(p.kdc)
        p.score+=gpm.score(p.gpm)
        p.score+=xpm.score(p.xpm)
      if globalstats:
        p.score+=GLOBAL['kdc'].score(p.kdc)
        p.score+=GLOBAL['gpm'].score(p.gpm)
        p.score+=GLOBAL['xpm'].score(p.xpm)
  score=Summary([p.score for p in PLAYERS],rounding=2)
  nobs=[p for p in PLAYERS if abs(p.score)>score.median+score.deviation*2]
  good=[n for n in nobs if n.score>0]
  bad=[n for n in nobs if n.score<0]
  if output:
    for n in nobs:
      print(n)
  print(f'Score\t{str(score)}')
  print(f'{len(nobs)} nobs ({len(good)} positive, {len(bad)} negative) out of {len(PLAYERS)} players.')
      

read()
examinemetrics()
examinematches(output=False)
#printall()
print(f'{len(MATCHES)} matches analyzed.')
