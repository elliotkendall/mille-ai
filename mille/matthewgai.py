"""
matthewg@zevils.com 's entry in the Mille Bornes AI competition.

TODOs from the web:
* Tweak discard strategy.
* "Safe trip" bonus for no 200s. -- make this more sophisticated
* Factor in number of points left in game, not just miles left in hand.
* Extension strategy: Factor in how many hazards and remedies in hand,
  mileage cards left in deck, mileage of opponents, points left in game.
  (Also, safeties that opponents have out.)
* Delay ending game to get out safeties, run out the deck?
* Prioritize Go over attack?
* Save low-mileage cards for endgame.

"""
from __future__ import division  # / == float, // == int

from mille.ai import AI
from mille.cards import Cards
from mille.deck import Deck
from mille.game import Game
from mille.move import Move

import collections
import csv
import math
import os
import random
import re


class Constants(object):
  DEBUG = False

  @classmethod
  def debug(klass, msg, *args):
    if klass.DEBUG:
      print msg % tuple(arg() if callable(arg) else arg
                        for arg in args)    

  @classmethod
  def populationFile(klass, playerCount):
    return os.path.join(os.path.dirname(__file__),
                        "matthewgai_population_%d" % playerCount)

  @classmethod
  def savePopulation(klass, playerCount, population):
    with open(klass.populationFile(playerCount), "w") as f:
      csvWriter = csv.writer(f)
      for (member, fitness) in population:
        csvWriter.writerow((fitness,) + member.toTuple())

  @classmethod
  def loadPopulation(klass, playerCount):
    population = []
    with open(klass.populationFile(playerCount), "r") as f:
      csvReader = csv.reader(f)
      for line in csvReader:
        population.append((klass(*map(float, line[1:])), float(line[0])))
    return population

  def __init__(self,
               remedy_discard_boost,
               discard_move_value_penalty,
               safety_horde_factor,
               attack_quality_mod_stop,
               attack_quality_mod_limit,
               dupe_penalty_factor,
               safe_trip_factor,
               aggressiveness,
               mileage_boost):
    self.remedy_discard_boost = remedy_discard_boost
    self.discard_move_value_penalty = discard_move_value_penalty
    self.safety_horde_factor = safety_horde_factor
    self.attack_quality_mod_stop = attack_quality_mod_stop
    self.attack_quality_mod_limit = attack_quality_mod_limit
    self.dupe_penalty_factor = dupe_penalty_factor
    self.safe_trip_factor = safe_trip_factor
    self.aggressiveness = aggressiveness
    self.mileage_boost = mileage_boost

    self.hand_fitness_scores = []

  def clone(self):
    return self.__class__(*self.toTuple())

  def toTuple(self):
    return (self.remedy_discard_boost,
            self.discard_move_value_penalty,
            self.safety_horde_factor,
            self.attack_quality_mod_stop,
            self.attack_quality_mod_limit,
            self.dupe_penalty_factor,
            self.safe_trip_factor,
            self.aggressiveness,
            self.mileage_boost)

CONSTANT_POPULATIONS_FOR_PLAYERCOUNT = {
  2: Constants.loadPopulation(2),
  3: Constants.loadPopulation(3),
  4: Constants.loadPopulation(4),
  6: Constants.loadPopulation(6),
}

