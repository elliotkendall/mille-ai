"""
matthewg@zevils.com 's entry in the Mille Bornes AI competition.

TODOs from the web:
* Tweak discard strategy.
* "Safe trip" bonus for no 200s.
* Factor in number of points left in game, not just miles left in hand.
* Extension strategy: Factor in how many hazards and remedies in hand,
  mileage cards left in deck, mileage of opponents, points left in game.
  (Also, safeties that opponents have out.)
* Don't horde for CF as aggressively.  Want the bonus for getting safeties out.
* Delay ending game to get out safeties, run out the deck?
* Prioritize Go over attack?
* Use card counting: If all of an attack are out, discard the remedy.
* Save low-mileage cards for endgame.
* Watch opponent discards: If they discard remedies, they probably have the safety.
* There's only one of each safety, so if one opponent has it, nobody else will.

"""
from __future__ import division  # / == float, // == int

from mille.ai import AI
from mille.cards import Cards
from mille.deck import Deck
from mille.game import Game
from mille.move import Move

import collections


class MatthewgAI(AI):

  def __init__(self):
    self.resetCardCount()
    self.gameState = None

  def resetCardCount(self):
    # Doesn't attempt to account for a card in another player's hand.
    # If it's not in our hand, a tableau, or the discard pile, it
    # is possibly remaining.
    self.cardsUnseen = dict(Deck.composition)

    # Unlike GameState.cardsLeft, this also includes cards in
    # other players' hands.
    self.numCardsUnseen = sum(self.cardsUnseen.values())

    # Keep track of how many remedies of each type have been
    # discarded by each player.  It's a sign they might be hoarding
    # a safety for a CF.  When a player *plays* that remedy, this
    # count resets (since that's a sign that they *don't* have the
    # safety.)
    self.interestingRemedyDiscardsByPlayer = collections.defaultdict(
      lambda: dict((remedy, 0) for remedy in Cards.REMEDIES))

  def cardSeen(self, card):
    self.cardsUnseen[card] -= 1
    self.numCardsUnseen -= 1

  def playerPlayed(self, player, move):
    self.cardSeen(move.card)
    if Cards.cardToType(move.card) == Cards.REMEDY and move.card != Cards.REMEDY_GO:
      if move.type == Move.DISCARD:
        self.interestingRemedyDiscardsByPlayer[player][move.card] += 1
      else:
        self.interestingRemedyDiscardsByPlayer[player][move.card] = 0

  def cardDrawn(self, card):
    self.cardSeen(card)

  def handEnded(self, scoreSummary):
    self.resetCardCount()

  def chanceOpponentHasProtection(self, team, attack):
    # Chance that a particular opponent has protection from a particular attack in their hand.
    safety = Cards.attackToSafety(attack)
    remedy = Cards.attackToRemedy(attack)

    # Odds based on number of the card lurking out there somewhere.
    odds = self.percentOfCardsRemaining(safety, remedy)

    # Boost likelihood by 50% for each remedy they've discarded.
    for player in team.playerNumbers:
      for _ in xrange(self.interestingRemedyDiscardsByPlayer[player][remedy]):
        odds *= 1.5

    return odds


  def makeMove(self, gameState):
    self.gameState = gameState
    try:
      moves = self.gameState.validMoves
      discardCards = [move.card
                      if move.type == Move.DISCARD
                      else None
                      for move in moves]
      moveValues = dict((moves[i],
                         self.moveValue(moves[i], i, discardCards))
                        for i in xrange(len(moves)))
      #print "XXX"
      #for (move, value) in moveValues.iteritems():
      #  print "XXX: ...Move %s: %r" % (move, value)
      moves.sort(key=lambda move: moveValues[move],
                 reverse=True)
    finally:
      self.gameState = None
    return moves[0]

  def moveValue(self, move, discardIdx, discardCards):
    # Value of a move is the amount it moves us closer to winning,
    # or (amount it harms an opponent / number of opponents), or
    # (for discard) expected net value of replacement card.

    card = move.card
    cardType = Cards.cardToType(card)

    if move.type == Move.DISCARD:
      cardValue = self.cardValue(card, discardIdx, discardCards)
      # TODO: Factor in expected value of replacement card.
      return (1 - cardValue) * 0.01

    # TODO: Factor in "safe trip" cost of playing 200km,
    # "shutout" cost of failing to play an attack,
    # and "delayed action" cost of failing to discard.

    card = move.card
    cardType = Cards.cardToType(card)
    if cardType == Cards.MILEAGE:
      # TODO: Avoid playing a 75 unless we have a 25,
      # and avoid playing a 25 unless we need it.
      value = self.mileageCardValue(card)
      mileage = Cards.cardToMileage(card)
      if mileage == self.gameState.target - self.gameState.us.mileage:
        return 1.0
      elif mileage == 25 and len([card for card in discardCards if card == card]) < 2:
        # Don't play our last 25km (unless we need to).
        return 0.0
      else:
        return value
    elif cardType == Cards.REMEDY:
      if card == Cards.REMEDY_END_OF_LIMIT and not self.gameState.us.speedLimit:
        return 0.0

      # If we need a remedy to move, and we have that remedy, it's a rather strong play!
      return 1.0
    elif cardType == Cards.SAFETY:
      # Adjust this to control how tightly we horde safeties for CF.
      return 0.6
    elif cardType == Cards.ATTACK:
      target = self.gameState.teamNumberToTeam(move.target)
      if card == Cards.ATTACK_SPEED_LIMIT:
        # If they're already under a speed limit, don't bother with another.
        if target.speedLimit:
          return 0.0
      else:
        # If they already need a remedy, don't bother with another -- unless they need
        # "go", in which case the attack is still worthwhile because now they need
        # the specific attack's remedy *in addition to* go.
        if target.needRemedy and target.needRemedy != Cards.REMEDY_GO:
          return 0.0


      # Fantastic, we now know how threatening this entity is in general.
      # But is attacking them going to make a difference on the current trip?
      # TODO: Assumes an extension.
      # TODO: Finish implementing this!  Factor in number of turns expected to remain,
      #       mileage cards opponent is likely to have/draw...
      targetTripCompletionChance = target.mileage / 1000

      # TODO: Add an "aggressiveness" constant?
      return ((1 - self.chanceOpponentHasProtection(target, card)) *
              self.chanceTeamWillWin(target) *
              self.chanceTeamWillCompleteTrip(target))
            

    # than playing them outright, so that we can save safeties for coup fourre.
    if len(safeties) > 0:
      return safeties[0]

  def mileageCardValue(self, card):
    # TODO: This assumes an extension.
    tripMileageRemaining = 1000 - self.gameState.us.mileage
    tripRemainingMileagePercentConsumed = Cards.cardToMileage(card) / tripMileageRemaining
    # TODO: Factor in delayed action, safe trip, shutout.
    # TODO: Assumes extension.

    # e.g. the game is currently at 0 points (0% done), and completing this trip will net 600 points
    # (600/5000=12% done).  And the trip is currently at 900km (100km remaining), and playing this mileage
    # card will get us to 1000k (100% of remaining distance.)  Value of playing this move is:
    #   1.00 * 0.12
    # TODO: This should be even more valuable, because it eliminates the possibility of future attacks.
    return tripRemainingMileagePercentConsumed * self.valueOfPoints(400 + 200, self.gameState.us)


  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    # TODO: Don't go for it if we're way in the lead.
    return True

  def cardValue(self, card, cardIdx, cards):
    # cardIdx and cards let us disambiguate between two equal cards in our hand.
    #
    # All equally worthless:
    # * Safeties in play or elsewhere in our hand
    # * Remedies for safeties in play or elsewhere in our hand
    # * 200mi if we've already maxed out
    # * Mileage > distance remaining (assuming extension will be played)
    #   TODO: ...but what if an extension *won't* be played?
    # * Safeties we have in our hand
    #
    # The good stuff:
    # * Mileage cards: 1pt per mileage/25
    # * Remedy: 4pt, minus 1pt for duplicates in our hand (min=1).
    # * Unplayed safeties: 9pt
    # * Attack: 6pt * percentage of opponents vulnerable to it

    cardType = Cards.cardToType(card)
    if cardType == Cards.MILEAGE:
      mileage = Cards.cardToMileage(card)
      mileageRemaining = 1000 - self.gameState.us.mileage
      if mileage > mileageRemaining:
        return 0.0
      elif mileage == 200 and self.gameState.us.twoHundredsPlayed >= 2:
        return 0.0
      elif mileage == 25 and cards.index(card) == cardIdx:
        # Try to hold onto a single 25km card in case we need it to finish.
        return 1.0
      else:
        return self.mileageCardValue(card)
    elif cardType == Cards.REMEDY:
      # Go is special because even if we have the safety (Right of Way),
      # we still want to hang onto it because we'll need to go after
      # getting attacked some other way.
      if card == Cards.REMEDY_GO:
        # If we have all the safeties, and we're moving, Go is useless.
        # Otherwise, it's awesome.
        if (self.gameState.us.moving and
            (len(self.gameState.us.safeties) +
             len([c for c in cards if Cards.cardToType(c) == Cards.SAFETY])) == len(Cards.SAFETIES)):
          return 0.0
        else:
          return 1.0
      elif Cards.remedyToSafety(card) in self.gameState.us.safeties:
        return 0.0
      else:
        # Do we already have an equivalent safety in our hand?
        duplicateRemedies = -1
        for otherHandCard in cards:
          otherCardType = Cards.cardToType(otherHandCard)
          if otherCardType == Cards.REMEDY and otherHandCard == card:
            duplicateRemedies += 1
          elif otherCardType == Cards.SAFETY and otherHandCard == card:
            # We're holding the safety, the remedy is useless.
            return 0.0

        # Factor in:
        # 1. Value of taking a turn.
        # 2. Likelihood of getting hit with this attack.
        #    (Number of attacks remaining / number of teams in game.)
        # 3. Likelihood of drawing another remedy (or the safety.)
        return (self.valueOfPoints(self.expectedTurnPoints(self.gameState.us),
                                   self.gameState.us) *
                (self.percentOfCardsRemaining(Cards.remedyToAttack(card)) /
                 len(self.gameState.opponents) + 1) *
                (1-self.percentOfCardsRemaining(card, Cards.remedyToSafety(card))))
    elif cardType == Cards.SAFETY:
      # Never discard a safety!
      # (Assuming default deck composition of 1 of each type...)
      return 1.0
    elif cardType == Cards.ATTACK:
      safety = Cards.attackToSafety(card)
      remedy = Cards.attackToRemedy(card)

      valuesPerTarget = []
      for target in self.gameState.opponents:
        if safety in target.safeties:
          valuesPerTarget.append(0.0)
        else:
          valuesPerTarget.append(
            (1-self.chanceOpponentHasProtection(target, card)) *
            (1-self.percentOfCardsRemaining(safety, remedy)) *
            self.valueOfPoints(self.expectedTurnPoints(target), target))
      return sum(valuesPerTarget)/len(valuesPerTarget)
    else:
      raise Exception("Unknown card type for %r: %r" % (card, cardType))

  def valueOfPoints(self, points, team):
    gamePointsRemaining = max(Game.pointsToWin - team.totalScore, 0)
    if gamePointsRemaining > 0:
      return max(1.0, points / gamePointsRemaining)
    else:
      return 0.5

  def chanceTeamWillCompleteTrip(self, team):
    needMileage = self.gameState.target - team.mileage
    validMileageCards = [card
                         for card in Cards.MILEAGE_CARDS
                         if Cards.cardToMileage(card) <= needMileage]
    validMileagePct = self.percentOfCardsRemaining(*validMileageCards)
    unseenTotalMileage = sum([self.cardsUnseen[card]
                              for card in validMileageCards])
    if unseenTotalMileage < needMileage:
      return 0.0
    else:
      # TODO: Factor in how close everyone is to finishing the trip,
      # and how many cards are left in the deck.
      return validMileagePct * (needMileage / unseenTotalMileage)


  def chanceTeamWillWin(self, team):
    # First, figure out how likely this team is to win.
    # By default, everyone is equally likely to win.
    priorOddsTargetWillWinGame = 1 / (len(self.gameState.opponents) + 1)

    # Factor in how close everyone is to 5k points,
    # and also how close this opponent is to completing the trip.
    # If this opponent is at 4.9k pts and everyone else is at 1k,
    # opponent is crushingly likely to win.  OTOH if everyone
    # else is at 975km on the trip and this opponent is at 0km,
    # they're not going to win the trip anyway...
    #
    # First, figure out the "game percent done" -- how close
    # to done are we?  The closer we are to done, the more
    # certain we are in predicting the winner.
    maxScore = max([self.gameState.us.totalScore] +
                   [opponent.totalScore for opponent in self.gameState.opponents])
    gamePercentDone = maxScore / Game.pointsToWin

    # Next, figure out (based on current score) how likely the player is to win.
    # Assume that the player with the max score will prevail, and that their
    # opponents are proportionally likely to win based on their own scores.
    if maxScore == 0:
      aggregateTargetWinChance = priorOddsTargetWillWinGame
    else:
      currentScoreTargetWinChance = team.totalScore / maxScore

      # We've now computed two different odds of winning based on the current scores -- so,
      # not factoring in the current trip at all -- one "everyone is equally likely" and
      # one "base everything on current scores.  Combine them according to our certainty
      # in each metric, aka gamePercentDone.
      aggregateTargetWinChance = ((currentScoreTargetWinChance * gamePercentDone) +
                                  (priorOddsTargetWillWinGame * (1-gamePercentDone))) / 2

    return aggregateTargetWinChance

  def expectedTurnPoints(self, team):
    # TODO: Implement me!
    return 75

  def percentOfCardsRemaining(self, *cards):
    cardCount = 0
    for card in cards:
      cardCount += self.cardsUnseen[card]
    return cardCount / max(self.numCardsUnseen, cardCount, 1)
