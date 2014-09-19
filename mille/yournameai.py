from mille.ai import AI
from mille.cards import Cards
from mille.move import Move

# A copy of the BasicAI class from sampleais.py
class YourNameAI(AI):
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
        type = Cards.cardToType(play.card)
        if type == Cards.MILEAGE:
          mileage.append(play)
        elif type == Cards.REMEDY:
          remedies.append(play)
        elif type == Cards.ATTACK:
          attacks.append(play)
        elif type == Cards.SAFETY:
          safeties.append(play)

    # If we can move, move
    if len(mileage) > 0:
      return mileage[0]

    # Play a red card if appropriate
    if len(attacks) > 0:
      return attacks[0]

    # Play a remedy if we can
    if len(remedies) > 0:
      return remedies[0]

    # Play a safety rather than discard
    if len(safeties) > 0:
      return safeties[0]
    
    # Discard something
    return discards[0]

  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    return True