INITIAL_CONSTANTS_FOR_PLAYERCOUNT = {
  2: Constants(remedy_discard_boost = 1.5,
               discard_move_value_penalty = 0.001,
               safety_horde_factor = 0.6,
               attack_quality_mod_stop = 0.25,
               attack_quality_mod_limit = 0.25,
               dupe_penalty_factor = 3,
               safe_trip_factor = 0.4,
               aggressiveness = 1.0,
               mileage_boost = 1.2,
               ),
  3: Constants(remedy_discard_boost = 1.5,
               discard_move_value_penalty = 0.001,
               safety_horde_factor = 0.6,
               attack_quality_mod_stop = 0.25,
               attack_quality_mod_limit = 0.25,
               dupe_penalty_factor = 3,
               safe_trip_factor = 0.4,
               aggressiveness = 1.0,
               mileage_boost = 1.2,
               ),
  4: Constants(remedy_discard_boost = 1.5,
               discard_move_value_penalty = 0.001,
               safety_horde_factor = 0.6,
               attack_quality_mod_stop = 0.25,
               attack_quality_mod_limit = 0.25,
               dupe_penalty_factor = 3,
               safe_trip_factor = 0.4,
               aggressiveness = 1.0,
               mileage_boost = 1.2,
               ),
  6: Constants(remedy_discard_boost = 1.5,
               discard_move_value_penalty = 0.001,
               safety_horde_factor = 0.6,
               attack_quality_mod_stop = 0.25,
               attack_quality_mod_limit = 0.25,
               dupe_penalty_factor = 3,
               safe_trip_factor = 0.4,
               aggressiveness = 1.0,
               mileage_boost = 1.2,
               ),
}

def ConstantsForPlayerCount(playerCount):
  if not CONSTANT_POPULATIONS_FOR_PLAYERCOUNT[playerCount]:
    adam = INITIAL_CONSTANTS_FOR_PLAYERCOUNT[playerCount].toTuple()
    steve = adam
    population = []
  else:
    population = CONSTANT_POPULATIONS_FOR_PLAYERCOUNT[playerCount]
    # Sort population by fitness.
    population.sort(key=lambda c: c[1])
    # Enforce population cap.
    population = population[0:1000]
    Constants.debug("Population for %d:\n%s\n",
                    playerCount,
                    lambda: "".join(map(lambda p: "  %r: %r\n" % (p[1],
                                                                  p[0].toTuple()),
                                        population)))
    Constants.savePopulation(playerCount, population)

    # Pick two individuals to breed.  Generate two random numbers in
    # the range [0, totalFitness).  For each number, start at the
    # least-fit member and keep going until we've seen that much
    # fitness.
    totalFitness = 0  # Bally!
    for member in population:
      totalFitness += member[1]

    def lookingForMisterGoodConstant():
      luckyNumber = random.choice(range(int(totalFitness)))
      seenFitness = 0
      for (c, fitness) in population:
        seenFitness += fitness
        if seenFitness >= luckyNumber:
          return c
      return population[-1][0]
    adam = lookingForMisterGoodConstant().toTuple()
    steve = lookingForMisterGoodConstant().toTuple()

  # Set mutation rate high at first to generate a diverse initial population.
  # ...well, at *very* first, set it to 0 so that we get a reasonable baseline.
  if len(population) < 10:
    mutationOdds = 0.0
  elif len(population) < 900:
    mutationOdds = 0.25
  else:
    mutationOdds = 0.05

  darlingBundleOfJoy = []
  for i in xrange(len(adam)):
    darlingBundleOfJoy.append((adam[i]+steve[i])/2)
    if random.random() < mutationOdds:
      # Two eyes good, three eyes better?
      darlingBundleOfJoy[-1] *= random.choice([0, 1]) + random.choice([7, 8, 9])/10
  Constants.debug("Bred %r and %r to produce %r -- mazel tov, it's a tuple!",
                  adam, steve, darlingBundleOfJoy)
  return Constants(*darlingBundleOfJoy)

def cacheComputationForTurn(fn):
  def _callOncePerTurn(ai, *args, **kwargs):
    # Flatten kwargs into a tuple of (k1, v1, k2, v2, ..., kn, vn)
    sig = tuple([fn.__name__] + map(repr, args) + map(repr, reduce(lambda a, b: a + b, kwargs.items(), tuple())))
    if sig in ai.turnCache:
      return ai.turnCache[sig]
    else:
      ret = fn(ai, *args, **kwargs)
      ai.turnCache[sig] = ret
      return ret
  return _callOncePerTurn


