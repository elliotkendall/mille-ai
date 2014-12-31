from random import shuffle
from copy import copy, deepcopy

from mille.deck import Deck
from mille.gamestate import GameState
from mille.team import Team
from mille.player import Player
from mille.cards import Cards
from mille.move import Move

class Game:
  # How many points to win a game, as opposed to a single hand
  pointsToWin = 5000

  def __init__(self, AIs, debug = False, teams = None, players = None):
    self.teams = []
    self.players = []
    self.debug = debug
    self.transcriptWriter = None

    if not (bool(AIs) ^ bool(teams and players)):
      raise Exception("Must specify one and only one of (AIs), (teams, players).")

    if AIs is None:
      self.teams = teams
      self.players = players
    else:
      self.generateTeams(AIs)

    # Some initialization logic lives in its own routine so it can be called
    # separately if we're going to re-use this object for a new game
    self.reset()

  def generateTeams(self, AIs):
    # Seat players in a random order
    shuffle(AIs)
    
    # Set up teams
    count = len(AIs)
    if count == 2 or count == 4:
      teams = 2
    elif count == 3 or count == 6:
      teams = 3
    else:
      raise ValueError('Invalid number of players')

    for i in range(teams):
      self.teams.append(Team(i))

    team = 0
    for playerNumber in range(count):
      self.teams[team].playerNumbers.append(playerNumber)
      self.players.append(Player())
      self.players[playerNumber].number = playerNumber
      self.players[playerNumber].teamNumber = team
      self.players[playerNumber].ai = AIs[playerNumber]
      team = team + 1
      if team >= teams:
        team = 0

  # Prepare this object for a new game
  def reset(self):
    for team in self.teams:
      team.totalScore = 0

  # Prepare this object for a new hand
  def resetHandState(self):
    self.winner = -1
    self.tripComplete = False
    self.delayedAction = False
    self.extension = False
    self.discardPile = []
    if len(self.players) == 4:
      self.target = 1000
      self.extensionPossible = False
    else:
      self.target = 700
      self.extensionPossible = True
    self.deck = Deck()
    # No hands yet.
    for player in self.players:
      player.hand = []
    # Reset per-hand team variables
    for team in self.teams:
      team.reset()

  # Run a complete game
  #
  # Returns a list of winning player numbers
  def play(self):
    gameOver = False
    winningscore = 0
    winningteam = -1
    self.resetHandState()

    for player in self.players:
      player.ai.gameStarted(self.makeState(player))

    if self.transcriptWriter:
      self.transcriptWriter.writeGameStart()

    while not gameOver:
      # Run a single hand
      self.playHand()
      if self.debug:
        # Show the hand's results
        for team in self.teams:
          print 'Team ' + str(team.number) + ' has ' + str(team.totalScore) + ' points'
      # Adjust total scores
      for team in self.teams:
        if team.totalScore > winningscore:
          winningscore = team.totalScore
          winningteam = team.number
        if team.totalScore >= self.pointsToWin:
          gameOver = True
    if self.debug:
      print 'Team ' + str(winningteam) + ' wins'

    if self.transcriptWriter:
      self.transcriptWriter.writeGameEnd()

    # Return the winners indexed by name
    ret = {}
    for playerNumber in self.teams[winningteam].playerNumbers:
      name = str(self.players[playerNumber].ai)
      if not ret.has_key(name):
        ret[name] = 0
      ret[name] += 1
    return ret

  # Play a single hand
  def playHand(self):
    self.resetHandState()

    # Fresh deck
    self.deck = Deck()

    # Deal hands
    for player in self.players:
      player.hand = self.draw(player, 6)

    if self.transcriptWriter:
      self.transcriptWriter.writeHandStart()

    currentPlayerNumber = 0
    # Normally this is currentPlayerNumber + 1, but in the case of a coup
    # fourre it gets changed to give the player another turn
    nextPlayerNumber = 1

    while True:
      currentPlayer = self.players[currentPlayerNumber]
      currentTeam = self.teams[currentPlayer.teamNumber]

      drewCardThisMove = None
      try:
        drewCardThisMove = self.draw(currentPlayer)
        currentPlayer.hand.append(drewCardThisMove)
      except IndexError:
        self.delayedAction = True

      if self.debug:
        print 'Hand contents:',
        print Cards.cardsToStrings(currentPlayer.hand)

      if len(currentPlayer.hand) == 0:
        totalHandSize = 0
        for player in self.players:
          totalHandSize += len(player.hand)
        if totalHandSize == 0:
          # Everyone's out of cards - game over
          break
        else:
          # Pass and let someone else go
          currentPlayerNumber = nextPlayerNumber
          nextPlayerNumber += 1
          if nextPlayerNumber >= len(self.players):
            nextPlayerNumber = 0
          continue

      state = self.makeState(currentPlayer)
      state.findValidPlays()
      # Store a copy of this locally, just in case the AI changes it
      validMoves = state.validMoves
      move = currentPlayer.ai.makeMove(state)

      # Replace invalid moves with a random discard
      if move not in validMoves:
        print 'Warning: invalid play'
        move = Move(Move.DISCARD, currentPlayer.hand[0])

      if self.debug:
        print currentPlayer,
        print move

      sanitizedPlayer = copy(currentPlayer)
      sanitizedPlayer.hand = []
      sanitizedPlayer.ai = None
      self.notifyPlayers(sanitizedPlayer, move)

      oldTarget = self.target
      self.handleMove(currentPlayer, currentTeam, move)
      if self.transcriptWriter:
        extensionWasDeclared = self.target > oldTarget
        self.transcriptWriter.writeMove(currentPlayer.number, drewCardThisMove, move, extensionWasDeclared)
      if self.tripComplete:
        break

      # Remove the card from the player's hand
      del currentPlayer.hand[currentPlayer.hand.index(move.card)]

      if self.debug:
        for team in self.teams:
          print team
        print ''

      # Go on to the next player. If a safety got played, nextPlayerNumber
      # got changed and will cause us to break out of the normal rotation
      currentPlayerNumber = nextPlayerNumber
      nextPlayerNumber += 1
      if nextPlayerNumber >= len(self.players):
        nextPlayerNumber = 0

    if self.debug:
      print 'Hand complete'

    if self.transcriptWriter:
      self.transcriptWriter.writeHandEnd()

    self.computeHandScores()

  def handleMove(self, currentPlayer, currentTeam, move, forceExtension = False):
    if True:  # To keep the indent level of all this the same as in upstream and make the diff prettier. :(
      currentPlayerNumber = currentPlayer.number

      # Handle moves
      if move.type == Move.PLAY:
        card = move.card
        type = Cards.cardToType(card)
        if type == Cards.MILEAGE:
          currentTeam.mileage += Cards.cardToMileage(card)
          currentTeam.mileagePile.append(card)
          if card == Cards.MILEAGE_200:
            currentTeam.safeTrip = False
            currentTeam.twoHundredsPlayed += 1
          if currentTeam.mileage == self.target:
            tempState = self.makeState(currentPlayer)
            if self.extensionPossible and (forceExtension or
                                           currentPlayer.ai.goForExtension(tempState)):
              if self.debug:
                print 'Player ' + str(currentPlayerNumber) + ' goes for the extension'
              self.extension = True
              self.extensionPossible = False
              self.target = 1000
            else:
              if self.debug:
                print 'Race complete'
              self.winner = currentPlayer.teamNumber
              self.tripComplete = True
              return
        elif type == Cards.REMEDY:
          currentTeam.battlePile.append(card)
          if card == Cards.REMEDY_END_OF_LIMIT:
            currentTeam.speedLimit = False
          else:
            currentTeam.needRemedy = Cards.REMEDY_GO
          if (card == Cards.REMEDY_GO
              or Cards.SAFETY_RIGHT_OF_WAY in currentTeam.safeties):
            currentTeam.needRemedy = None
            currentTeam.moving = True
        elif type == Cards.ATTACK:
          targetTeam = self.teams[(move.target)]

          # Check for coup fourre
          neededSafety = Cards.attackToSafety(card)
          coupFourrePlayerNumber = -1
          for targetPlayerNumber in targetTeam.playerNumbers:
            targetPlayer = self.players[targetPlayerNumber]
            if neededSafety in targetPlayer.hand:
              tempState = self.makeState(targetPlayer)
              if targetPlayer.ai and targetPlayer.ai.playCoupFourre(card, tempState):
                coupFourrePlayerNumber = targetPlayerNumber
              # There's only one of each safety, so if we found it, we don't
              # need to keep looking
              break

          if coupFourrePlayerNumber == -1:
            # The attack resolves
            targetTeam.battlePile.append(card)
            if card == Cards.ATTACK_SPEED_LIMIT:
              self.teams[move.target].speedLimit = True
            else:
              self.teams[move.target].moving = False
              self.teams[move.target].needRemedy = Cards.attackToRemedy(card)
          else:
            # Coup fourre
            self.playSafety(targetTeam, neededSafety)
            nextPlayerNumber = coupFourrePlayerNumber
            # Remove the safety from the player's hand
            del self.players[coupFourrePlayerNumber].hand[self.players[coupFourrePlayerNumber].hand.index(neededSafety)]
            # Draw an extra card to replace the one just played
            try:
              player = self.players[coupFourrePlayerNumber]
              cfCard = self.draw(player)
              player.hand.append(cfCard)
            except IndexError:
              cfCard = None
              pass
            targetTeam.coupFourres += 1
            cfMove = Move(Move.PLAY, neededSafety, None, True)
            if self.debug:
              print self.players[nextPlayerNumber],
              print cfMove
            cfPlayer = copy(self.players[nextPlayerNumber])
            cfPlayer.hand = []
            cfPlayer.ai = None
            self.notifyPlayers(cfPlayer, cfMove)
            if self.transcriptWriter:
              self.transcriptWriter.writeMove(cfPlayer.number,
                                              cfCard,
                                              cfMove,
                                              False)
        elif type == Cards.SAFETY:
          self.playSafety(currentTeam, card)
          nextPlayerNumber = currentPlayerNumber
        else:
          raise ValueError('Unknown card type!')
      elif move.type == Move.DISCARD:
        self.discardPile.append(move.card)

  def computeHandScores(self):
    # Look for a shut out
    teamsWithMileage = 0
    for team in self.teams:
      if team.mileage > 0:
        teamsWithMileage += 1
    
    # Now actually figure scores
    scoreSummary = ''
    handScoresByTeam = []
    totalScoresByTeam = []
    for team in self.teams:
      scoreSummary += 'Team ' + str(team.number) + "\n"
      team.handScore = team.mileage
      scoreSummary += '  ' + str(team.mileage) + " miles\n"
      team.handScore += 100 * len(team.safeties)
      scoreSummary += '  ' + str(len(team.safeties)) + ' safeties = ' + str(100 * len(team.safeties)) + "\n"
      team.handScore += 300 * team.coupFourres
      scoreSummary += '  ' + str(team.coupFourres) + ' coup fourres = ' + str(300 * team.coupFourres) + "\n"
      if len(team.safeties) == 4:
        scoreSummary += "  All four safeties = 500\n"
        team.handScore += 700

      if self.winner == team.number:
        team.handScore += 400
        scoreSummary += "  Trip complete = 400\n"
        if self.delayedAction:
          scoreSummary += "  Delayed action = 300\n"
          team.handScore += 300
        if team.safeTrip:
          scoreSummary += "  Safe trip = 300\n"
          team.handScore += 300
        if self.extension:
          scoreSummary += "  Extension = 200\n"
          team.handScore += 200
        if teamsWithMileage == 1:
          team.handScore += 500
          scoreSummary += "  Shut out = 500\n"
      scoreSummary += '  Total: ' + str(team.handScore) + "\n"
      team.totalScore += team.handScore
      handScoresByTeam.append(team.handScore)
      totalScoresByTeam.append(team.totalScore)

    if self.debug:
      print scoreSummary

    # Notify the players that the hand is over
    for player in self.players:
      if player.ai:
        player.ai.handEnded(scoreSummary)
        player.ai.handEnded2(handScoresByTeam, totalScoresByTeam)

  def notifyPlayers(self, movingPlayer, move):
    for player in self.players:
      player.ai.playerPlayed(movingPlayer, move)

  # This is a separate method since it gets called from two places in
  # playHand()
  def playSafety(self, team, card):
    team.safeties.append(card)
    if card == Cards.SAFETY_RIGHT_OF_WAY:
      team.speedLimit = False
    if Cards.remedyToSafety(team.needRemedy) == card:
      if (card == Cards.SAFETY_RIGHT_OF_WAY
       or Cards.SAFETY_RIGHT_OF_WAY in team.safeties):
        team.needRemedy = None
        team.moving = True
      else:
        team.needRemedy = Cards.REMEDY_GO
  
  # Make a customized state object for the player that includes
  # everything needed to make a decision, but doesn't expose private
  # information about other players
  def makeState(self, player):
    state = GameState()
    state.debug = self.debug
    # Pass copies, not the original objects, so the canonical ones can't
    # "accidentally" get modified by the AIs
    state.hand = copy(player.hand)
    state.discardPile = copy(self.discardPile)
    state.teams = deepcopy(self.teams)
    state.us = copy(self.teams[player.teamNumber])
    state.opponents = deepcopy(self.teams)
    del state.opponents[(player.teamNumber)]
    # Passed by value, doesn't need copying
    state.target = self.target
    state.cardsLeft = self.deck.cardsLeft()
    state.playerCount = len(self.players)
    return state

  def draw(self, player, count = 1):
    cards = self.deck.draw(count)
    if count == 1:
      player.ai.cardDrawn(cards)
    else:
      for card in cards:
        player.ai.cardDrawn(card)
    return cards
