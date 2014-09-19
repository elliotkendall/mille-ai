from mille.cards import Cards

# Information about a team
class Team:
  def __init__(self, number = -1):
    self.number = number
    self.playerNumbers = []
    self.totalScore = 0
    self.reset()

  # This stuff lives in a separate method so that we can easily reset it
  # between hands
  def reset(self):
    self.mileage = 0
    self.speedPile = []
    self.battlePile = []
    self.mileagePile = []
    self.safeties = []
    self.coupFourres = 0
    self.handScore = 0
    self.moving = False
    self.speedLimit = False
    self.needRemedy = Cards.REMEDY_GO
    self.safeTrip = True
    self.twoHundredsPlayed = 0

  def __str__(self):
    ret = "Team " + str(self.number) + ': ' + str(self.mileage) + " miles\n"
    if self.needRemedy != None:
      ret += '  Needs ' + Cards.cardToString(self.needRemedy) + "\n"
    if self.moving:
      ret += "  Moving\n"
    if self.speedLimit:
      ret += "  Under a speed limit\n"
    for safety in self.safeties:
      ret += '  ' + Cards.cardToString(safety) + "\n"
    return ret
