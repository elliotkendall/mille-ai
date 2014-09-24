# A class of constants and static translation methods

class Cards:
  # Constants
  MILEAGE_25 = 0
  MILEAGE_50 = 1
  MILEAGE_75 = 2
  MILEAGE_100 = 3
  MILEAGE_200 = 4

  REMEDY_SPARE_TIRE = 5
  REMEDY_GASOLINE = 6
  REMEDY_REPAIRS = 7
  REMEDY_GO = 8
  REMEDY_END_OF_LIMIT = 9

  ATTACK_FLAT_TIRE = 10
  ATTACK_OUT_OF_GAS = 11
  ATTACK_ACCIDENT = 12
  ATTACK_STOP = 13
  ATTACK_SPEED_LIMIT = 14
  
  SAFETY_PUNCTURE_PROOF = 15
  SAFETY_EXTRA_TANK = 16
  SAFETY_DRIVING_ACE = 17
  SAFETY_RIGHT_OF_WAY = 18

  MILEAGE = 0
  REMEDY = 1
  ATTACK = 2
  SAFETY = 3

  # Valid when under speed limit
  LOW_MILEAGE = [MILEAGE_25, MILEAGE_50 ]

  # Dictionary version
  constantToString = { 0: '25 Miles', 1: '50 Miles', 2: '75 Miles',
   3: '100 Miles', 4: '200 Miles', 5: 'Spare Tire', 6: 'Gasoline',
   7: 'Repairs', 8: 'Go', 9: 'End of Limit', 10: 'Flat Tire',
   11: 'Out of Gas', 12: 'Accident', 13: 'Stop', 14: 'Speed Limit',
   15: 'Puncture Proof', 16: 'Extra Tank', 17: 'Driving Ace',
   18: 'Right of Way'
  }

  # Turns a mileage card constant into its numerical miles value
  @classmethod
  def cardToMileage(c, card):
    if card == c.MILEAGE_25:
      return 25
    elif card == c.MILEAGE_50:
      return 50
    elif card == c.MILEAGE_75:
      return 75
    elif card == c.MILEAGE_100:
      return 100
    elif card == c.MILEAGE_200:
      return 200
    raise ValueError('Passed card is not known mileage')

  # Turns e.g. MILEAGE_25 into "25 Miles" or SAFETY_RIGHT_OF_WAY into "Right
  # of Way"
  @classmethod
  def cardToString(c, card):
    return c.constantToString[card]

  # Same as above for a list
  @classmethod
  def cardsToStrings(c, cards):
    ret = []
    for card in cards:
      ret.append(c.constantToString[card])
    return ret

  # What kind of card is this?
  @classmethod
  def cardToType(c, card):
    if card in range(0, 5):
      return c.MILEAGE
    elif card in range(5, 10):
      return c.REMEDY
    elif card in range(10, 15):
      return c.ATTACK
    elif card in range(15, 19):
      return c.SAFETY

  # What remedy resolves this attack?
  @classmethod
  def attackToRemedy(c, card):
    if card == c.ATTACK_FLAT_TIRE:
      return c.REMEDY_SPARE_TIRE
    elif card == c.ATTACK_OUT_OF_GAS:
      return c.REMEDY_GASOLINE
    elif card == c.ATTACK_ACCIDENT:
      return c.REMEDY_REPAIRS
    elif card == c.ATTACK_STOP:
      return c.REMEDY_GO
    raise ValueError('Unknown attack card')

  # What safety prevents this attack?
  @classmethod
  def attackToSafety(c, card):
    if card == c.ATTACK_FLAT_TIRE:
      return c.SAFETY_PUNCTURE_PROOF
    elif card == c.ATTACK_OUT_OF_GAS:
      return c.SAFETY_EXTRA_TANK
    elif card == c.ATTACK_ACCIDENT:
      return c.SAFETY_DRIVING_ACE
    elif card == c.ATTACK_STOP or card == c.ATTACK_SPEED_LIMIT:
      return c.SAFETY_RIGHT_OF_WAY

  # What safety provides this benefit?
  @classmethod
  def remedyToSafety(c, card):
    if card == c.REMEDY_SPARE_TIRE:
      return c.SAFETY_PUNCTURE_PROOF
    elif card == c.REMEDY_GASOLINE:
      return c.SAFETY_EXTRA_TANK
    elif card == c.REMEDY_REPAIRS:
      return c.SAFETY_DRIVING_ACE
    elif card == c.REMEDY_GO or card == c.REMEDY_END_OF_LIMIT:
      return c.SAFETY_RIGHT_OF_WAY

  # What attack does this remedy fix?
  @classmethod
  def remedyToAttack(c, card):
    if card == c.REMEDY_SPARE_TIRE:
      return c.ATTACK_FLAT_TIRE
    elif card == c.REMEDY_GASOLINE:
      return c.ATTACK_OUT_OF_GAS
    elif card == c.REMEDY_REPAIRS:
      return c.ATTACK_ACCIDENT
    elif card == c.REMEDY_GO:
      return c.ATTACK_STOP
    elif card == c.REMEDY_END_OF_LIMIT:
      return c.ATTACK_SPEED_LIMIT
