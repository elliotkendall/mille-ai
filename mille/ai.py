# Interface that AIs should implement
class AI:
  # Called at the start of a game
  def gameStarted(self, gameState):
    pass

  # Make a move on your turn
  def makeMove(self, gameState):
    pass

  # Called when you draw a card
  def cardDrawn(self, card):
    pass

  # Called when another player plays
  def playerPlayed(self, player, move):
    pass

  # scoreSummary is a human-readable string describing the hand scores.
  def handEnded(self, scoreSummary):
    pass

  # handScoresByTeam is a list of hand scores, one per team.  Team i's
  # hand score is at handScoresByTeam[i].  Similarly,
  # totalScoresByTeam is a list of total scores (including points from
  # the just-ended hand.)
  def handEnded2(self, handScoresByTeam, totalScoresByTeam):
    pass

  # Play a coup fourre?
  def playCoupFourre(self, attackCard, gameState):
    pass

  # Go for the extension?
  def goForExtension(self, gameState):
    pass
