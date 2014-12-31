#!/usr/bin/env python
from sys import exit, stdout
from mille.sampleais import *
from mille.game import Game
from mille.cards import Cards
from mille.transcript import TranscriptReader, TranscriptWriter

# Begin configurable parameters

competitors = [BasicAI, ManualAI]
numPlayers = 2
games = 1
debug = False

readTranscript = None
writeTranscript = None
#readTranscript = "/tmp/millegame"
#writeTranscript = "/tmp/millegame"

# End configurable parameters

if readTranscript:
  reader = TranscriptReader(
    readTranscript,
    lambda *args: stdout.write("Transcript game start!\n"),
    lambda *args: stdout.write("Transcript hand start!\n"),
    lambda game, player, drawnCard, move: stdout.write(
      "Transcript move: %d drew %s %s\n" % (
        player, Cards.cardToString(drawnCard) if drawnCard else "nothing", move)),
    lambda *args: stdout.write("Transcript hand end!\n"),
    lambda game: stdout.write("Transcript game end!  Scores: %s\n" % (
        " ".join(map(lambda team: "%d" % team.totalScore,
                     game.teams)))))
  reader.read(debug = True)
  exit(0)

players = []
competitor = 0
for i in range(numPlayers):
  players.append(competitors[competitor]())
  competitor += 1
  if competitor >= len(competitors):
    competitor = 0

scores = {}
transcriptWriter = None
for i in range(games):
  g = Game(players, debug)
  if writeTranscript:
    transcriptWriter = TranscriptWriter(writeTranscript, g)
  winners = g.play()
  for winner in winners:
    if not scores.has_key(winner):
      scores[winner] = 0
    scores[winner] += 1

print scores
