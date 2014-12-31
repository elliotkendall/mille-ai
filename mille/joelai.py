from mille.ai import AI
from mille.cards import Cards
from mille.move import Move
from mille.deck import Deck
from copy import copy


class JoelAI(AI):
  def __init__(self):
    
    #gameHistory is a full play by play index of cards played this game.
    self.gameHistory = []
    
    #teamXPlayed is a full play by play index of cards played only by team X.
    self.team1Played = []
    self.team2Played = []
    self.team3Played = []
    
    #cardsLeft tracks the cards left in the deck.
    self.cardsLeft = copy(Deck.composition)
    
  def getDangerCards(self, gameState):
    #Danger cards are cards that can actually stop us
    dangerCards = 0
    if len(gameState.us.safeties) == 4:
      #If we have all of the safeties, there are no danger cards.
      return 0
    else:
      for card in self.cardsLeft:
        if Cards.cardToType(card) == Cards.ATTACK and Cards.attackToSafety(card) not in gameState.us.safeties and card != Cards.ATTACK_SPEED_LIMIT:
        #For each card that's an attack and we don't have the safety
          if Cards.attackToRemedy(card) not in gameState.hand:
            #If the remedy isn't in our hand, all cards are danger cards
            dangerCards+=self.cardsLeft[card]
          elif gameState.hand.count(Cards.attackToRemedy(card)) < self.cardsLeft[card]:
            #If The number of remedies we have is less than the number of attacks out there
            dangerCards+=(self.cardsLeft[card] - gameState.hand.count(Cards.attackToRemedy(card)))
            #The number of attacks minus our remedies are danger cards

            
  def handEnded(self, scoreSummary):
    #This is called when a hand is over
    self.gameHistory = []
    self.team1Played = []
    self.team2Played = []
    self.team3Played = []
    self.cardsLeft = copy(Deck.composition)
    
  def playerPlayed(self, player, move):
    self.gameHistory.append([player.number, player.teamNumber, move.card])
    self.cardsLeft[move.card]-=1
    if player.teamNumber == 0:
      self.team1Played.append([player.number, player.teamNumber, move.card])
    elif player.teamNumber == 1:
      self.team2Played.append([player.number, player.teamNumber, move.card])
    elif player.teamNumber == 2:
      self.team3Played.append([player.number, player.teamNumber, move.card])
    else:
      print "playerPlayed Error: Invalid Team Number: "
      print player.teamNumber
      
  def priorityTarget(self, gameState):
    #There's no priority target if there are only two teams
    if len(self.team3Played) == 0:
      return -1
    else:
      #If first opponent team has a higher total score, they are our priority target.
      if gameState.opponents[0].totalScore > gameState.opponents[1]:
        return gameState.opponents[0].number
      else:
        return gameState.opponents[1].number
        
  def sortAttacks(self, attackList, targetTeam):
    sortedList = []
    sortedList2 = []
    sortedList3 = []
    sortedList4 = []
    if targetTeam == -1:
      for i in range(len(attackList)):
        if attackList[i].card == Cards.ATTACK_FLAT_TIRE:
          sortedList.insert(0,attackList[i])
        elif attackList[i].card == Cards.ATTACK_OUT_OF_GAS:
          sortedList.insert(1,attackList[i])
        elif attackList[i].card == Cards.ATTACK_ACCIDENT:
          sortedList.insert(2,attackList[i])
        elif attackList[i].card == Cards.ATTACK_STOP:
          sortedList.insert(3,attackList[i])
        else:
          sortedList.insert(4,attackList[i])
      return sortedList
    else:
      for i in range(len(attackList)):
        if attackList[i].target == targetTeam and attackList[i].card <= 13:
          if attackList[i].card >= 10 and attackList[i].card <= 12:
            sortedList.insert(0,attackList[i])
          elif attackList[i].card == Cards.ATTACK_STOP:
            sortedList.append(attackList[i])
        elif attackList[i].target != targetTeam and attackList[i].card <= 13:
          if attackList[i].card >= 10 and attackList[i].card <= 12:
            sortedList2.insert(0,attackList[i])
          elif attackList[i].card == Cards.ATTACK_STOP:
            sortedList2.append(attackList[i])
        elif attackList[i].target == targetTeam and attackList[i].card == 14:
          sortedList3.append(attackList[i])
        elif attackList[i].target != targetTeam and attackList[i].card == 14:
          sortedList4.append(attackList[i])
      sortedList.extend(sortedList2)
      sortedList.extend(sortedList3)
      sortedList.extend(sortedList4)
    return sortedList
      
         
  def makeMove(self, gameState):
    discards = []
    mileage = []
    attacks = []
    remedies = []
    safeties = []
    worthlessCards = [] #These are cards that cannot ever help us and are first to be discarded.
    milesToGo = gameState.target - gameState.us.mileage
    numMiles = []
    targetTeam = self.priorityTarget(gameState)
    
    for play in gameState.validMoves:
      type = Cards.cardToType(play.card)
      if (play.type == Move.DISCARD):
	    #Never discard a safety.
        if type != Cards.SAFETY:
          if type == Cards.MILEAGE:
            #Mileage cards are worthless if they put us over 1000 miles.
            if Cards.cardToMileage(play.card) + gameState.us.mileage > 1000:
              worthlessCards.append(play)
              
            #200 miles is worthless if we've played 2 of them, or if # played + # in hand > 2, the surplus is worthless
            else:
              discards.append(play)
          elif type == Cards.ATTACK:
            #Attack cards are worthless if we only have one opponent and they have played the safety
            if targetTeam == -1:
              for opponent in gameState.opponents:
                if Cards.attackToSafety(play.card) in opponent.safeties:
                  worthlessCards.append(play)
                else:
                  discards.append(play)
            else:
              discards.append(play)
            
          elif type == Cards.REMEDY:
            #Remedies are worthless if the we have played the safety
            if Cards.remedyToSafety(play.card) in gameState.us.safeties:
              worthlessCards.append(play)
            #Remedies are worthless if we have the safety for it in our hand
            elif Cards.remedyToSafety(play.card) in gameState.hand:
              worthlessCards.append(play)
            #Remedies are worthless if all of the appropriate attack cards have been played and we do not need it right now.
            elif self.cardsLeft[Cards.remedyToAttack(play.card)] == 0 and gameState.us.needRemedy != Cards.remedyToAttack(play.card):
              worthlessCards.append(play)
            else:
              discards.append(play)
      else:
        if type == Cards.MILEAGE:
          #Sort as we insert, biggest mileage at the front of the list
          if len(mileage) == 0:
            numMiles.append(Cards.cardToMileage(play.card))
            mileage.append(play)
          elif len(mileage) == 1:
            if Cards.cardToMileage(play.card) > numMiles[0]:
              numMiles.insert(0, Cards.cardToMileage(play.card))
              mileage.insert(0, play)
            else:
              numMiles.append(Cards.cardToMileage(play.card))
              mileage.append(play)
          elif len(mileage) == 2:
            if Cards.cardToMileage(play.card) > numMiles[0]:
              numMiles.insert(0, Cards.cardToMileage(play.card))
              mileage.insert(0, play)
            elif Cards.cardToMileage(play.card) > numMiles[1]:
              numMiles.insert(1, Cards.cardToMileage(play.card))
              mileage.insert(1, play)
            else:
              numMiles.append(Cards.cardToMileage(play.card))
              mileage.append(play)
          else:
            #If it's biggest, insert it first
            if Cards.cardToMileage(play.card) > numMiles[0]:
              numMiles.insert(0, Cards.cardToMileage(play.card))
              mileage.insert(0, play)
            #If it's smallest, insert it last
            elif Cards.cardToMileage(play.card) < numMiles[len(numMiles) - 1]:
              numMiles.insert((1 - len(numMiles)), Cards.cardToMileage(play.card))
              mileage.insert((1 - len(mileage)), play)
            #Otherwise Insert it at index 1
            else:
              numMiles.insert(1, Cards.cardToMileage(play.card))
              mileage.insert(1, play)
            
        elif type == Cards.ATTACK:
          if targetTeam == -1:
            #No priority target
            attacks.append(play)
          #Sort as we insert, priority targets in front
          elif play.target == targetTeam:
            attacks.insert(0, play)
          else:
            attacks.append(play)
        elif type == Cards.REMEDY:
          remedies.append(play)
        elif type == Cards.SAFETY:
          safeties.append(play)
    
    
    
	#If there are less than 10 cards left, play any safeties in our hand
	# NOTE: Investigate how much this changes AI results
    if gameState.cardsLeft <= 10:
      if len(safeties) > 0:
        return safeties[0]
			
	#If we can win the game, play a safety if we can, then check to see if we are safe to go for delayed action, otherwise win the game.
    if milesToGo in numMiles:
      if len(safeties) > 0:
        return safeties[0]
      elif gameState.cardsLeft == 0:
        #Win the game if we already have a delayed action.
        return mileage[numMiles.index(milesToGo)]
      elif self.getDangerCards(gameState) == 0:
        #If we are safe, attack if we can, pitch a worthless card if we can't, win the game otherwise.
        if len(attacks) > 0:
          return attacks[0]
        elif len(worthlessCards) > 0:
          return worthlessCards[0]
        else:
          return mileage[numMiles.index(milesToGo)]
      else:
        #For the time being, consider even one potential attack too deadly, and end the game.
        #TINKER HERE LATER
        return mileage[numMiles.index(milesToGo)]
        
    if len(attacks) > 0:
      attacks = self.sortAttacks(attacks, targetTeam)        
      #Attack if we can in a two player game always.
      if targetTeam == -1 :
        return attacks[0]
      #If we can't move in a 3 player game, attack first.
      elif len(mileage) == 0:
        return attacks[0]
      #If we have a valid move for 100 miles or more and we've got a ways to go, move, otherwise attack.
      elif Cards.cardToMileage(mileage[0].card) >= 100 and milesToGo >= 400:
        return mileage[0]
      else:
        return attacks[0]
    
	#Fix what needs fixing in a two player game, attack in a 3 player game (since we aren't moving)
    if len(remedies) > 0:
      return remedies[0]
   
  #If we need a remedy and we have the safety for it after move 10, just play it.
    if gameState.us.needRemedy != None and len(safeties) > 0:
      for s in safeties:
        if Cards.remedyToSafety(gameState.us.needRemedy) == s.card and len(self.gameHistory) >= 10:
          return s
	  
  # If we can move
    if len(mileage) > 0:
      #Move as fast as we can if we haven't gone too far
      if milesToGo > 400:
        return mileage[0]
      #If we've already played a 200 and our biggest mileage card leaves us at or over 100 miles, play it
      if (milesToGo - Cards.cardToMileage(mileage[0].card) >= 100):
        if (gameState.us.twoHundredsPlayed > 0):
          return mileage[0]
      #If we have more than 200 miles to go, haven't played a 200, have a 100, and we're not under a speed limit, play the 100
      if milesToGo > 200 and gameState.us.twoHundredsPlayed == 0 and Cards.MILEAGE_100 in gameState.hand and not(gameState.us.speedLimit):
        for i in mileage:
          if numMiles[mileage.index(i)] == 100:
            return i
      #If we're over 100 miles away and we can get to 100 miles away, do it
      if milesToGo > 100:
        for i in numMiles:
          if milesToGo - i == 100:
            return mileage[numMiles.index(i)]
      #If we're under a speed limit, play the biggest mileage we have
      if gameState.us.speedLimit:
        return mileage[0]
      #If we're at 200 miles or less, play our smallest mileage (if we could win the game, we already would have done so)
      if milesToGo <= 200:
        mileage.reverse()
        return mileage[0]
      #Return our biggest mileage
      return mileage[0]
    
  # Discard something worthless if we have it
    if len(worthlessCards) > 0:
      return worthlessCards[0]
    
    #If we are at the end of the game, discard high mileage, then remedies, then attacks, then low mileage.
    if gameState.cardsLeft == 0:
      for d in discards:
        if d.card <= 4:
          if d.card >= 2:
            return d
      for d in discards:
        if d.card <= 9:
          if d.card >= 2:
            return d
      for d in discards:
        if d.card <= 14:
          if d.card >= 2:
            return d
      for d in discards:
        if d.card <= 2:
          return d
    
    for d in discards:
      #If we have more of a remedy than there are attacks in the game, discard it.
      if Cards.cardToType(d.card) == Cards.REMEDY and discards.count(d) > self.cardsLeft[Cards.remedyToAttack(d.card)]:
        return d
      #If we have 3 of any given card, discard it.
      if discards.count(d) >= 3:
        return d
      #If we're under a speed limit, discard 75 if we have it, 100 if we already popped our safeTrip cherry, 200 if we haven't and are halfway through the race, the rest of the mileage.
      if gameState.us.speedLimit:
        if d.card == Cards.MILEAGE_75:
          return d
        if gameState.us.safeTrip and ((gameState.target == 1000 and gameState.us.handScore >= 600) or (gameState.target == 700 and gameState.us.handScore > 400)) and d.card == Cards.MILEAGE_200:
          return d
        if d.card == Cards.MILEAGE_100:
          return d
        if d.card == Cards.MILEAGE_200:
          return d
      else:
        if d.card == Cards.MILEAGE_25:
          return d
          
    #Pitch doubles next - low mileage first, then high mileage, then remedies
    for d in discards:
       if discards.count(d) > 1:
        if d.card <= 1:
          return d
    for d in discards:
      if discards.count(d) > 1:
        if d.card <= 4:
          return d
    for d in discards:
      if discards.count(d) > 1:
        if d.card <= 9:
          return d    
          
    #Pitch crappy single cards.
    if Cards.MILEAGE_25 in gameState.hand:
      return Move(Move.DISCARD, Cards.MILEAGE_25)
    if Cards.MILEAGE_75 in gameState.hand:
      return Move(Move.DISCARD, Cards.MILEAGE_75)
    if Cards.MILEAGE_50 in gameState.hand:
      return Move(Move.DISCARD, Cards.MILEAGE_50)
    if Cards.REMEDY_END_OF_LIMIT in gameState.hand:
      return Move(Move.DISCARD, Cards.REMEDY_END_OF_LIMIT)
    
    #Pitch any mileage that puts us over 700 if the target is 700
    for d in discards:
      if Cards.cardToType(d.card) == Cards.MILEAGE:
        if gameState.target == 700 and Cards.cardToMileage(d.card) + gameState.us.mileage > 700:
          return d
    
    #If we have an attack and the remedy for the attack, pitch the remedy
    for d in discards:
      if Cards.cardToType(d.card) == Cards.ATTACK:
        if Cards.attackToRemedy(d.card) in gameState.hand:
          return Move(Move.DISCARD, Cards.attackToRemedy(d.card))
          
    
    
    #Pitch duplicate attack cards now, but only if we don't have the safety for it already played.
    for d in discards:
      if discards.count(d) > 1:
        if d.card <= 14 and Cards.attackToSafety(d.card) not in gameState.us.safeties:
          return d
    
    #If we've gotten here we have a pretty good hand - so play a safety if we have one 
    if len(safeties) > 0:
      return safeties[0]
      
    #Pitch attacks we don't have the safety for
    for d in discards:
      if Cards.cardToType(d.card) == Cards.ATTACK and Cards.attackToSafety(d.card) not in gameState.us.safeties:
          return d

    #Pitch any duplicates at this point
    for d in discards:
      if discards.count(d) > 1:
        return d

    #Pitch Speed Limit next
    for d in discards:
      if d.card == 14:
        return d

    #Pitch Stop next
    for d in discards:
      if d.card == 13:
        return d

    #In nearly a million runs total this hasn't ever triggered.  But it seems best to leave it here.
    return discards[0]


  def playCoupFourre(self, attackCard, gameState):
  #This is complete.
    return True

  def goForExtension(self, gameState):
    milesInHand = 0
    opponentScore = 0
    haveATwoHundred = False
    dangerscore = 0
    remainingCards = 0
    expectedMiles = 0
    totalPlayers = len(gameState.us.playerNumbers)
    if totalPlayers == 3 or totalPlayers == 6:
      numTeams = 3
    else:
      numTeams = 2
      
    for i in self.cardsLeft:
      remainingCards += self.cardsLeft[i]
    
    for i in gameState.opponents:
      totalPlayers += len(i.playerNumbers)
      opponentScore = i.totalScore + i.mileage + 100 * len(i.safeties) + 300 * i.coupFourres
      if opponentScore > 5000:
        dangerscore = opponentScore
        
    scoreIfWeStop = gameState.us.totalScore + 700 + 100 * len(gameState.us.safeties) + 300 * gameState.us.coupFourres + 400
    if remainingCards == 0:
      scoreIfWeStop += 300
    if gameState.us.safeTrip == True:
      scoreIfWeStop += 300
    #I am being lazy and not including shutout - if we have a shutout it's kinda hard to mess up.
    
    #Don't go for an extension if the win puts us over 5000 points and no opponent would have more
    if scoreIfWeStop >= 5000 and scoreIfWeStop > dangerscore:
      return False
    
    #Can't lose the game on purpose!
    if dangerscore > scoreIfWeStop:
      return True
      
    #If we have a safe trip let's not mess with it and just stop now.  This makes later logic much easier for 200 cards.
    if gameState.us.safeTrip == True:
      return False
    
    for h in gameState.hand:
      if Cards.cardToType(h) == Cards.MILEAGE:
        if h == Cards.MILEAGE_200 and gameState.us.twoHundredsPlayed == 1:
          haveATwoHundred = True
          milesInHand += Cards.cardToMileage(h)
        else:
          milesInHand += Cards.cardToMileage(h)

    #We have enough to make it directly, so let's go for it.    
    if milesInHand >= 300:
      return True

    #If we don't have 300 miles in hand and there are no cards to draw then we definitely don't want to go for it.
    if remainingCards == 0:
      return False
      
    #Plan: Assign equal probability for any mileage to be in any given players' unknown cards, remove those from the list.
    #Assign equal weight to draw each card to our team (just use 2 vs 3 for simplicity)
    #If we should draw the mileage we need more than X% of the time, we should go for it.
    #Start with x = 57%, test different values though on 50k runs minimum - start with 0%, 57%, 100%, make sure we can see
    #A difference over 50k runs, then adjust up or down from 57% based on results using a half the distance method.
    #Note: 57% is 4/7 and should be GTO based on scoring considerations.
      
    #Need to handle 200 mileage cards differently - we could only play 1, and we can only do that if we haven't played 2.
    #Making these floats also because math.
    unknown25s = self.cardsLeft[0] * 1.0
    unknown50s = self.cardsLeft[1] * 1.0
    unknown75s = self.cardsLeft[2] * 1.0
    unknown100s = self.cardsLeft[3] * 1.0
    
    
    #If we can play a 200 and they exist in the deck
    if gameState.us.twoHundredsPlayed == 1 and self.cardsLeft[4] > 0:
      unknown200s = self.cardsLeft[4] * 1.0
      #Subtract expected number of 200s left in the deck after accounting for other players' hands
      unknown200s -= unknown200s * (6.0 * (totalPlayers - 1) / remainingCards)
      #Presume even chance for us to get one, but we can only use one.
      if (unknown200s / totalPlayers) > 1.0:
        expectedMiles += 200
      #If there's less than an even chance for us to get one, expected miles goes up by the chance we'll get one times 200.
      else:
        expectedMiles += (unknown200s / totalPlayers) * 200
      
    #We can use any number of 100s/75s/50s/25s so we can just do this:
    unknown100s -= unknown100s * (6.0 * (totalPlayers - 1) / remainingCards)
    expectedMiles += (unknown100s / totalPlayers) * 100

    unknown75s -= unknown75s * (6.0 * (totalPlayers - 1) / remainingCards)
    expectedMiles += (unknown75s / totalPlayers) * 75

    unknown50s -= unknown50s * (6.0 * (totalPlayers - 1) / remainingCards)
    expectedMiles += (unknown50s / totalPlayers) * 50        

    unknown25s -= unknown25s * (6.0 * (totalPlayers - 1) / remainingCards)
    expectedMiles += (unknown25s / totalPlayers) * 25
      
    #Amazingly this is the same for any game size.
    if expectedMiles >= 1250:
      return True
  
    else:
      return False
