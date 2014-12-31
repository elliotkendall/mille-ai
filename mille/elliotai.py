from mille.ai import AI
from mille.cards import Cards
from mille.move import Move
from random import shuffle
from copy import copy, deepcopy

# Todo
# * Value playing a safety higher if it fixes our current problem
# * Value discarding a remedy higher if we hold the safety (or it's been played)
# * Handle stop/go differently from others to avoid valuing discarding go          print 'Opponent is threatening to win - playing safeties'
# * Disvalue cards that are too high for the target
# * Value playing an attack when you hold (or have played) the safety
# * Disvalue attack cards in two-team when opponents have the safety

class ElliotAI(AI):
  def __init__(self):
    self.reset()

  def handEnded(self, scoreSummary):
    self.reset()

  def reset(self):
    self.attackCounts = {
      Cards.ATTACK_FLAT_TIRE: 0,
      Cards.ATTACK_OUT_OF_GAS: 0,
      Cards.ATTACK_ACCIDENT: 0,
      Cards.ATTACK_STOP: 0,
      Cards.ATTACK_SPEED_LIMIT: 0
    }
    self.priorities = {
      Move(Move.PLAY, Cards.MILEAGE_25): 1,
      Move(Move.PLAY, Cards.MILEAGE_50): 2,
      Move(Move.PLAY, Cards.MILEAGE_75): 3,
      Move(Move.PLAY, Cards.MILEAGE_100): 4,
      Move(Move.PLAY, Cards.MILEAGE_200): 5,
      Move(Move.PLAY, Cards.REMEDY_SPARE_TIRE): 6,
      Move(Move.PLAY, Cards.REMEDY_GASOLINE): 6,
      Move(Move.PLAY, Cards.REMEDY_REPAIRS): 6,
      Move(Move.PLAY, Cards.REMEDY_GO): 6,
      Move(Move.PLAY, Cards.REMEDY_END_OF_LIMIT): 5,
      Move(Move.PLAY, Cards.ATTACK_FLAT_TIRE, 0): 8,
      Move(Move.PLAY, Cards.ATTACK_FLAT_TIRE, 1): 8,
      Move(Move.PLAY, Cards.ATTACK_FLAT_TIRE, 2): 8,
      Move(Move.PLAY, Cards.ATTACK_OUT_OF_GAS, 0): 8,
      Move(Move.PLAY, Cards.ATTACK_OUT_OF_GAS, 1): 8,
      Move(Move.PLAY, Cards.ATTACK_OUT_OF_GAS, 2): 8,
      Move(Move.PLAY, Cards.ATTACK_ACCIDENT, 0): 8,
      Move(Move.PLAY, Cards.ATTACK_ACCIDENT, 1): 8,
      Move(Move.PLAY, Cards.ATTACK_ACCIDENT, 2): 8,
      Move(Move.PLAY, Cards.ATTACK_STOP, 0): 7,
      Move(Move.PLAY, Cards.ATTACK_STOP, 1): 7,
      Move(Move.PLAY, Cards.ATTACK_STOP, 2): 7,
      Move(Move.PLAY, Cards.ATTACK_SPEED_LIMIT, 0): 6,
      Move(Move.PLAY, Cards.ATTACK_SPEED_LIMIT, 1): 6,
      Move(Move.PLAY, Cards.ATTACK_SPEED_LIMIT, 2): 6,
      Move(Move.PLAY, Cards.SAFETY_PUNCTURE_PROOF): -7,
      Move(Move.PLAY, Cards.SAFETY_EXTRA_TANK): -7,
      Move(Move.PLAY, Cards.SAFETY_DRIVING_ACE): -7,
      Move(Move.PLAY, Cards.SAFETY_RIGHT_OF_WAY): -7,

      Move(Move.DISCARD, Cards.MILEAGE_25): -1,
      Move(Move.DISCARD, Cards.MILEAGE_50): -2,
      Move(Move.DISCARD, Cards.MILEAGE_75): -3,
      Move(Move.DISCARD, Cards.MILEAGE_100): -4,
      Move(Move.DISCARD, Cards.MILEAGE_200): -5,
      Move(Move.DISCARD, Cards.REMEDY_SPARE_TIRE): -5,
      Move(Move.DISCARD, Cards.REMEDY_GASOLINE): -5,
      Move(Move.DISCARD, Cards.REMEDY_REPAIRS): -5,
      Move(Move.DISCARD, Cards.REMEDY_GO): -10,
      Move(Move.DISCARD, Cards.REMEDY_END_OF_LIMIT): -3,
      Move(Move.DISCARD, Cards.ATTACK_FLAT_TIRE): -6,
      Move(Move.DISCARD, Cards.ATTACK_OUT_OF_GAS): -6,
      Move(Move.DISCARD, Cards.ATTACK_ACCIDENT): -6,
      Move(Move.DISCARD, Cards.ATTACK_STOP): -6,
      Move(Move.DISCARD, Cards.ATTACK_SPEED_LIMIT): -4,
    }
  
  def makeMove(self, gameState):
    # If an opponent is threatening to win, play safeties
    for opponent in gameState.opponents:
      if (opponent.mileage > gameState.target - 100
        or (opponent.mileage == gameState.target - 200
            and opponent.twoHundredsPlayed < 2)):
        self.priorities[Move(Move.PLAY, Cards.SAFETY_PUNCTURE_PROOF)] = 100
        self.priorities[Move(Move.PLAY, Cards.SAFETY_DRIVING_ACE)] = 100
        self.priorities[Move(Move.PLAY, Cards.SAFETY_RIGHT_OF_WAY)] = 100
        self.priorities[Move(Move.PLAY, Cards.SAFETY_EXTRA_TANK)] = 100
        break

    # If we can't play any more 200s, they're automatic discards
    if gameState.us.twoHundredsPlayed == 2:
      self.priorities[Move(Move.DISCARD, Cards.MILEAGE_200)] = 0

    # Adjust priorities based on our hand contents
    priorities = deepcopy(self.priorities)
    attackCounts = copy(self.attackCounts)
    remedyCounts = {}
    for card in gameState.hand:
      type = Cards.cardToType(card)
      if type == Cards.ATTACK:
        ElliotAI.adjustScoresForAttack(card, attackCounts, priorities)
      elif type == Cards.REMEDY:
        try:
          remedyCounts[card] += 1
        except KeyError:
          remedyCounts[card] = 1
    for remedy, count in remedyCounts.items():
      if remedy == Cards.REMEDY_GO:
        if count > 3:
          self.priorities[Move(Move.DISCARD, remedy)] = 0
        elif count > 2:
          self.priorities[Move(Move.DISCARD, remedy)] = -2
      else:
        if count > 2:
          self.priorities[Move(Move.DISCARD, remedy)] = 0
        elif count == 2:
          self.priorities[Move(Move.DISCARD, remedy)] = -2

    movePriorities = {}
    
    # Shuffle possible plays so that we pick a random move when two
    # are equally good
    shuffle(gameState.validMoves)
    for play in gameState.validMoves:
      try:
        priority = self.priorities[play]
        movePriorities[priority] = play
      except:
        pass

    sortedMoves = sorted(movePriorities.items(), None, None, True)
    if gameState.debug:
      for i in sortedMoves:
        print str(i[0]) + ': ' + str(i[1])
    myMove = sortedMoves[0][1]

    # If this move would make us win, see if we can play a safety first
    # instead
    if (myMove.type == Move.PLAY
        and Cards.cardToType(myMove.card) == Cards.MILEAGE
        and Cards.cardToMileage(myMove.card) + gameState.us.mileage == gameState.target):
      for move in gameState.validMoves:
        if (move.type == Move.PLAY
            and Cards.cardToType(move.card) == Cards.SAFETY):
          return move

    return myMove

  def playerPlayed(self, player, move):
    type = Cards.cardToType(move.card)
    if move.type == Move.PLAY and type == Cards.ATTACK:

      ElliotAI.adjustScoresForAttack(move.card, self.attackCounts, self.priorities)
    elif move.type == Move.DISCARD and type == Cards.REMEDY:
      # When a team discards a remedy, they're a less attractive target for
      # that attack
      self.priorities[Move(Move.PLAY, Cards.remedyToAttack(move.card), player.teamNumber)] += -.5

  @staticmethod
  def adjustScoresForAttack(card, attackCounts, priorities):
    # Discarding the associated remedy is a better move, and an
    # auto-discard if all three have been played now
    # Also that safety is less useful as a coup fourre
    attackCounts[card] += 1
    if attackCounts[card] == 3:
      priorities[Move(Move.PLAY, Cards.attackToSafety(card))] = 100
      priorities[Move(Move.DISCARD, Cards.attackToRemedy(card))] = 0
    else:
      priorities[Move(Move.PLAY, Cards.attackToSafety(card))] += 1
      priorities[Move(Move.DISCARD, Cards.attackToRemedy(card))] += .5
  
  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    score = 0
    # Safeties played