class MatthewgAI(AI):
  constants = None
  constants_playercount = None

  def __init__(self):
    self.resetCardCount()
    self.resetTurnCache()
    self.gameState = None

  def debug(self, msg, *args):
    if self.gameState and self.gameState.debug:
      print msg % tuple(arg() if callable(arg) else arg
                        for arg in args)

  def resetTurnCache(self):
    self.turnCache = {}

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
    self.debug("After seeing %s, unseen cards:\n%s",
               Cards.cardToString(card),
               self.unseenCardsToString)

  @cacheComputationForTurn
  def unseenCardsToString(self):
    ret = []
    for card in xrange(max(Deck.composition.keys()) + 1):
      ret.append("  %s: %d\n" % (Card.cardToString(card), self.cardsUnseen[card]))
    return "".join(ret)

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

  @cacheComputationForTurn
  def teams(self):
    return [self.gameState.us] + self.gameState.opponents

  @cacheComputationForTurn
  def playerCount(self):
    return sum(map(lambda team: len(team.playerNumbers), self.teams()))

  @cacheComputationForTurn
  def chanceOpponentHasProtection(self, team, attack):
    # Chance that a particular opponent has protection from a particular attack in their hand.
    safety = Cards.attackToSafety(attack)
    remedy = Cards.attackToRemedy(attack)

    if safety in team.safeties:
      self.debug("Team %d has already played safety v. %s",
                 team.number,
                 Cards.cardToString(attack))
      return 1.0

    # Odds based on number of the card lurking out there somewhere.
    odds = self.percentOfCardsRemaining(safety, remedy)

    # Boost likelihood by 50% for each remedy they've discarded.
    remedyDiscards = 0
    for player in team.playerNumbers:
      for _ in xrange(self.interestingRemedyDiscardsByPlayer[player][remedy]):
        remedyDiscards += 1
        odds *= self.__class__.constants.remedy_discard_boost

    self.debug("Team %d protection odds %r v. %s, based on %d safety %d remedy %d discards.",
               team.number,
               odds,
               Cards.cardToString(attack),
               self.cardsUnseen[safety],
               self.cardsUnseen[remedy],
               remedyDiscards)
    return odds


  def makeMove(self, gameState):
    self.resetTurnCache()
    self.gameState = gameState
    if not self.__class__.constants or self.__class__.constants_playercount != self.playerCount():
      self.__class__.constants = ConstantsForPlayerCount(self.playerCount())
      self.__class__.constants_playercount = self.playerCount()

    # Data we want available during hand score evaluation, when gamestate is absent.
    self.usTeamNumber = self.gameState.us.number
    self._playerCount = self.playerCount()

    try:
      moves = self.gameState.validMoves
      discardCards = [move.card
                      if move.type == Move.DISCARD
                      else None
                      for move in moves]
      moveValues = dict((moves[i],
                         self.moveValue(moves[i], i, discardCards))
                        for i in xrange(len(moves)))

      moves.sort(key=lambda move: moveValues[move],
                 reverse=True)
      self.debug("Moves:\n%s",
                 lambda: "".join(["  %r: %s\n" % (moveValues[move], move)
                                  for move in moves]))
    finally:
      self.gameState = None
    return moves[0]

  @cacheComputationForTurn
  def moveValue(self, move, discardIdx, discardCards):
    # Value of a move is the amount it moves us closer to winning,
    # or (amount it harms an opponent / number of opponents), or
    # (for discard) expected net value of replacement card.

    card = move.card
    cardType = Cards.cardToType(card)

    if move.type == Move.DISCARD:
      cardValue = self.cardValue(card, discardIdx, discardCards)
      # TODO: Factor in expected value of replacement card.
      return (1 - cardValue) * self.__class__.constants.discard_move_value_penalty

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

      if mileage == 200 and self.gameState.us.twoHundredsPlayed == 0:
        safeTripFactor = self.__class__.constants.safe_trip_factor
      else:
        safeTripFactor = 1.0

      if mileage == self.gameState.target - self.gameState.us.mileage:
        return 1.0 * safeTripFactor
      elif mileage == 25 and len([card for card in discardCards if card == card]) < 2:
        # Don't play our last 25km (unless we need to).
        return 0.0
      else:
        return value * safeTripFactor
    elif cardType == Cards.REMEDY:
      if card == Cards.REMEDY_END_OF_LIMIT and not self.gameState.us.speedLimit:
        return 0.0

      # If we need a remedy to move, and we have that remedy, it's a rather strong play!
      return 1.0
    elif cardType == Cards.SAFETY:
      return self.__class__.constants.safety_horde_factor
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

      # TODO: Balance these, and also factor in chance opponent can get protection in the future.
      # And also factor in trip distance remaining for speed limit.
      if card == Cards.ATTACK_STOP:
        attackQualityModifier = self.__class__.constants.attack_quality_mod_stop
      elif card == Cards.ATTACK_SPEED_LIMIT:
        attackQualityModifier = self.__class__.constants.attack_quality_mod_limit
      else:
        attackQualityModifier = 1.0

      # TODO: Add an "aggressiveness" constant?
      return ((1 - self.chanceOpponentHasProtection(target, card)) *
              self.chanceTeamWillWin(target) *
              self.chanceTeamWillCompleteTrip(target) *
              attackQualityModifier *
              self.__class__.constants.aggressiveness)


    # than playing them outright, so that we can save safeties for coup fourre.
    if len(safeties) > 0:
      return safeties[0]

  @cacheComputationForTurn
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
    ret = tripRemainingMileagePercentConsumed * self.valueOfPoints(400 + 200, self.gameState.us) * self.__class__.constants.mileage_boost
    self.debug("Value of %dkm: %r, since it covers %r of remaining trip distance.",
               Cards.cardToMileage(card),
               ret,
               tripRemainingMileagePercentConsumed)
    return ret


  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    # TODO: Don't go for it if we're way in the lead.
    return True

  @cacheComputationForTurn
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

    # How many of this card do we already have in our hand?
    numDuplicates = len([c for c in cards if c == card])
    # Make this card less valuable if we have more if it on our hand.
    # The obvious thing to do is a straight divisor:
    # If we have 2 dupes, value each at 1/2; if 3, value each at 1/3.
    # But that's too severe, having 2 200km is more valuable than having
    # 1 200km!  So, we take the "duplicate fraction", 1/numDuplicates,
    # and we want to scale down *the inverse of that* to bring it
    # nearer to 1 (to reduce the severity of the penalty), and then
    # invert again to cancel out the inversion.
    dupeFrac = 1/numDuplicates
    dupePenaltyFactor = self.__class__.constants.dupe_penalty_factor
    dupeCoefficient = 1-(1-dupeFrac)/dupePenaltyFactor

    cardType = Cards.cardToType(card)
    if cardType == Cards.MILEAGE:
      mileage = Cards.cardToMileage(card)
      mileageRemaining = 1000 - self.gameState.us.mileage
      if mileage > mileageRemaining:
        return 0.0 * dupeCoefficient
      elif mileage == 200 and self.gameState.us.twoHundredsPlayed >= 2:
        return 0.0 * dupeCoefficient
      elif mileage == 25 and cards.index(card) == cardIdx:
        # Try to hold onto a single 25km card in case we need it to finish.
        return 1.0 * dupeCoefficient
      else:
        return self.mileageCardValue(card) * dupeCoefficient
    elif cardType == Cards.REMEDY:
      
      # Attacks that could necessitate this card.
      if card == Cards.REMEDY_GO:
        relevantAttacks = Cards.ATTACKS[:]
      else:
        relevantAttacks = [Cards.remedyToAttack(card)]

      relevantAttacks = [c for c in relevantAttacks
                         if not Cards.attackToSafety(c) in self.gameState.us.safeties + cards]

      # Factor in:
      # 1. Value of taking a turn.
      # 2. Likelihood of getting hit with a relevant attack.
      #    (Number of attacks remaining / number of teams in game.)
      #    NB: If no attacks are relevant, this will be 0.
      # TODO: Also add likelihood of drawing another remedy (or the safety.)
      turnPoints = self.expectedTurnPoints(self.gameState.us)
      turnPointValue = self.valueOfPoints(turnPoints, self.gameState.us)
      # Hold onto at least one of the card if we already know we need it!
      if (cards.index(card) == cardIdx and
          ((not self.gameState.us.moving and card == Cards.REMEDY_GO) or
           (self.gameState.us.speedLimit and card == Cards.REMEDY_END_OF_LIMIT) or
           (self.gameState.us.needRemedy and card == self.gameState.us.needRemedy))):
        self.debug("We need %s, attack on us odds == 1.0!", Cards.cardToString(card))
        attackOnUsOdds = 1.0
      else:
        attackOdds = self.percentOfCardsRemaining(*relevantAttacks) * self.expectedTurnsLeft()
        attackOnUsOdds = attackOdds / (len(self.gameState.opponents) + 1)
      value = turnPointValue * attackOnUsOdds
      self.debug("Card %s val: %r = %r * %r = val(%d) * pctLeft(%s)/#teams",
                 Cards.cardToString(card),
                 value,
                 turnPointValue, attackOnUsOdds,
                 turnPoints,
                 ",".join([Cards.cardToString(c) for c in relevantAttacks]))
      return value * dupeCoefficient
    elif cardType == Cards.SAFETY:
      # Never discard a safety!
      # (Assuming default deck composition of 1 of each type...)
      return 1.0 * dupeCoefficient
    elif cardType == Cards.ATTACK:
      safety = Cards.attackToSafety(card)
      remedy = Cards.attackToRemedy(card)

      valuesPerTarget = []
      for target in self.gameState.opponents:
        valuesPerTarget.append(
          (1-self.chanceOpponentHasProtection(target, card)) *
          (1-self.percentOfCardsRemaining(safety, remedy)) *
          self.valueOfPoints(self.expectedTurnPoints(target), target))
      return sum(valuesPerTarget)/len(valuesPerTarget) * dupeCoefficient
    else:
      raise Exception("Unknown card type for %r: %r" % (card, cardType))

  @cacheComputationForTurn
  def valueOfPoints(self, points, team):
    gamePointsRemaining = max(Game.pointsToWin - team.totalScore, 0)
    if gamePointsRemaining > 0:
      ret = min(1.0, points / gamePointsRemaining)
    else:
      ret = 0.5
    self.debug("Value of %d points to team %d: %r (%d remaining)",
               points, team.number, ret, gamePointsRemaining)
    return ret

  @cacheComputationForTurn
  def chanceTeamWillCompleteTrip(self, team):
    if self.useMonteCarloSimulation():
      self.debug("Using monte carlo method for team trip completion estimate.")
      teamResults = [result[team.number + 1]
                     for result
                     in self.monteCarloMileageSimulation()]
      completionCount = 0
      for result in teamResults:
        if result == 0:
          completionCount += 1
      ret = completionCount/len(teamResults)
      self.debug("%r chance that %d will complete trip (%d/%d)",
                 ret, team.number, completionCount, len(teamResults))
    else:
      self.debug("Using card-counting method for team trip completion estimate.")
      turnsLeft = self.deckExhaustionTurnsLeft()
      playersOnTeam = len(team.playerNumbers)
      teamMovesLeft = turnsLeft * playersOnTeam

      if team.moving:
        goCoeff = 1.0
      else:
        goCoeff = min(1.0, self.percentOfCardsRemaining(Cards.REMEDY_GO) * teamMovesLeft)

      if team.needRemedy and team.needRemedy != Cards.REMEDY_GO:
        remedyCoeff = min(1.0, self.percentOfCardsRemaining(
            team.needRemedy,
            Cards.remedyToSafety(team.needRemedy)) * teamMovesLeft)
      else:
        remedyCoeff = 1.0

      if goCoeff == 0.0 or remedyCoeff == 0.0:
        self.debug("Team %d can't complete trip due to remedy unavailable.", team.number)
        return 0.0

      needMileage = 1000 - team.mileage
      validMileageCards = [card
                           for card in Cards.MILEAGE_CARDS
                           if Cards.cardToMileage(card) <= needMileage]
      validMileageCards.sort(reverse=True)
      validMileagePct = self.percentOfCardsRemaining(*validMileageCards)
      unseenTotalMileage = sum([Cards.cardToMileage(card) * self.cardsUnseen[card]
                                for card in validMileageCards])
      if unseenTotalMileage < needMileage:
        self.debug("Not enough mileage left in deck for team %d to complete trip.",
                   team.number)
        ret = 0.0
      else:
        ret = min(1.0,
                  (validMileagePct *
                   (unseenTotalMileage / needMileage) *
                   teamMovesLeft *
                   remedyCoeff *
                   goCoeff))
        self.debug("Team %d has %r of trip completion, based on crude card count: %r * (%r / %r) * %r * %r * %r",
                   team.number,
                   ret,
                   validMileagePct,
                   unseenTotalMileage,
                   needMileage,
                   teamMovesLeft,
                   remedyCoeff,
                   goCoeff)

    return ret

  @cacheComputationForTurn
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
    maxScore = max(map(lambda team: team.totalScore,
                       self.teams()))
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

    self.debug("%r chance that team %d will win (game %r done, team has %d/%d max %d.)",
               aggregateTargetWinChance, team.number, gamePercentDone, team.totalScore, Game.pointsToWin, maxScore)
    return aggregateTargetWinChance

  @cacheComputationForTurn
  def expectedTurnPoints(self, team):
    # TODO: Implement me!
    return 75

  @cacheComputationForTurn
  def percentOfCardsRemaining(self, *cards):
    cardCount = 0
    for card in cards:
      cardCount += self.cardsUnseen[card]
    return cardCount / max(self.numCardsUnseen, cardCount, 1)

  @cacheComputationForTurn
  def monteCarloMileageSimulation(self):
    # Returns a list of many (turns elapsed, team 0 trip mileage remaining, team 1 trip remaining, ...)
    # TODO: Assumes extension.
    results = []
    for _ in xrange(100):
      needMileage = dict((team.number, team.mileage) for team in self.teams())
      moving = dict((team.number, team.moving) for team in self.teams())
      needRemedy = dict((team.number, team.needRemedy) for team in self.teams())
      twoHundredsPlayed = dict((team.number, team.twoHundredsPlayed) for team in self.teams())

      tripCompletedBy = None
      deck = collections.deque()
      for (card, qty) in self.cardsUnseen.iteritems():
        for _ in xrange(qty):
          deck.append(card)
      random.shuffle(deck)

      turnsElapsed = 1
      while deck:
        for currentTurnTeam in self.teams():
          if not deck:
            break

          teamNo = currentTurnTeam.number
          teamNeedMileage = needMileage[teamNo]
          teamNeedRemedy = needRemedy[teamNo]
          teamMoving = moving[teamNo]
          teamTwoHundredsPlayed = twoHundredsPlayed[teamNo]
          if teamNeedRemedy:
            teamNeedSafety = Cards.remedyToSafety(teamNeedRemedy)
          else:
            teamNeedSafety = None

          for playerNum in currentTurnTeam.playerNumbers:
            if tripCompletedBy == playerNum:
              deck = None
              break
            if not deck:
              break

            card = deck.pop()
            cardType = Cards.cardToType(card)
            if Cards.cardToType(card) != Cards.MILEAGE:
              if card == Cards.REMEDY_GO:
                teamMoving = True
                if teamNeedRemedy == Cards.REMEDY_GO:
                  teamNeedRemedy = None
              elif teamNeedRemedy:
                if ((cardType == Cards.SAFETY and teamNeedSafety == card) or
                    (cardType == Cards.REMEDY and needRemedy[teamNo] == card)):
                  teamNeedRemedy = None
            else:
              mileage = Cards.cardToMileage(card)
              if mileage == 200 and teamTwoHundredsPlayed >= 2:
                continue
              elif mileage > teamNeedMileage:
                continue
              elif mileage == 200:
                teamTwoHundredsPlayed += 1

              teamNeedMileage -= mileage

            if teamNeedMileage == 0 and teamMoving and not teamNeedRemedy:
              tripCompletedBy = playerNum
              break

          needMileage[teamNo] = teamNeedMileage
          needRemedy[teamNo] = teamNeedRemedy
          moving[teamNo] = teamMoving
          twoHundredsPlayed[teamNo] = teamTwoHundredsPlayed

        turnsElapsed += 1

      result = [turnsElapsed]
      for i in xrange(len(self.gameState.opponents) + 1):
        if i == self.gameState.us.number:
          team = self.gameState.us
        else:
          team = self.gameState.teamNumberToTeam(i)

        if needRemedy[i] or not moving[i]:
          mileage = 1000 - team.mileage
        else:
          mileage = needMileage[i]
        result.append(mileage)
      results.append(result)
    return results

  @cacheComputationForTurn
  def maxTripPctDone(self):
    # TODO: Assumes extension.
    ret = max(map(lambda team: team.mileage, self.teams())) / 1000.0
    self.debug("Max trip pct done: %r", ret)
    return ret

  @cacheComputationForTurn
  def expectedTurnsLeft(self):
    maxTripPctDone = self.maxTripPctDone()
    self.debug("Max trip percent done: %r", maxTripPctDone)
    if self.useMonteCarloSimulation():
      deckExhaustionTurns = self.deckExhaustionTurnsLeft()
      return deckExhaustionTurns

    gameEndTurns = [gameOutcome[0]
                    for gameOutcome
                    in self.monteCarloMileageSimulation()]
    ret = math.ceil(sum(gameEndTurns)/len(gameEndTurns))
    self.debug("Game is expected to end in %r turns.", ret)
    return ret

  @cacheComputationForTurn
  def deckExhaustionTurnsLeft(self):
    ret = math.ceil(self.gameState.cardsLeft / self.playerCount())
    self.debug("%d turns until deck exhaustion (%d players, %d cards left)",
               ret, self.playerCount(), self.gameState.cardsLeft)
    return ret

  @cacheComputationForTurn
  def useMonteCarloSimulation(self):
    # This is expensive, and it's more expensive and less useful early in a trip.
    return (self.maxTripPctDone() > 0.75 or
            self.deckExhaustionTurnsLeft() < 10)


  def handEnded(self, scoreSummary):
    scoresByTeam = {}
    teamNo = None
    for line in scoreSummary.split("\n"):
      match = re.match(r'^Team (\d+)$', line)
      if match:
        teamNo = int(match.group(1))
      else:
        match = re.match(r'^\s+Total: (\d+)$', line)
        if match:
          scoresByTeam[teamNo] = int(match.group(1))

    ourScore = scoresByTeam[self.usTeamNumber]
    avgScore = sum(scoresByTeam.values()) / len(scoresByTeam)
    fitness = ourScore - avgScore
    if ourScore == max(scoresByTeam.values()):
      fitness += 5000

    fitness_scores = self.__class__.constants.hand_fitness_scores
    fitness_scores.append(fitness)
    if len(fitness_scores) >= 500:
      avg_fitness = sum(fitness_scores)/len(fitness_scores)
      Constants.debug("Determined fitness of %r: %r", self.__class__.constants.toTuple(), avg_fitness)
      CONSTANT_POPULATIONS_FOR_PLAYERCOUNT[self._playerCount].append(
        (self.__class__.constants, avg_fitness))
      self.__class__.constants = None
    else:
      Constants.debug("Still determining fitness, played %d hands.", len(fitness_scores))
