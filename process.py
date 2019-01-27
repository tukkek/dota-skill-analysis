#!/usr/bin/python3
import os,json,statistics,random
from pathlib import Path

MINIMUMSAMPLESIZE=10
NAMEPADDING=len('Keeper of the Light')
NOBLIMIT=2
INPUTDIR='matches'
HEROES={hero['id']:hero for hero in json.load(open('heroes.json'))}
MATCHES=[]
TEAMS=[]
PLAYERS=[]
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
    self.score=0
  
  def __repr__(self):
    r=''
    r+=f'  {self.name}\n'
    r+=f'    KDA {self.kills}/{self.deaths}/{self.assists}\n'
    r+=f'    KDAC {self.kdac:.1f}\n'
    r+=f'    GPM {self.gpm}\n'
    r+=f'    XPM {self.xpm}\n'
    r+=f'    Score {self.score:.0f}\n'
    return r[:-1]

class Team:
  def __init__(self):
    self.players=[]
    self.won=False
    self.best=None
    self.worst=None
    TEAMS.append(self)
  
  def __repr__(self):
    r=''
    for p in self.players:
      r+=repr(p)+'\n'
    return r
  
  def win(self):
    return " (winner)" if self.won else ""

  def examine(self):
    skill=statistics.median([p.score for p in self.players])
    relative=[]
    for p in self.players:
      p.relativescore=p.score-skill
      relative.append(p.relativescore)
    self.worst=min(relative)
    self.best=max(relative)
    
  def getgoodnobs(self):
    return [p for p in self.players if p.relativescore>=NOBLIMIT]
    
  def getbadnobs(self):
    return [p for p in self.players if p.relativescore<=-NOBLIMIT]
  
  def getnobs(self):
    return self.getgoodnobs()+self.getbadnobs()
  
class Match:
  def __init__(self,data):
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
    return r[:-1]
  
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

def collapse(values): 
  return [] if len(values)==0 else [statistics.median(values)]

def score(p,team,match,hero,role,universal):
  local=[]
  nlocal=[]
  if team:
    local+=collapse([team['kdac'].score(p.kdac),team['gpm'].score(p.gpm),team['xpm'].score(p.xpm)])
  if match:
    local+=collapse([match['kdac'].score(p.kdac),match['gpm'].score(p.gpm),match['xpm'].score(p.xpm)])
  if hero:
    nlocal+=collapse([KDAC[p.name].score(p.kdac),GPM[p.name].score(p.gpm),XPM[p.name].score(p.xpm)])
  if role:
    kdac=[]
    gpm=[]
    xpm=[]
    for r in p.hero['roles']:
      r=ROLES[r]
      kdac.append(r['kdac'].score(p.kdac))
      gpm.append(r['gpm'].score(p.gpm))
      xpm.append(r['xpm'].score(p.xpm))
    nlocal+=collapse([collapse(score)[0] for score in [kdac,gpm,xpm]])
  if universal:
    nlocal+=collapse([gkdac.score(p.kdac),ggpm.score(p.gpm),gxpm.score(p.xpm)])
  scores=collapse(local)+collapse(nlocal)
  assert len(scores)>0
  return collapse(scores)[0]

def examinematches(output=True,team=True,match=True,hero=True,role=True,universal=True):
  global gkdac,ggpm,gxpm,gscore
  gkdac=Summary([p.kdac for p in PLAYERS])
  ggpm=Summary([p.gpm for p in PLAYERS],rounding=0)
  gxpm=Summary([p.xpm for p in PLAYERS],rounding=0)
  for m in MATCHES:
    players=[p for p in m.getplayers()]
    match=crunch(players) if match else False
    radiant=crunch(m.radiant.players) if team else False
    dire=crunch(m.dire.players) if team else False
    for p in players:
      playerteam=radiant if p.team==m.radiant else dire
      p.score=score(p,playerteam,match,hero,role,universal)
  gscore=Summary([p.score for p in PLAYERS],rounding=2)
        
def examinemetrics(output=True): #used to calibrate and test overall metric sanity
  if output:
    print(f'KDAC\t{gkdac}')
    print(f'GPM\t{ggpm}')
    print(f'XPM\t{gxpm}')
    print(f'Score\t{str(gscore)}')
    print()
      
def examinenobs(output=True,printall=False,randomize=False):
  if output:
    if printall:
      if randomize:
        random.shuffle(NOBS)
      for n in NOBS:
        print(n)
    print(f'Median relative player skill: {Summary([p.relativescore for m in MATCHES for p in m.getplayers()])}.')
    goodnobs=[n for t in TEAMS for n in t.getgoodnobs()]
    badnobs=[n for t in TEAMS for n in t.getbadnobs()]
    totalnobs=len(goodnobs)+len(badnobs)
    print(f'{totalnobs} NOBs ({round(100*(totalnobs)/(len(MATCHES)*10))}% of players, {len(goodnobs)} positive, {len(badnobs)} negative).')
    nobspermatch=[sum(len(team.getnobs()) for team in [m.radiant,m.dire]) for m in MATCHES]
    print(f'NOBs per match: {Summary(nobspermatch,rounding=0)}. Mode: {statistics.mode(nobspermatch)}.')
    unbalanced=sum([len(m.radiant.getnobs()+m.dire.getnobs())>0 for m in MATCHES])
    print(f'Unbalanced matches: {round(100*unbalanced/len(MATCHES))}% ({unbalanced}).')
    print(f'Median good NOB: {Summary([n.relativescore for n in goodnobs])}.')
    print(f'Median bad NOB: {Summary([n.relativescore for n in badnobs])}.')
    print()
    
def countwins(score):
  wins=0
  total=0
  for t in TEAMS:
    if (score>0 and t.best>=score) or (score<0 and t.worst<=score) or score==0:
      total+=1
      if t.won:
        wins+=1
  return wins,total
    
def examineimpact(output=False,parseable=open('impact.csv','w')):
  best=-9000
  worst=+9000
  scores=set()
  for t in TEAMS:
    t.examine()
    scores.add(round(t.best,1))
    scores.add(round(t.worst,1))
    if t.best>best:
      best=t.best
    if t.worst<worst:
      worst=t.worst
  if parseable:
    parseable.write(f'Score;Win rate (%);Frequency in teams (%);\n')
  for score in sorted(scores):
    wins,total=countwins(score)
    if total>=MINIMUMSAMPLESIZE:
      frequency=round(100*total/(len(MATCHES)*2))
      winrate=round(100*wins/total)
      if output:
        print(f'Presence of {score} score predicts a {winrate}% win rate (present in {frequency}% of teams).')
      if parseable:
        parseable.write(f'{score};{winrate};{frequency};\n')
  if output:
    print()

def examinescores(output=False): #TODO rank heroes/roles per score, maybe even radiant/dire?
  pass

read()
examineheroes()
examineroles()
examinematches()
examineimpact(output=True)
examinemetrics()
examinenobs()
examinescores()
print(f'{len(MATCHES)} matches analyzed ({len(MATCHES)*10} players).')