#    print str(len(gameState.us.safeties)) + ' safeties played'
    score += len(gameState.us.safeties) * 200

    # Mileage in hand
    mileage = 0
    for card in gameState.hand:
      try:
        mileage += Cards.cardToMileage(card)
      except ValueError:
        pass
    if mileage > 300:
      mileage = 300
#    print str(mileage) + ' miles in hand'
    score += mileage

    # Each card is on average worth 33 miles
    expectedMiles = 33 * (gameState.cardsLeft / len(gameState.opponents) + 1)
    if expectedMiles > 300 - mileage:
      expectedMiles = 300 - mileage
    score += expectedMiles
#    print str(expectedMiles) + ' expected miles in ' + str(gameState.cardsLeft) + ' cards'

    # Played attacks
    for attack in Cards.ATTACKS:
      if not Cards.attackToSafety(attack) in gameState.us.safeties:
        score += 60 * self.attackCounts[attack]
#        print str(self.attackCounts[attack]) + ' ' + Cards.cardToString(attack) + ' cards played'

    # Opponents
    for opponent in gameState.opponents:
      score -= opponent.mileage
#      print 'Team ' + str(opponent.number) + ' has ' + str(opponent.mileage) + ' miles'
      score -= len(opponent.safeties) * 100
#      print 'Team ' + str(opponent.number) + ' has ' + str(len(opponent.safeties)) + ' safeties'
      if opponent.moving:
#        print 'Team ' + str(opponent.number) + ' is moving'
        score -= 200

#    print 'Score: ' + str(score)
    if score > 500:
      return True
    else:
      return False
