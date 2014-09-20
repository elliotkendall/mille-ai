from random import shuffle
from mille.cards import Cards

class Deck:
  # How many of each card is in the deck
  composition = {
   Cards.MILEAGE_25: 10,
   Cards.MILEAGE_50: 10,
   Cards.MILEAGE_75: 10,
   Cards.MILEAGE_100: 12,
   Cards.MILEAGE_200: 4,
   Cards.REMEDY_SPARE_TIRE: 6,
   Cards.REMEDY_GASOLINE: 6,
   Cards.REMEDY_REPAIRS: 6,
   Cards.REMEDY_GO: 14,
   Cards.REMEDY_END_OF_LIMIT: 6,
   Cards.ATTACK_FLAT_TIRE: 3,
   Cards.ATTACK_OUT_OF_GAS: 3,
   Cards.ATTACK_ACCIDENT: 3,
   Cards.ATTACK_STOP: 5,
   Cards.ATTACK_SPEED_LIMIT: 4,
   Cards.SAFETY_PUNCTURE_PROOF: 1,
   Cards.SAFETY_EXTRA_TANK: 1,
   Cards.SAFETY_DRIVING_ACE: 1,
   Cards.SAFETY_RIGHT_OF_WAY: 1
  }

  def __init__(self):
    self.deck = []

    for card, count in self.composition.items():
      for i in range(count):
        self.deck.append(card)
    shuffle(self.deck)

  # Draws the next "count" cards from the deck and returns them
  def draw(self, count = 1):
    if count == 1:
      return self.deck.pop()
    ret = []
    for i in range(count):
      ret.append(self.deck.pop())
    return ret

  def cardsLeft(self):
    return len(self.deck)
