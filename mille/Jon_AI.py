from mille.ai import AI
from mille.cards import Cards
from mille.move import Move

# Simple AI
class Jon_AI(AI):

  needRoll = 0
  milesLeft = 700

  def makeMove(self, state):

    if (state.us.needRemedy == Cards.REMEDY_GO):
      self.needRoll = self.needRoll + 1
    else:
      self.needRoll = 0

    # Miles we need to win
    self.milesLeft = state.target - state.us.mileage
    
    discards = []
    mileage = []
    attacks = []
    remedies = []
    safeties = []
    #print '--- AI cards ---'
    #print Cards.cardsToStrings(state.hand)
    #print '------'
    for play in state.validMoves:
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

    # If there's only one card left, play a safety to draw it
    if ((state.cardsLeft == 1) & (len(safeties)>0)):
        return safeties[0]

    # Could this be the last round?
    lastRound = False
    iCanWin = False
    if (((self.milesLeft == 25) & (Cards.MILEAGE_25 in state.hand)) |
        ((self.milesLeft == 50) & (Cards.MILEAGE_50 in state.hand)) |
        ((self.milesLeft == 75) & (Cards.MILEAGE_75 in state.hand)) |
        ((self.milesLeft == 100) & (Cards.MILEAGE_100 in state.hand)) |
        ((self.milesLeft == 200) & (Cards.MILEAGE_200 in state.hand))):
      lastRound = True
      iCanWin = True
    for team in state.opponents:
      milesOther = state.target - team.mileage
      if ((milesOther == 25) | (milesOther == 50) | (milesOther == 75) |
          (milesOther == 100) | (milesOther == 200)):
        lastRound = True

    # If anyone can win and I have a safety, play it.
    if (lastRound) & (len(safeties) > 0):
      return safeties[0]

    # Play the best red card if possible, unless I can win
    if ((not(iCanWin)) & (len(attacks) > 0)):
      best = self.GetBestAttack(state, attacks)
      return best

    # Play a remedy, EoL as lowest priority
    for remedy in remedies:
      if remedy.card != Cards.REMEDY_END_OF_LIMIT:
        return remedy
    # Consider EoL now, unless near the end of the game
    for remedy in remedies:
        # Play EOL unless near the end of the game
        if (self.milesLeft > 50):
          return remedy

    # If we can move, play the highest mileage; this may win
    if len(mileage) > 0:
      best = self.GetBestMove(state, mileage)
      return best

    # Consider playing a safety
    if len(safeties) > 0:
      safety = self.ConsiderPlaySafety(state, safeties)
      if (not safety is None):
        return safeties[0]
    
    # Discard something
    disc = self.GetDiscard(state, discards)
    if (not (disc is None)):
      return disc

    # Hand is all safeties and attacks.  Play safety
    if len(safeties) > 0:
      return safeties[0]
    # Discard random
    return discards[0]

  def playCoupFourre(self, attackCard, state):
    return True

  # Always go for extension, unless opponent has a big advantage
  def goForExtension(self, state):
    milesInHand = 0
    for card in state.hand:
      if (Cards.cardToType(card) == Cards.MILEAGE):
        milesInHand = milesInHand + Cards.cardToMileage(card)
    if ((state.cardsLeft < 5) & (milesInHand < 300)):
      # Not enough cards to bother
      return False
    theirSafeties = 0
    # If opponent is at 600, or they have all the safeties, don't extend
    for opponent in state.opponents:
      if opponent.mileage >= 600:
        return False
      theirSafeties = theirSafeties + len(opponent.safeties)
    if theirSafeties >= 3:
      return False;
    return True

  # Get the best attack card
  def GetBestAttack(self, state, attacks):
    # Best attack is one where safety is visible
    for attack in attacks:
      safety = Cards.attackToSafety(attack.card)
      safetyVisible = self.CountCard(state, safety)
      if (safetyVisible >= 1):
        return attack
    # Count remedies for 3 regular attacks, and figure out which is best
    gas = self.CountCard(state, Cards.REMEDY_GASOLINE)
    repairs = self.CountCard(state, Cards.REMEDY_REPAIRS)
    spares = self.CountCard(state, Cards.REMEDY_SPARE_TIRE)

    bestAttack = attacks[0] # Could be Stop or Limit
    for attack in attacks:
      if attack.card == Cards.ATTACK_OUT_OF_GAS:
        if ((gas >= repairs) & (gas >= spares)):
          bestAttack = attack
      elif attack.card == Cards.ATTACK_ACCIDENT:
        if ((repairs >= gas) & (repairs >= spares)):
          bestAttack = attack
      elif attack.card == Cards.ATTACK_FLAT_TIRE:
        if ((spares >= gas) & (spares >= repairs)):
          bestAttack = attack
      if ((bestAttack.card == Cards.ATTACK_STOP) | (bestAttack.card == Cards.ATTACK_SPEED_LIMIT)):
          # Anything's better than Stop/Limit
          bestAttack = attack
    return bestAttack

  # Get the best mileage card
  def GetBestMove(self,  state, mileage):
    # If the race is almost over, may not want to play highest card
    needToPlay = -1
    if self.milesLeft == 125:  # 100/25 or 75/50
      if ((Cards.MILEAGE_75 in state.hand) & (Cards.MILEAGE_50 in state.hand)):
        needToPlay = Cards.MILEAGE_75
      if ((Cards.MILEAGE_100 in state.hand) & (Cards.MILEAGE_25 in state.hand)):
        needToPlay = Cards.MILEAGE_100
    elif self.milesLeft == 100:  # 75/25 or 50/50, or 100
      if (state.hand.count(Cards.MILEAGE_50) >= 2):
        needToPlay= Cards.MILEAGE_50
      if (Cards.MILEAGE_100 in state.hand):
        needToPlay = Cards.MILEAGE_100
    highCard = mileage[0]
    for mileCard in mileage:
      if (mileCard.card == needToPlay):
        return mileCard
      if (Cards.cardToMileage(mileCard.card)) > (Cards.cardToMileage(highCard.card)):
        highCard = mileCard
    return highCard

  # Get the best to discard
  def GetDiscard(self, state, discards):

    milesLeft = state.target - state.us.mileage
    milesInHand = 0
    for discard in discards:
      # Excess mileage; discard the card that puts me over the top
      if (Cards.cardToType(discard.card) == Cards.MILEAGE):
        milesInHand = milesInHand + Cards.cardToMileage(discard.card)
        if (milesInHand > milesLeft): 
          return discard
      # Too many 200s
      if (discard.card == Cards.MILEAGE_200):
        total200 = state.us.twoHundredsPlayed + state.hand.count(Cards.MILEAGE_200)
        if (total200 > 2):
          return discard
      # Attack that opponent has a safety for, if only 1 opponent
      if (len(state.opponents) == 1) & (Cards.cardToType(discard.card) == Cards.ATTACK):
        safety = Cards.attackToSafety(discard.card)
        if safety in state.opponents[0].safeties:
          return discard
      # Remedy for a safety that I have
      if Cards.cardToType(discard.card) == Cards.REMEDY:
        safety = Cards.remedyToSafety(discard.card)
        if (safety in state.hand) | (safety in state.us.safeties):
          return discard
    # Now that we've gone through the best options, try second-tier discards
    for discard in discards:
      # 2 of the same remedy, or 3 if it's GO
      if Cards.cardToType(discard.card) == Cards.REMEDY:
        count = state.hand.count(discard.card)
        if (count > 1) & (discard.card != Cards.REMEDY_GO):
          return discard
        if count > 2:
          return discard
        # Weak mileage, unless near the end of the game
        if (milesLeft > 100):
          if discard.card == Cards.MILEAGE_25:
            return discard
          if discard.card == Cards.MILEAGE_50:
            return discard
          if discard.card == Cards.MILEAGE_75:
            return discard
    # Nothing good to discard; just toss something that's not attack or safety
    for d in discards:
      if ((Cards.cardToType(d.card) != Cards.SAFETY) &
          (Cards.cardToType(d.card) != Cards.ATTACK)):
        return d;

  # Maybe play a safety; doesn't necssarily return anything
  def ConsiderPlaySafety(self, state, safeties):
    # If I'm stuck and the safety resolves it, play it
    if (not state.us.moving):
      needRemedy = state.us.needRemedy
      needSafe = Cards.remedyToSafety(needRemedy)
      for safety in safeties:
        if (safety.card == needSafe):
          return safety
    # If all the hazards are visible, just play the safety
    for safety in safeties:
      if (safety.card == Cards.SAFETY_PUNCTURE_PROOF):
        flats = self.CountCard(state, Cards.ATTACK_FLAT_TIRE)
        if (flats >= 3):
          return safety
      elif (safety.card == Cards.SAFETY_EXTRA_TANK):
        outs = self.CountCard(state, Cards.ATTACK_OUT_OF_GAS)
        if (outs >= 3):
          return safety
      elif (safety.card == Cards.SAFETY_DRIVING_ACE):
        acc = self.CountCard(state, Cards.ATTACK_ACCIDENT)
        if (acc >= 3):
          return safety
    # Out of cards, just play the safety
    if (len(state.hand) == len(safeties)):
      return safety
    # Been stuck for too long, have to do something
    if (self.needRoll >= 10):
      return safeties[0]

# Utility methods

  # Count how many instances of a card have been played
  def CountCard(c, state, card):
#    print ' Looking for ' + Cards.cardToString(card)
    inHand = state.hand.count(card)
    inDiscard = state.discardPile.count(card)
    inMyBattle = state.us.battlePile.count(card)
    inOpponentsBattle = 0
    for team in state.opponents:
      inOpponentsBattle = inOpponentsBattle + team.battlePile.count(card)
    total = inHand + inDiscard + inMyBattle + inOpponentsBattle
#    print 'Total instances of ' + Cards.cardToString(card) + ' equals ' + str(total)
    return total
    
