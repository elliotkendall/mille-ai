# Information about a player
class Player:
  def __init__(self):
    self.hand = []
    self.number = -1
    self.teamNumber = -1
    self.ai = None

  def __str__(self):
    return str(self.ai) + ', player ' + str(self.number) + ' (team ' + str(self.teamNumber) + ')'
