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
KDAC={} #hero summary per hero name
GPM={} #hero summary per hero name
XPM={} #hero summary per hero name
ROLES={} #summary crunch by role name

gkdac=None
ggpm=None
gxpm=None
score=None

class Player:
  def __init__(self,data,team):
    self.team=team
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
    r+=f'    KDAC {self.kdac:.1f}\n'
    r+=f'    GPM {self.gpm}\n'
    r+=f'    XPM {self.xpm}\n'
    r+=f'    Score {self.score:.0f}\n'
    return r[:-1]
  
  def isnob(self,absolute=True):
    score=abs(self.score)
    return score>=NOBLIMIT if absolute else score>=gscore.median+gscore.deviation*NOBLIMIT

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
      p=Player(p,team)
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
    r=f'{self.round(self.median):5.1f}\t± {self.round(self.deviation):5.1f}\t'
    return r
  
  def score(self,p):
    return 0 if self.deviation==0 else (p-self.median)/self.deviation

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
    
def printheroes(frequency,output,alphabetical,delimiter,csv):
  if alphabetical:
    iterator=sorted(frequency) 
  else:
    iterator=sorted(frequency,key=lambda f:frequency[f],reverse=True)
  csv.write('Hero;Matches;KDAC;GPM;XPM;\n')
  for hero in iterator:
    if output:
      line=[
        hero.center(NAMEPADDING),
        str(frequency[hero]).rjust(4),
        f'{KDAC[hero].median:.1f}kdac'.rjust(8),
        f'{GPM[hero].median:.0f}gpm'.rjust(5),
        f'{XPM[hero].median:.0f}xpm'.rjust(5),
        ]
      print(delimiter.join(line))
    if csv:
      parseable=[hero,frequency[hero],KDAC[hero].median,GPM[hero].median,XPM[hero].median,]
      parseable=[str(data) for data in parseable]
      csv.write(';'.join(parseable)+'\n')
    
def examineheroes(output=False,alphabetical=True,delimiter=' ',warn=True,csv=open('heroes.csv','w')):
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
  printheroes(frequency,output,alphabetical,delimiter,csv)

def crunch(players):
  kdac=[]
  gpm=[]
  xpm=[]
  for p in players:
    kdac.append(p.kdac)
    gpm.append(p.gpm)
    xpm.append(p.xpm)
  return {
    'kdac':Summary(kdac,rounding=0),
    'gpm':Summary(gpm,rounding=0),
    'xpm':Summary(xpm,rounding=0),
  }

def scoreroles(player):
  kdac=[]
  gpm=[]
  xpm=[]
  for r in player.hero['roles']:
    r=ROLES[r]
    kdac.append(r['kdac'].score(player.kdac))
    gpm.append(r['gpm'].score(player.gpm))
    xpm.append(r['xpm'].score(player.xpm))
  return [statistics.median(scores) for scores in [kdac,gpm,xpm]]

def examinematches(output=True,team=True,match=True,hero=True,role=True,universal=True):
  global gkdac,ggpm,gxpm,gscore
  gkdac=Summary([p.kdac for p in PLAYERS])
  ggpm=Summary([p.gpm for p in PLAYERS],rounding=0)
  gxpm=Summary([p.xpm for p in PLAYERS],rounding=0)
  for m in MATCHES:
    players=[p for p in m.getplayers()]
    match=crunch(players)
    radiant=crunch(m.radiant.players)
    dire=crunch(m.dire.players)
    for p in players:
      scores=[]
      if team:
        assert(p.team==m.radiant or p.team==m.dire)
        team=radiant if p.team==m.radiant else dire
        scores.extend([team['kdac'].score(p.kdac),team['gpm'].score(p.gpm),team['xpm'].score(p.xpm)])
      if match:
        scores.extend([match['kdac'].score(p.kdac),match['gpm'].score(p.gpm),match['xpm'].score(p.xpm)])
      if hero:
        scores.extend([KDAC[p.name].score(p.kdac),GPM[p.name].score(p.gpm),XPM[p.name].score(p.xpm)])
      if role:
        scores.extend(scoreroles(p))
      if universal:
        scores.extend([gkdac.score(p.kdac),ggpm.score(p.gpm),gxpm.score(p.xpm)])
      assert len(scores)>0
      p.score=statistics.median(scores)
  gscore=Summary([p.score for p in PLAYERS],rounding=2)
  for p in PLAYERS:
    if p.isnob():
      NOBS.append(p)
        
def examinemetrics(output=True): #used to calibrate and test overall metric sanity
  if output:
    print(f'KDAC\t{gkdac}')
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
    print(f'{len(NOBS)} NOBs ({round(100*len(NOBS)/(len(MATCHES)*10))}% of players, {len(GOODNOBS)} positive, {len(BADNOBS)} negative).')
    nobspermatch=[sum(p.isnob() for p in m.getplayers()) for m in MATCHES]
    print(f'NOBs per match: {Summary(nobspermatch,rounding=0)}.')
    balanced=sum(n==0 for n in nobspermatch)
    print(f'Balanced matches: {round(100*balanced/len(MATCHES))}% ({balanced}).')
    print()
    
def examineimpact(output=False,parseable=open('impact.csv','w')):
  if parseable:
    parseable.write(f'Score;Win rate (%);Frequency in teams (%);\n')
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
        print(f'Presence of {score} score predicts a {winrate}% win rate (present in {frequency}% of teams).')
      if parseable:
        parseable.write(f'{score};{winrate};{frequency};\n')
  if output:
    print()
    
def examineroles(output=False):
  roles=set(role for hero in HEROES.values() for role in hero['roles'])
  for r in roles:
    ROLES[r]={'kdac':[],'gpm':[],'xpm':[],}
  for p in PLAYERS:
    for r in p.hero['roles']:
      ROLES[r]['kdac'].append(p.kdac)
      ROLES[r]['gpm'].append(p.gpm)
      ROLES[r]['xpm'].append(p.xpm)
  for name in sorted(ROLES):
    r=ROLES[name]
    r['kdac']=Summary(r['kdac'])
    r['gpm']=Summary(r['gpm'])
    r['xpm']=Summary(r['xpm'])
    if output:
      print(name.center(10),r)

def examinescores(output=False): #rank heroes/roles per score, maybe even radiant/dire?
  pass

read()
examineheroes()
examineroles()
examinematches()
examinemetrics()
printnobs()
examineimpact()
examinescores()
#TODO would be cool to examine score per hero
print(f'{len(MATCHES)} matches analyzed ({len(MATCHES)*10} players).')
