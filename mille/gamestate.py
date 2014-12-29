from mille.cards import Cards
from mille.move import Move

# A representation of the game state limited to the information that should
# be available to a particular player

class GameState:

  def __init__(self):
    # The information we track
    self.hand = []
    self.discardPile = []
    self.us = None
    self.opponents = []
    self.validMoves = []
    self.target = 0
    self.cardsLeft = -1
    self.debug = False

  def teamNumberToTeam(self, teamNumber):
    if self.us.number == teamNumber:
      return self.us
    for opponent in self.opponents:
      if opponent.number == teamNumber:
        return opponent
    raise KeyError(teamNumber)

  # Populate our validMoves attribute based on our other information.
  # This should probably be in the Game class instead...
  def findValidPlays(self):
    for card in self.hand:
      # You can always discard
      self.validMoves.append(Move(Move.DISCARD, card))

      type = Cards.cardToType(card)
      if (card == self.us.needRemedy
       or (card == Cards.REMEDY_END_OF_LIMIT and self.us.speedLimit)
       or (self.us.moving and type == Cards.MILEAGE
           and ((not self.us.speedLimit) or card in Cards.LOW_MILEAGE)
           and (self.us.twoHundredsPlayed < 2 or card != Cards.MILEAGE_200)
           and (self.us.mileage + Cards.cardToMileage(card) <= self.target))
       or type == Cards.SAFETY):
        self.validMoves.append(Move(Move.PLAY, card))
      elif type == Cards.ATTACK:
        for opponent in self.opponents:
          if card == Cards.ATTACK_SPEED_LIMIT:
            if ((not opponent.speedLimit)
             and Cards.SAFETY_RIGHT_OF_WAY not in opponent.safeties):
              self.validMoves.append(Move(Move.PLAY, card, opponent.number))
          elif (opponent.moving
           and Cards.attackToSafety(card) not in opponent.safeties):
            self.validMoves.append(Move(Move.PLAY, card, opponent.number))
