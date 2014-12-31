#!/usr/bin/env python

from mille.cards import Cards
from mille.move import Move
from mille.transcript import TranscriptReader

import collections
import sys


class Stats(object):
  def __init__(self):
    self.eventCounts = {}
    self.byOpponent = {}
    for event in ("win",
                  "loss", 
                  "handWin",
                  "handLoss",
                  "discard",
                  "attack",
                  "attackFailed",
                  "safety",
                  "targeted",
                  "coupFourred",
                  "needRemedyTurn",
                  "needGoTurn",
                  "speedLimitTurn",
                  "declaredExtension",
                  "movedWithEmptyDeck",
                  "safeTrip",
                  "shutout",
                  "wasShutOut",
                  ):
      self.eventCounts[event] = collections.defaultdict(lambda: 0)
      self.byOpponent[event] = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))

  def sawEvent(self, event, actor, allActors):
    self.eventCounts[event][actor] += 1
    for otherActor in allActors:
      if otherActor == actor:
        continue
      self.byOpponent[event][actor][otherActor] += 1


class PlayerAndTeamStats(object):
  def __init__(self):
    self.byPlayer = Stats()
    self.byTeam = Stats()

  def sawEvent(self, event, player, playerTeam, players, teams):
    self.byPlayer.sawEvent(event, player, players)
    self.byTeam.sawEvent(event, playerTeam, teams)


