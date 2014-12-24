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
    discards = []
    mileage = []
    attacks = []
    remedies = []
    safeties = []
    for play in gameState.validMoves:
      if (play.type == Move.DISCARD):
        discards.append(play)
      else:
        cardType = Cards.cardToType(play.card)
        if cardType == Cards.MILEAGE:
          mileage.append(play)
        elif cardType == Cards.REMEDY:
          remedies.append(play)
        elif cardType == Cards.ATTACK:
          attacks.append(play)
        elif cardType == Cards.SAFETY:
          safeties.append(play)
        else:
          raise Exception("Unknown type for %r: %r" % (play.card, cardType))

    # If we can move, move as far as possible.
    mileage.sort(key=lambda move: Cards.cardToMileage(move.card), reverse=True)
    if len(mileage) > 0:
      return mileage[0]

    # Play a remedy if we can
    if len(remedies) > 0:
      return remedies[0]

    # Attack whoever's furthest ahead, unless they're already impaired.
    # TODO: Also factor in who's beaten us in past games.
    attackValues = dict((attacks[i],
                         self.cardValue(attacks[i].card,
                                        i,
                                        attacks,
                                        gameState,
                                        target=attacks[i].target))
                        for i in xrange(len(attacks)))
    attacks.sort(cmp=lambda a, b: self.compareAttacks(attackValues, gameState, a, b),
                 reverse=True)
    for attack in attacks:
      if attackValues[attack] == 0:
        # TODO: Generalize "card value" to be used to pick a move,
        # not just a static order of "move, remedy, attack, ...".
        continue

      target = gameState.teamNumberToTeam(attack.target)
      if attack.card == Cards.ATTACK_SPEED_LIMIT:
        # If they're already under a speed limit, don't bother with another.
        if target.speedLimit:
          continue
      else:
        # If they already need a remedy, don't bother with another -- unless they need
        # "go", in which case the attack is still worthwhile because now they need
        # the specific attack's remedy *in addition to* go.
        if target.needRemedy and target.needRemedy != Cards.REMEDY_GO:
          continue

      return attack

    # Play a safety rather than discard
    # TODO: Might be worth discarding certain non-safety cards rather
    # than playing them outright, so that we can save safeties for coup fourre.
    if len(safeties) > 0:
      return safeties[0]
    
    # Discard the least valuable card.
    discardCards = tuple(discard.card for discard in discards)
    cardValues = dict((discards[discardIdx],
                       self.cardValue(discards[discardIdx].card,
                                      discardIdx,
                                      discardCards,
                                      gameState))
                      for discardIdx in xrange(len(discards)))
    discards.sort(key=lambda discard: cardValues[discard])
    return discards[0]

  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    # TODO: Don't go for it if we're way in the lead.
    return True

  def cardValue(self, card, cardIdx, cards, gameState, target=None):
    # moveIdx and cards let us disambiguate between two equal cards in our hand.
    #
    # By default, evaluates the value w.r.t. all potential targets;
    # this mode is used when evaluating potential discards.  If target
    # (a team number) is specified, evaluates the value w.r.t. the
    # specific target; this mode is used when evaluating potential
    # attacks.
    #
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
    #   TODO: Also factor in likelihood of future safety/remedy draw.
    #   TODO: ...and have it be target-specific, based on opponent's previous
    #            discards.

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
      if safety in gameState.us.safeties:
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

      if target:
        targets = (gameState.teamNumberToTeam(target), )
      else:
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

  def compareAttacks(self, attackValues, gameState, a, b):
    # Sort first by likelihood of attack success, then by threat level of target.
    # TODO: More advanced threat level model than just mileage.

    rets = (cmp(attackValues[a], attackValues[b]),
            cmp(gameState.teamNumberToTeam(a.target).mileage,
                gameState.teamNumberToTeam(b.target).mileage))
    for ret in rets:
      if ret != 0:
        return ret
    return 0
