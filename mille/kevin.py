# @author Kevin Hoeschele

from mille.ai import AI
from mille.cards import Cards
from mille.move import Move


from inspect import getmembers
from pprint import pprint
import sys

class KevinAI(AI):




  def makeMove(self, gameState):
    discards = []
    mileage = []
    attacks = []
    remedies = []
    safeties = []

    cardsPlayed=[]
    us = gameState.us
    cardsPlayed = cardsPlayed + us.mileagePile
    cardsPlayed = cardsPlayed + us.speedPile
    cardsPlayed = cardsPlayed + us.battlePile
    cardsPlayed = cardsPlayed + us.safeties



    MyMileage = us.mileage
    MyRunningTotal = MyMileage + us.totalScore + len(us.safeties)* 100 + us.coupFourres * 300


    opponents = gameState.opponents
    ourSafeties = us.safeties
    playedSafeties = ourSafeties
    opponentsCount=0
    opponentsSafeties =[]
    for opponent in opponents:
      opponentsCount = opponentsCount +1
      opponentsSafeties = opponentsSafeties + opponent.safeties
      cardsPlayed = cardsPlayed + opponent.mileagePile
      cardsPlayed = cardsPlayed + opponent.speedPile
      cardsPlayed = cardsPlayed + opponent.battlePile
      cardsPlayed = cardsPlayed + opponent.safeties
    playedSafeties = playedSafeties + opponentsSafeties

    cardsPlayed = cardsPlayed + gameState.discardPile
    cardPlayedByType= {}
    for x in xrange(0,19):
      cardPlayedByType[x]=0

    for card in cardsPlayed:
      cardPlayedByType[card] +=1


    target = gameState.target
    target_minus_25 = target - 25
    target_minus_50 = target - 50
    target_minus_75 = target - 75
    target_minus_100 = target - 100
    target_minus_200 = target - 200



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



    #######################
    #  IF CAN GO FOR WIN  DO IT!
    #######################

    if len(mileage) > 0:
      if us.mileage == target_minus_25:
        for mi in mileage:
          if mi.card == Cards.MILEAGE_25:
            return mi
      elif us.mileage == target_minus_50:
        for mi in mileage:
          if mi.card == Cards.MILEAGE_50:
            return mi
      elif us.mileage == target_minus_75:
        for mi in mileage:
          if mi.card == Cards.MILEAGE_75:
            return mi
      elif us.mileage == target_minus_100:
        for mi in mileage:
          if mi.card == Cards.MILEAGE_100:
            return mi
      elif us.mileage == target_minus_200:
        for mi in mileage:
          if mi.card == Cards.MILEAGE_200:
            return mi

    ########################
    #  play a red card based on weighted factors
    #  but check to see if the corrosponding safety is known in play or in your hand
    #  if not known  dont play if less then X cards in deck
    #####################################




    numberOfCardsLeftToNotAttack=10


    if len(attacks) >0:
      highestWeight = -10
      weightedAttacks = {}
      for attack in attacks:
        opponent = gameState.teamNumberToTeam(attack.target)
        opponentMileage = opponent.mileage
        opponentRunningTotal = opponentMileage + opponent.totalScore + len(opponent.safeties)* 100 + opponent.coupFourres * 300
        weight = 0
        if opponentRunningTotal >= 3000:
 #         print "opponentRunningTotal >= 3500"
          weight +=1
        if opponentRunningTotal >= 3500:
 #         print "opponentRunningTotal >= 3500"
          weight +=1
        if opponentRunningTotal >= 4000:
#          print "opponentRunningTotal >= 4000"
          weight +=1
        if opponentRunningTotal >= 4500:
 #         print "opponentRunningTotal >= 4500"
          weight +=2
        if opponentRunningTotal >= MyRunningTotal+1000:
  #        print "opponentRunningTotal >= myRunningTotal+2000"
          weight +=1
        if opponentRunningTotal >= MyRunningTotal+2000:
  #        print "opponentRunningTotal >= myRunningTotal+2000"
          weight +=3
        if opponentMileage >= MyMileage+400:
   #       print "opponentMileage >= my mileage + 400"
          weight +=1

        if opponentMileage >=  target_minus_200:
          if opponentMileage >=  target_minus_50 and attack.card == Cards.ATTACK_SPEED_LIMIT:
            weight = -10
    #        print "opponet withi 50 of end and attack=limit"
          else:
            weight +=1
     #       print "opponent within 200 of end"
        if attack.card !=Cards.ATTACK_SPEED_LIMIT and attack.card !=Cards.ATTACK_STOP:
          weight +=0.6
        if attack.card ==Cards.ATTACK_SPEED_LIMIT:
          weight += 0
        if attack.card ==Cards.ATTACK_STOP:
          weight += 0.01
      #    print "attack card not limit or stop"


        corrospondingSafetyisNotKnown=True
        corrospondingSafety = Cards.attackToSafety(attack.card)
        if cardPlayedByType[corrospondingSafety] ==1:
          corrospondingSafetyisNotKnown = False
        for safet in safeties:
          if Cards.attackToSafety(attack.card) == safet.card:
           corrospondingSafetyisNotKnown = False

        if corrospondingSafetyisNotKnown:
          if gameState.cardsLeft < numberOfCardsLeftToNotAttack:
            weight = -10  #nop
       #     print "safety NOT known and gameState.cardsLeft < numberOfCardsLeftToNotAttack"
          else:
        #    print "safety not known"
            weight -= 0.5
          #print "proceed with attack!!!!!!!!!!"
        else:
         # print "safety KNOWN!"
          weight += 0.5
        #print "weight="+str(weight)
        if weight > highestWeight:
          highestWeight = weight
        weightedAttacks[weight]=attack

      if highestWeight > -1:
        #print "=============highest Weight="+str(highestWeight)
        #print weightedAttacks[highestWeight]
        return weightedAttacks[highestWeight]

      

    ##################3
    # play a remedy
    ##################

    if len(remedies) > 0:
      remedies.sort(key=lambda x: x.card)
      if remedies[0].card == Cards.REMEDY_END_OF_LIMIT and us.mileage >= target_minus_50 and len(mileage) > 0:
        mileage.sort(key=lambda x: x.card, reverse=True )
        #print "remedy= EOL AND us.mileage="+str(us.mileage)+" mileage[0]="+str(mileage[0].card)
        return mileage[0]
      else:
        return remedies[0]


    #####################
    # play a mileage:
    #      first check to see if you are 200 or less away, if any 2 card combonation in hand will finish race
    #      if not, play highest mileage 
    ######################

    if len(mileage) > 0:
      mileage.sort(key=lambda x: x.card, reverse=True )
      if len(mileage) > 2 and us.mileage > target_minus_200:
        num=0
        
        for mi in mileage:
          num +=1
          mileageCopy = mileage[num:]
          for mi2 in mileageCopy:
            mivalue = Cards.cardToMileage(mi.card)
            mi2value = Cards.cardToMileage(mi2.card)
            total = us.mileage + mivalue + mi2value
            if total == target:
              return mi
      return mileage[0]




    ##############################
    #  If have safety that solves a problem we have... use it
    ############################
    
    remedyNeeded = us.needRemedy
    if remedyNeeded > 0:
      for safet in safeties:
        if safet.card == Cards.remedyToSafety(remedyNeeded):
          return safet
    if us.speedLimit == True: 
     for safet in safeties:
        if safet.card == Cards.SAFETY_RIGHT_OF_WAY:
          return safet
     


    ####################
    # ENTER EASY DISCARD PHASE
    ##############

  # reuse these because this used to be in a seperate function
    mileage = []
    attacks = []
    remedies = []

    for play in discards:
      type = Cards.cardToType(play.card)
      if type == Cards.MILEAGE:
        mileage.append(play)
      elif type == Cards.REMEDY:
        remedies.append(play)
      elif type == Cards.ATTACK:
        attacks.append(play)






    ##################
    # Remedies we have safeties for in play, in hand or for all attacks have been played
    ################

    if len(remedies) > 0:
      for remedy in remedies:
        for safet in safeties:
          if Cards.remedyToSafety(remedy.card) == safet.card:
            return remedy      

        if Cards.remedyToSafety(remedy.card) in ourSafeties:
          return remedy
        corrospondingAttack = Cards.remedyToAttack(remedy.card)
        if corrospondingAttack ==Cards.ATTACK_FLAT_TIRE:
          if cardPlayedByType[Cards.ATTACK_FLAT_TIRE] == 3:
