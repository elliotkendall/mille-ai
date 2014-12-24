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
    odds = (self.cardsUnseen[safety] + self.cardsUnseen[remedy]) / max(self.numCardsUnseen, 1)

    # Boost likelihood by 50% for each remedy they've discarded.
    for player in team.playerNumbers:
      for _ in xrange(self.interestingRemedyDiscardsByPlayer[player][remedy]):
        odds *= 1.5

    return odds


  def makeMove(self, gameState):
    moves = gameState.validMoves
    discardCards = [move.card
                    if move.type == Move.DISCARD
                    else None
                    for move in moves]
    moveValues = dict((moves[i],
                       self.moveValue(moves[i], gameState, i, discardCards))
                      for i in xrange(len(moves)))
    #print "XXX"
    #for (move, value) in moveValues.iteritems():
    #  print "XXX: ...Move %s: %r" % (move, value)
    moves.sort(key=lambda move: moveValues[move],
               reverse=True)
    return moves[0]

  def moveValue(self, move, gameState, discardIdx, discardCards):
    # Value of a move is the amount it moves us closer to winning,
    # or (amount it harms an opponent / number of opponents), or
    # (for discard) expected value of replacement card.
    if move.type == Move.DISCARD:
      cardValue = self.cardValue(move.card,
                                 discardIdx,
                                 discardCards,
                                 gameState)
      # TODO: This isn't on the same scale as moveValue!
      # TODO: Factor in expected value of replacement card.
      # TODO: Constant needs tweaking...
      # TODO: This is *way* too quick to discard a remedy.  It discards
      #       a gasoline over a mileage card.
      #print "ZZZ: ...Value of %s: %r" % (move, cardValue)
      return (1 - cardValue/10) * 0.01

    # TODO: Factor in "safe trip" cost of playing 200km,
    # "shutout" cost of failing to play an attack,
    # and "delayed action" cost of failing to discard.
    gamePointsRemaining = max(Game.pointsToWin - gameState.us.totalScore, 0)

    card = move.card
    cardType = Cards.cardToType(card)
    if cardType == Cards.MILEAGE:
      # TODO: This assumes an extension.
      tripMileageRemaining = 1000 - gameState.us.mileage
      tripRemainingMileagePercentConsumed = Cards.cardToMileage(card) / tripMileageRemaining
      # TODO: Factor in delayed action, safe trip, shutout.
      # TODO: Assumes extension.
      if gamePointsRemaining > 0:
        gameRemainingPercentAdvancedAfterCompletingTrip = max(1.0, (400 + 200) / gamePointsRemaining)
      else:
        gameRemainingPercentAdvancedAfterCompletingTrip = 0

      # e.g. the game is currently at 0 points (0% done), and completing this trip will net 600 points
      # (600/5000=12% done).  And the trip is currently at 900km (100km remaining), and playing this mileage
      # card will get us to 1000k (100% of remaining distance.)  Value of playing this move is:
      #   1.00 * 0.12
      # TODO: This should be even more valuable, because it eliminates the possibility of future attacks.
      return tripRemainingMileagePercentConsumed * gameRemainingPercentAdvancedAfterCompletingTrip
    elif cardType == Cards.REMEDY:
      if card == Cards.REMEDY_END_OF_LIMIT and not gameState.us.speedLimit:
        return 0.0

      # If we need a remedy to move, and we have that remedy, it's a rather strong play!
      return 1.0
    elif cardType == Cards.SAFETY:
      # Adjust this to control how tightly we horde safeties for CF.
      return 0.6
    elif cardType == Cards.ATTACK:
      target = gameState.teamNumberToTeam(move.target)
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

      # By default, everyone is equally likely to win.
      priorOddsTargetWillWinGame = 1 / (len(gameState.opponents) + 1)

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
      maxScore = max([gameState.us.totalScore] +
                     [opponent.totalScore for opponent in gameState.opponents])
      gamePercentDone = maxScore / Game.pointsToWin

      # Next, figure out (based on current score) how likely the player is to win.
      # Assume that the player with the max score will prevail, and that their
      # opponents are proportionally likely to win based on their own scores.
      if maxScore == 0:
        aggregateTargetWinChance = priorOddsTargetWillWinGame
      else:
        currentScoreTargetWinChance = target.totalScore / maxScore

        # We've now computed two different odds of winning based on the current scores -- so,
        # not factoring in the current trip at all -- one "everyone is equally likely" and
        # one "base everything on current scores.  Combine them according to our certainty
        # in each metric, aka gamePercentDone.
        aggregateTargetWinChance = ((currentScoreTargetWinChance * gamePercentDone) +
                                    (priorOddsTargetWillWinGame * (1-gamePercentDone))) / 2

      # Fantastic, we now know how threatening this entity is in general.
      # But is attacking them going to make a difference on the current trip?
      # TODO: Assumes an extension.
      # TODO: Finish implementing this!  Factor in number of turns expected to remain,
      #       mileage cards opponent is likely to have/draw...
      targetTripCompletionChance = target.mileage / 1000

      # TODO: Add an "aggressiveness" constant?
      return ((1 - self.chanceOpponentHasProtection(target, card)) *
              aggregateTargetWinChance *
              targetTripCompletionChance)
            

    # than playing them outright, so that we can save safeties for coup fourre.
    if len(safeties) > 0:
      return safeties[0]

  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    # TODO: Don't go for it if we're way in the lead.
    return True

  def cardValue(self, card, cardIdx, cards, gameState):
    # moveIdx and cards let us disambiguate between two equal cards in our hand.
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
      mileageRemaining = 1000 - gameState.us.mileage
      if mileage > mileageRemaining:
        return 0
      elif mileage == 200 and gameState.us.twoHundredsPlayed >= 2:
        return 0
      else:
        return Cards.cardToMileage(card) / 25
    elif cardType == Cards.REMEDY:
      safety = Cards.remedyToSafety(card)
      attack = Cards.remedyToAttack(card)
      # Go is special because even if we have the safety (Right of Way),
      # we still want to hang onto it because we'll need to go after
      # getting attacked some other way.
      if card != Cards.REMEDY_GO and safety in gameState.us.safeties:
        return 0
      else:
        # Do we already have an equivalent safety in our hand?
        duplicateRemedies = 0
        for otherHandCard in cards:
          otherCardType = Cards.cardToType(otherHandCard)
          if otherCardType == Cards.REMEDY and otherHandCard == card:
            duplicateRemedies += 1
          elif otherCardType == Cards.SAFETY and safety == otherHandCard:
            return 0
          
        return max(1, 4 - duplicateRemedies) * (
          # The more likely this attack is to come up, the more valuable the remedy is.
          # TODO: For Go, *all* attacks count!
          self.cardsUnseen[attack] / max(self.numCardsUnseen, 1))
    elif cardType == Cards.SAFETY:
      if card in gameState.us.safeties:
        return 0
      else:
        # Do we already have an equivalent safety in our hand?
        for otherIdx in xrange(cardIdx):
          if cards[otherIdx] == card:
            return 0
        return 9
    elif cardType == Cards.ATTACK:
      safety = Cards.attackToSafety(card)
      remedy = Cards.attackToRemedy(card)

      targets = gameState.opponents
      totalTargets = len(targets)
      vulnerableTargets = totalTargets
      neededSafety = Cards.attackToSafety(card)
      for potentialTarget in targets:
        if neededSafety in potentialTarget.safeties:
          vulnerableTargets -= 1
        else:
          vulnerableTargets -= self.chanceOpponentHasProtection(
            potentialTarget, card)
      return (6 * (vulnerableTargets / totalTargets) * 
        # The more likely there is to be protection against this attack,
        # the less valuable the attack is.
        1-((self.cardsUnseen[safety] +
            self.cardsUnseen[remedy]) / max(self.numCardsUnseen, 1)))
    else:
      raise Exception("Unknown card type for %r: %r" % (card, cardType))
