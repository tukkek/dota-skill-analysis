#!/usr/bin/python3
import os,json,statistics,random
from pathlib import Path

MINIMUMSAMPLESIZE=10
NAMEPADDING=len('Keeper of the Light')
NOBLIMIT=2
INPUTDIR='matches'
HEROES={hero['id']:hero for hero in json.load(open('heroes.json'))}
MATCHES=[]
PLAYERS=[]
NOBS=[]
GOODNOBS=[]
BADNOBS=[]
KDAC={} #Summary per hero name
GPM={} #Summary per hero name
XPM={} #Summary per hero name

gkdac=None
ggpm=None
gxpm=None
score=None

class Player:
  def __init__(self,data):
    self.hero=HEROES[data['hero_id']]
    self.name=self.hero['localized_name']
    self.kills=data['kills']
    self.deaths=data['deaths']
    self.assists=data['assists']
    self.kdac=self.kills+self.assists/10-self.deaths
    self.gpm=data['gold_per_min']
    self.xpm=data['xp_per_min']
    #self.level=data['level']
    self.score=0
  
  def __repr__(self):
    r=''
    r+=f'  {self.name}\n'
    #r+=f'    Level {self.level}\n'
    r+=f'    KDA {self.kills}/{self.deaths}/{self.assists}\n'
    r+=f'    cKPD {self.kdac:.1f}\n'
    r+=f'    GPM {self.gpm}\n'
    r+=f'    XPM {self.xpm}\n'
    r+=f'    Score {self.score:.0f}\n'
    return r[:-1]
  
  def isnob(self,absolute=True):
    return abs(self.score)>=NOBLIMIT if absolute else score.median+score.deviation*NOBLIMIT

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
  
  def haspositivenob(self,score):
    for p in self.players:
      if p.score>=score:
        return True
    return False
  
  def hasnegativenob(self,score):
    for p in self.players:
      if p.score<=score:
        return True
    return False

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
    self.deviation=statistics.median([abs(p-self.median) for p in population])
  
  def round(self,value):
    r=round(value,self.rounding)
    return int(r) if self.rounding==0 else r
  
  def __repr__(self):
    r=''
    r+=f'median {self.round(self.median)}\t'
    r+=f'median deviation {self.round(self.deviation)}\t'
    return r[:-1]
  
  def score(self,p):
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
    
def printheroes(frequency,alphabetical,delimiter):
  for hero in (sorted(frequency) if alphabetical else sorted(frequency,key=lambda f:frequency[f],reverse=True)):
    line=[
      hero.center(NAMEPADDING),
      str(frequency[hero]).rjust(4),
      f'{KDAC[hero].median:.1f}kdac'.rjust(8),
      f'{GPM[hero].median:.0f}gpm'.rjust(5),
      f'{XPM[hero].median:.0f}xpm'.rjust(5),
      ]
    print(delimiter.join(line))
    
def examineheroes(output=False,alphabetical=True,delimiter=' ',warn=True):
  kdac={}
  gpm={}
  xpm={}
  frequency={}
  for hero in (HEROES[heroid]['localized_name'] for heroid in HEROES):
    kdac[hero]=[]
    gpm[hero]=[]
    xpm[hero]=[]
    frequency[hero]=0
  for m in MATCHES:
    for p in m.getplayers():
      kdac[p.name].append(p.kdac)
      gpm[p.name].append(p.gpm)
      xpm[p.name].append(p.xpm)
      frequency[p.name]+=1
  for hero in kdac:
    KDAC[hero]=Summary(kdac[hero])
    GPM[hero]=Summary(gpm[hero])
    XPM[hero]=Summary(xpm[hero])
    if warn and frequency[hero]<MINIMUMSAMPLESIZE:
      raise Exception(f'Not enough samples for {hero}: {frequency[hero]}/{MINIMUMSAMPLESIZE}.')
  if output:
    printheroes(frequency,alphabetical,delimiter)

def examinematches(output=True,matchstats=True,herostats=True,globalstats=True):
  global gkdac,ggpm,gxpm,gscore
  gkdac=Summary([p.kdac for p in PLAYERS])
  ggpm=Summary([p.gpm for p in PLAYERS],rounding=0)
  gxpm=Summary([p.xpm for p in PLAYERS],rounding=0)
  for m in MATCHES:
    players=[p for p in m.getplayers()]
    kdac=Summary([p.kdac for p in players])
    gpm=Summary([p.gpm for p in players],rounding=0)
    xpm=Summary([p.xpm for p in players],rounding=0)
    for p in players:
      scores=[]
      if matchstats:
        scores.extend([kdac.score(p.kdac),gpm.score(p.gpm),xpm.score(p.xpm)])
      if herostats:
        scores.extend([KDAC[p.name].score(p.kdac),GPM[p.name].score(p.gpm),XPM[p.name].score(p.xpm)])
      if globalstats:
        scores.extend([gkdac.score(p.kdac),ggpm.score(p.gpm),gxpm.score(p.xpm)])
      assert len(scores)>0
      p.score=statistics.median(scores)
  gscore=Summary([p.score for p in PLAYERS],rounding=2)
  for p in PLAYERS:
    if p.isnob():
      NOBS.append(p)
        
def examinemetrics(output=True): #used to calibrate and test overall metric sanity
  if output:
    print(f'cKPD\t{gkdac}')
    print(f'GPM\t{ggpm}')
    print(f'XPM\t{gxpm}')
    print(f'Score\t{str(gscore)}')
    print()
      
def printnobs(output=True,printall=False,randomize=False):
  if output:
    if printall:
      if randomize:
        random.shuffle(NOBS)
      for n in NOBS:
        print(n)
    for n in NOBS:
      if n.score>0:
        GOODNOBS.append(n)
      else:
        BADNOBS.append(n)
    print(f'{len(NOBS)} nobs ({round(100*len(NOBS)/(len(MATCHES)*10))}% of players, {len(GOODNOBS)} positive, {len(BADNOBS)} negative).')
    nobspermatch=[sum(p.isnob() for p in m.getplayers()) for m in MATCHES]
    print(f'Nobs per match: {Summary(nobspermatch,rounding=0)}.')
    balanced=sum(n==0 for n in nobspermatch)
    print(f'Balanced matches: {round(100*balanced/len(MATCHES))}% ({balanced}).')
    print()
    
def examineimpact(output=False,parseable=open('impact.csv','w')):
  if parseable:
    parseable.write(f'Score;Win rate (%);Frequency in matches(%);\n')
  teams=[]
  for m in MATCHES:
    teams.append(m.radiant)
    teams.append(m.dire)
  scores=set()
  for p in PLAYERS:
    scores.add(round(p.score,1))
  for score in sorted(scores):
    wins=0
    total=0
    for t in teams:
      if (score>0 and t.haspositivenob(score)) or (score<0 and t.hasnegativenob(score)) or score==0:
        total+=1
        if t.won:
          wins+=1
    if total>=MINIMUMSAMPLESIZE:
      winrate=round(100*wins/total)
      frequency=round(100*total/(len(MATCHES)*2))
      if output:
        print(f'{score} score or higher score predicts a {winrate}% win rate (present in {frequency} of teams).')
      if parseable:
        parseable.write(f'{score};{winrate};{frequency};\n')
  if output:
    print()

read()
examineheroes(warn=False)
examinematches()
examinemetrics()
printnobs()
examineimpact()
#TODO would be cool to examine score per hero
print(f'{len(MATCHES)} matches analyzed ({len(MATCHES)*10} players).')
