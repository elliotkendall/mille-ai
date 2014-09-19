from cards import Cards

# Represents a move. Moves have a type (play, discard), the card being
# played (see constants in the Cards class), and for attacks, the number of
# the target team
class Move:
  DISCARD = 0
  PLAY = 1
  def __init__(self, type, card, target = None, coupFourre = False):
    self.type = type
    self.card = card
    self.target = target
    self.coupFourre = coupFourre

  @classmethod
  def typeToString(c, type):
    if type == c.DISCARD:
      return 'discard'
    elif type == c.PLAY:
      return 'play'
    raise ValueError('Invalid move type')

  # Objects with the same data should be treated as equal
  def __eq__(self, other): 
    return self.__dict__ == other.__dict__

  def __str__(self):
    ret = self.typeToString(self.type) + 's ' + Cards.cardToString(self.card)
    if self.target != None:
      ret += ' on team ' + str(self.target)
    if self.coupFourre:
      ret += ' as a coup fourre!'
    return ret
