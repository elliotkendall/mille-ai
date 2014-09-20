# Classes for several example AI players

from mille.ai import AI
from mille.cards import Cards
from mille.move import Move

# About the dumbest AI that still plays a credible game
class BasicAI(AI):
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

# An "AI" that gets input from the user
class ManualAI(AI):
  def makeMove(self, gameState):
    print 'Opponents:'
    for opponent in gameState.opponents:
      print opponent
    print 'Us:'
    print gameState.us
    print 'Cards left in deck: ' + str(gameState.cardsLeft)
    print 'Target: ' + str(gameState.target) + ' miles'
    print 'Your hand: ',
    print Cards.cardsToStrings(gameState.hand)
    print 'Valid moves:'
    for i in range(len(gameState.validMoves)):
      print str(i) + ':',
      print gameState.validMoves[i]
    moveint = -1
    while moveint not in range(len(gameState.validMoves)):
      move = raw_input('Enter move index: ')
      try:
        moveint = int(move)
      except ValueError:
        moveint = -1
    return gameState.validMoves[int(move)]

  def playerPlayed(self, player, move):
    print player,
    print move
  
  def playCoupFourre(self, attackCard, gameState):
    coupFourre = raw_input('Play coup fourre (y/n)? [y]: ')
    if coupFourre == 'n':
      return False
    return True

  def goForExtension(self, gameState):
    extension = raw_input('Go for extension (y/n)? [n]: ')
    if extension == 'y':
      return True
    return False

class JonsAwesomeAI(AI):
  def makeMove(self, gameState):
    # If you have a 25, discard it. Otherwise, discard another card.
    if Cards.MILEAGE_25 in gameState.hand:
      return Move(Move.DISCARD, Cards.MILEAGE_25)
    return Move(Move.DISCARD, gameState.hand[0])

  def playCoupFourre(self, attackCard, gameState):
    return False