#            print "discard spare due to all flats played"
            return remedy
        elif corrospondingAttack ==Cards.ATTACK_OUT_OF_GAS:
          if cardPlayedByType[Cards.ATTACK_OUT_OF_GAS] == 3:
 #           print "discard gas due to all out of gas played"
            return remedy
        elif corrospondingAttack ==Cards.ATTACK_ACCIDENT:
          if cardPlayedByType[Cards.ATTACK_ACCIDENT] == 3:
  #          print "discard repairs due to all accidents played"
            return remedy
        elif corrospondingAttack ==Cards.ATTACK_SPEED_LIMIT:
          if cardPlayedByType[Cards.ATTACK_SPEED_LIMIT] == 4:
   #         print "discard end of limit due to all spedlimits played"
            return remedy


    ########################
    #   Attacks that opponents have safeties for (if not 3 or 6 person game)
    ######################

    if len(attacks) > 0:
      if opponentsCount ==1:
        for attack in attacks:
          if Cards.attackToSafety(attack.card) in opponentsSafeties:
            return attack




    ###################
    # mileage discard due to limit:  
    #     if an opponent has right of way and all EOL played and we have speed limit  discard mileage over 50
    ######################

    mileage.sort(key=lambda x: x.card)
    if len(mileage) > 0:
      opponentRightOfWay = False
      for safet in opponentsSafeties:
        if safet == Cards.SAFETY_RIGHT_OF_WAY:
          opponentRightOfWay = True
      if cardPlayedByType[Cards.REMEDY_END_OF_LIMIT] == 6 and us.speedLimit and opponentRightOfWay:

        for mi in mileage:
          if mi.card > 1:
            #print "discarding mi:" + Cards.cardToString(mi.card)
            return mi




    ########################
    #  milage that we can no longer play due to being to close to the end 
    # or playing 2 2 hundreds
    #########################

      thp = us.twoHundredsPlayed

      for mi in mileage:

        if thp == 2 or us.mileage > target_minus_200:
          if mi.card == Cards.MILEAGE_200:
            return mi
        if us.mileage > target_minus_100:
          if mi.card == Cards.MILEAGE_100:
            return mi
        if us.mileage > target_minus_75:
          if mi.card == Cards.MILEAGE_75:
            return mi
        if us.mileage > target_minus_50:
          if mi.card == Cards.MILEAGE_50:
            return mi






    #########################
    #  Enter "Smart" discard phases
    ########################

    ########################
    # Remedy smart discard:  remedies we have dupes of (save 1 of each, except GO  save 2)
    ###########################

    remedyDupes={}
    for x in xrange(5,10):
      remedyDupes[x]=0
    if len(remedies) > 0:
      for remedy in remedies:
        remedyDupes[remedy.card] += 1
      if remedyDupes[Cards.REMEDY_SPARE_TIRE] > 1:
        for remedy in remedies:
          if remedy.card == Cards.REMEDY_SPARE_TIRE:
            return remedy
      elif remedyDupes[Cards.REMEDY_GASOLINE] > 1:
        for remedy in remedies:
          if remedy.card == Cards.REMEDY_GASOLINE:
            return remedy
      elif remedyDupes[Cards.REMEDY_REPAIRS] > 1:
        for remedy in remedies:
          if remedy.card == Cards.REMEDY_REPAIRS:
            return remedy
      elif remedyDupes[Cards.REMEDY_GO] > 2:
        for remedy in remedies:
          if remedy.card == Cards.REMEDY_GO:
            return remedy
      elif remedyDupes[Cards.REMEDY_END_OF_LIMIT] > 1:
        for remedy in remedies:
          if remedy.card == Cards.REMEDY_END_OF_LIMIT:
            return remedy



   ####################
   # play a safety as no more easy discards are available
   ###################

    # Play a safety rather than discard
    if len(safeties) > 0:

      return safeties[0]






    ####################
    #  attack smart discard: if have more then 2 attack cards  discard stops/ speedlimits
    ####################

    attackDupes={}
    for x in xrange(10,16):
      attackDupes[x]=0

    if len(attacks) > 0:
      totalAttackCardsInHand=0
      for attack in attacks:
        totalAttackCardsInHand += 1
        attackDupes[attack.card] += 1
      if totalAttackCardsInHand > 2:
        for attack in attacks:
          if attack.card == Cards.ATTACK_SPEED_LIMIT:
            return attack 
          if attack.card == Cards.ATTACK_STOP:
            return attack





    #####################
    # final "smart" discard: if more then one mileage in hand discard lowest mileage
    # if exactly 1 mileage in hand  first discard a non GO remedy(starting with EOL, then an attack (order EOL, stop, then others)
    ########################

    if len(mileage) > 0:
      if len(mileage) == 1:


        remedies.sort(key=lambda x: x.card, reverse=True)
        for remedy in remedies:
          if remedy.card != Cards.REMEDY_GO:
            return remedy
        attacks.sort(key=lambda x: x.card, reverse=True)
        for attack in attacks:
          return attack
      else:
        return mileage[0]



    ##################
    #  discard whatever is left
    ##################

    return discards[0]  #toDiscard



  def playCoupFourre(self, attackCard, gameState):
    return True

  def goForExtension(self, gameState):
    us = gameState.us



    ############################
    #  last ditch effort, if opponent is past 5000, always go for extension
    ###########################

    MyMileage = us.mileage
    allFourSafeties = 0
    if len(us.safeties) == 4:
      allFourSafeties = 300

    tripComplete = 400

    safeTrip = 300
    if us.twoHundredsPlayed == 0:
      safeTrip= 300

    MyRunningTotal = MyMileage + us.totalScore + len(us.safeties)* 100 + us.coupFourres * 300 + allFourSafeties + tripComplete + safeTrip

    opponents = gameState.opponents
    shutout = False


    highestOpponentScore = 0
    for opponent in opponents:
      allFourSafeties = 0
      if opponent.mileage == 0:
        shutout=True

      if len(us.safeties) == 4:
        allFourSafeties = 300
      total = opponent.mileage + opponent.totalScore + len(opponent.safeties)*100 + opponent.coupFourres * 300 + allFourSafeties
      if total > highestOpponentScore:
        highestOpponentScore = total

    if shutout:
      MyRunningTotal += 500

    if highestOpponentScore > 5000:
      if MyRunningTotal <= highestOpponentScore:
#        print "last ditch effort my Total="+str(MyRunningTotal) + " highestOpponent="+str(highestOpponentScore)
        return True




    ################################
    # Blowout:
    #     else only go for extension if opponent is not moving, under 300 miles and over 75 cards in deck 

    opponents = gameState.opponents
    opponentsMoving = False
    opponentMaxMileage = 0
    for opponent in opponents:
      if opponent.moving:
        opponentsMoving = True
      if opponentMaxMileage < opponent.mileage:
        opponentMaxMileage = opponent.mileage


    if gameState.us.moving and gameState.cardsLeft > 75 and opponentsMoving == False and opponentMaxMileage < 300:
      return True
    return False




