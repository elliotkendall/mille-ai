#!/usr/bin/env python
import time
from sys import exit
from mille.matthewgai import Constants
from mille.matthewgai import MatthewgAI
from mille.matthewgai import PerfConstants
from mille.sampleais import *
from mille.game import Game
from mille.cards import Cards

# Begin configurable parameters

competitors = [MatthewgAI, BasicAI]
numPlayers = 6
games = 10000
debug = False
Constants.DEBUG = False
PerfConstants.SAVE_POPULATION = True


# End configurable parameters

players = []
competitor = 0
for i in range(numPlayers):
  players.append(competitors[competitor]())
  competitor += 1
  if competitor >= len(competitors):
    competitor = 0

scores = {}
gamesPlayed = 0
startTime = time.time()
while True:
  g = Game(players, debug)
  winners = g.play()
  for winner in winners:
    if not scores.has_key(winner):
      scores[winner] = 0
    scores[winner] += 1
  gamesPlayed += 1
  print "Played %d games in %d seconds." % (gamesPlayed, int(time.time() - startTime))

print scores