class Leaderboard(object):
  def __init__(self):
    self.lastPlayerMoved = ""  # To figure out who tried to attack a coup fourre player.
    self.currentGameSize = 0
    self.currentHandTarget = 0
    self.currentGamePlayers = tuple()
    self.currentGameTeams = tuple()
    self.overallStats = PlayerAndTeamStats()
    self.statsByGameSize = {
        2: PlayerAndTeamStats(),
        3: PlayerAndTeamStats(),
        4: PlayerAndTeamStats(),
        6: PlayerAndTeamStats(),
    }

  def gameStarted(self, game, playerNames):
    self.currentGameSize = len(playerNames)
    self.currentGamePlayers = tuple(playerNames)
    self.currentGameTeams = tuple(
        tuple(playerNames[i] for i in team.playerNumbers)
        for team in game.teams)

  def handStarted(self, game):
    self.currentHandTarget = game.target
    self.lastPlayerMoved = ""

  def movePlayed(self, game, playerNum, drawnCard, move):
    cardType = Cards.cardToType(move.card)
    player = game.players[playerNum]
    team = game.teams[game.players[playerNum].teamNumber]
    playerStr = self.currentGamePlayers[playerNum]
    teamPlayers = self.currentGameTeams[team.number]

    if game.target > self.currentHandTarget:
      self.currentHandTarget = game.target
      self.sawPlayerEvent("declaredExtension", playerStr, teamPlayers)

    if team.needRemedy and team.needRemedy != Cards.REMEDY_GO and team.needRemedy != Cards.REMEDY_END_OF_LIMIT:
      self.sawPlayerEvent("needRemedyTurn", playerStr, teamPlayers)
    elif not team.moving:
      self.sawPlayerEvent("needGoTurn", playerStr, teamPlayers)

    if team.speedLimit:
      self.sawPlayerEvent("speedLimitTurn", playerStr, teamPlayers)

    if move.type == Move.DISCARD:
      self.sawPlayerEvent("discard", playerStr, teamPlayers)
    elif cardType == Cards.ATTACK:
      self.sawPlayerEvent("attack", playerStr, teamPlayers)
      self.sawTeamEvent("targeted", self.currentGameTeams[move.target])
    elif cardType == Cards.MILEAGE:
      if drawnCard is None:
        self.sawPlayerEvent("movedWithEmptyDeck", playerStr, teamPlayers)
    elif cardType == Cards.SAFETY:
      if move.coupFourre:
        self.sawPlayerEvent("coupFourred", playerStr, teamPlayers)
        self.sawPlayerEvent("attackFailed", self.lastPlayerMoved, teamPlayers)
      self.sawPlayerEvent("safety", playerStr, teamPlayers)
      
    self.lastPlayerMoved = playerStr

  def handEnded(self, game):
    teamsWithMileage = len([team for team in game.teams if team.mileage > 0])
    for team in game.teams:
      teamPlayers = self.currentGameTeams[team.number]
      if team.safeTrip:
        self.sawTeamEvent("safeTrip", teamPlayers)
      if game.winner == team.number:
        self.sawTeamEvent("handWin", teamPlayers)
        if teamsWithMileage == 1:
          self.sawTeamEvent("shutout", teamPlayers)
      else:
        self.sawTeamEvent("handLoss", teamPlayers)
        if teamsWithMileage == 1:
          self.sawTeamEvent("wasShutOut", teamPlayers)

  def gameEnded(self, game):
    winningScore = 0
    winningTeamNumber = None
    for team in game.teams:
      if team.totalScore > winningScore:
        winningScore = team.totalScore
        winningTeamNumber = team.number

    for team in game.teams:
      teamPlayers = self.currentGameTeams[team.number]
      if team.number == winningTeamNumber:
        self.sawTeamEvent("win", teamPlayers)
      else:
        self.sawTeamEvent("loss", teamPlayers)

  def sawPlayerEvent(self, event, playerStr, teamPlayers):
    self.overallStats.byPlayer.sawEvent(event, playerStr, self.currentGamePlayers)
    self.overallStats.byTeam.sawEvent(event, teamPlayers, self.currentGameTeams)
    self.statsByGameSize[self.currentGameSize].byPlayer.sawEvent(event, playerStr, self.currentGamePlayers)
    self.statsByGameSize[self.currentGameSize].byTeam.sawEvent(event, teamPlayers, self.currentGameTeams)

  def sawTeamEvent(self, event, teamPlayers):
    self.overallStats.byTeam.sawEvent(event, teamPlayers, self.currentGameTeams)
    self.statsByGameSize[self.currentGameSize].byTeam.sawEvent(event, teamPlayers, self.currentGameTeams)
    for playerStr in teamPlayers:
      self.overallStats.byPlayer.sawEvent(event, playerStr, self.currentGamePlayers)
      self.statsByGameSize[self.currentGameSize].byPlayer.sawEvent(event, playerStr, self.currentGamePlayers)

  def showStats(self):
    print "# Leaderboard"
    print ""
    for (name, stats) in (("Overall", self.overallStats),
                          ("2-Player Division", self.statsByGameSize[2]),
                          ("3-Player Division", self.statsByGameSize[3]),
                          ("4-Player Division", self.statsByGameSize[4]),
                          ("6-Player Division", self.statsByGameSize[6]),
                          ):
      print "## %s" % name
      print ""
      self.showDivision(stats)

  def showDivision(self, playerAndTeamStats):
    print "### By Player"
    print ""
    self.showEntityStats(playerAndTeamStats.byPlayer)
    print "### By Team"
    print ""
    self.showEntityStats(playerAndTeamStats.byTeam)

  def showEntityStats(self, stats):
    events = stats.eventCounts.keys()
    events.sort()
    for event in events:
      print "#### %s" % event
      print ""
      eventStats = stats.eventCounts[event]
      entities = eventStats.keys()
      entities.sort(key = lambda entity: eventStats[entity], reverse = True)
      for i in xrange(len(entities)):
        print "%d. %s: %d" % (i+1,
                              str(entities[i]),
                              eventStats[entities[i]])
      print ""

      print "##### By Opponent"
      for entity in entities:
        print ""
        print "* %s" % str(entity)
        print ""
        byOpponentStats = stats.byOpponent[event][entity]
        opponents = byOpponentStats.keys()
        opponents.sort(key = lambda opponent: byOpponentStats[opponent], reverse = True)
        for i in xrange(len(opponents)):
          print "  %d. %s: %d" % (i+1,
                                  str(opponents[i]),
                                  byOpponentStats[opponents[i]])
      print ""

  def processTranscripts(self, paths):
    for path in paths:
      TranscriptReader(path,
                       self.gameStarted,
                       self.handStarted,
                       self.movePlayed,
                       self.handEnded,
                       self.gameEnded).read()
    self.showStats()


def main(argv):
  if len(argv) < 2:
    sys.stderr.write("Usage: %s transcript1 ... transcriptN\n" % argv[0])
    sys.exit(1)

  Leaderboard().processTranscripts(argv[1:])
  sys.exit(0)
  

if __name__ == "__main__":
  main(sys.argv)
