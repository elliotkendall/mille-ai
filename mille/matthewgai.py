"""
matthewg@zevils.com 's entry in the Mille Bornes AI competition.
"""
from __future__ import division  # / == float, // == int

from mille.ai import AI
from mille.cards import Cards
from mille.deck import Deck
from mille.move import Move

class MatthewgAI(AI):

  def makeMove(self, gameState):
    # Doesn't attempt to account for a card in another player's hand.
    # If it's not in our hand, a tableau, or the discard pile, it
    # is possibly remaining.
    cardsPossiblyRemaining = self.countCards(gameState)

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
    # TODO: Also factor in likelihood that they might have coup fourre available.
    attacks.sort(key=lambda move: gameState.opponents[move.target].mileage, reverse=True)
    if len(attacks) > 0:
      for attack in attacks:
        target = gameState.opponents[attack.target]
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
    discardCards = (discard.card for discard in discards)
    cardValues = dict((discards[discardIdx],
                       self.cardValue(discards[discardIdx].card,
                                      discardIdx,
                                      discardCards,
                                      gameState,
                                      cardsPossiblyRemaining))
                      for discardIdx in xrange(len(discards)))
    discards.sort(key=lambda discard: cardValues[discard])
    return discards[0]

  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    # TODO: Don't go for it if we're way in the lead.
    return True

  def countCards(self, gameState):
    cardsPossiblyRemaining = dict(Deck.composition)
    def countCardsForList(l):
      for card in l:
        cardsPossiblyRemaining[card] -= 1
    countCardsForList(gameState.discardPile)
    countCardsForList(gameState.hand)
    def countCardsForTeam(team):
      countCardsForList(team.mileagePile)
      countCardsForList(team.speedPile)
      countCardsForList(team.battlePile)
      countCardsForList(team.safeties)
    countCardsForTeam(gameState.us)
    for opponent in gameState.opponents:
      if opponent:
        countCardsForTeam(opponent)
    return cardsPossiblyRemaining

  def cardValue(self, card, cardIdx, cards, gameState, cardsPossiblyRemaining):
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
    #   TODO: Also factor in likelihood of future attack draw.
    # * Unplayed safeties: 9pt
    # * Attack: 6pt * percentage of opponents vulnerable to it
    #   TODO: Also factor in likelihood of future safety/remedy draw.

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
      if Cards.remedyToSafety(card) in gameState.us.safeties:
        return 0
      else:
        # Do we already have an equivalent safety in our hand?
        duplicateRemedies = 0
        for otherHandCard in cards:
          otherCardType = Cards.cardToType(otherHandCard)
          if otherCardType == Cards.REMEDY and otherHandCard == card:
            duplicateRemedies += 1
          elif otherCardType == Cards.SAFETY and Cards.remedyToSafety(card) == otherHandCard:
            return 0
        return max(1, 4 - duplicateRemedies)
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
      totalOpponents = len(gameState.opponents) - 1
      vulnerableOpponents = totalOpponents
      neededSafety = Cards.attackToSafety(card)
      for opponent in gameState.opponents:
        if opponent is None:
          continue
        elif neededSafety in opponent.safeties:
          vulnerableOpponents -= 1
      return 6 * (vulnerableOpponents / totalOpponents)
    else:
      raise Exception("Unknown card type for %r: %r" % (card, cardType))
