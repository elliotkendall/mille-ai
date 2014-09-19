# Interface that AIs should implement
class AI:
  # Make a move on your turn
  def makeMove(self, gameState):
    pass

  # Called when another player plays
  def playerPlayed(self, player, move):
    pass

  # Play a coup fourre?
  def playCoupFourre(self, attackCard, gameState):
    pass

  # Go for the extension?
  def goForExtension(self, gameState):
    pass