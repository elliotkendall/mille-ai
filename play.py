#!/usr/bin/env python
from sys import exit
from mille.matthewgai import MatthewgAI
from mille.sampleais import *
from mille.game import Game
from mille.cards import Cards

# Begin configurable parameters

competitors = [MatthewgAI, BasicAI]
numPlayers = 2
games = 100
debug = False

# End configurable parameters

players = []
competitor = 0
for i in range(numPlayers):
  players.append(competitors[competitor]())
  competitor += 1
  if competitor >= len(competitors):
    competitor = 0

scores = {}
for i in range(games):
  g = Game(players, debug)
  winners = g.play()
  for winner in winners:
    if not scores.has_key(winner):
      scores[winner] = 0
    scores[winner] += 1

print scores
