# Mille Borne AI Challenge #

For this competition, you will implement an artificial intelligence to play
Mille Borne so that actual people will be saved from having to.

## Rules ##

You will submit a file called &lt;yourname&gt;ai.py, which includes a class called
&lt;YourName&gt; that implements the AI interface (see Technical Details, The AI
Interface).  You may also submit any other support file(s) you like,
including other classes, etc.  The combined files you submit should be a
reasonable size.  I reserve the right to decide what "reasonable" means.

Your AI should make decisions in a reasonable amount of time. I reserve the
right to decide what "reasonable" means.

Your AI should not interact with the running system beyond what's necessary
to implement the methods of the AI interface.  For example, it should not
read/write local files other than those you provide with it.

I made a basic effort to make it harder for AIs to "cheat" and interact with
a running game in ways outside the Mille Bornes rules, but it is of course
possible to do so anyway. AIs doing that will be disqualified.

The rules are subject to change before the final submission deadline.

## Scoring ##

The submitted AIs will play against each other in various configurations. 
Your AI may end up on a team with other AIs, the sample BasicAI, and/or
other instances of itself.  All that matters is the number of games won by
your AI.

I will run some very large number of games and tally the wins by each
competitor.  The AI with the most wins will be the victor.

## Getting Started ##

Rename mille/yournameai.py to use your actual name. In the file, change
"class YourNameAI" to use your actual name.  This class is a copy of the
BasicAI class from sampleais.py - see Technical Details, Sample AIs.

Edit play.py and import your class; near the top, above the line
``from mille.sampleais import *`` add
``from mille.&lt;yourname&gt;ai import &lt;YourName&gt;AI``

Then, change the competitors variable to include &lt;YourName&gt;AI.
For example, mine would look like:

```python
from mille.elliotai import ElliotAI
[...]
competitors = [ElliotAI, ManualAI]
```

Run play.py to play a game against your AI. At the end it will display the
number of wins for each AI.  You only played one game, so the single point
will go to either your AI or ManualAI.

Once you have made some changes to your AI, you can change the competitors
list to replace ManualAI with BasicAI to see how your AI fares against the
example AI.  In that case, you may also want to increase the number of games
that it plays to get better statistical data:

```python
games = 100
```

You can also change the number of players: 2, 3, 4, or 6. The play.py
program will cycle through the competitors to select players, so it's okay
to have fewer competitors than players.

```python
numPlayers = 2

```

Finally, you may want to turn on debugging output in the main game engine. 
To do that, simply change the option at the top of play.py.

```python
debug = True
```

## Technical Details ##

Here is information about the classes that are probably most interesting to
AI developers.  Feel free to look at the other classes in the framework, of
course.

### The AI Interface ###

Your AI should be a python class implementing the interface defined in
*mille/ai.py*. The interface has these methods:

* **makeMove(gameState)**
    Decide what to do on your turn. Returns a Move object, which can either
    be newly created or one of the ones provides in gameState.validMoves -
    see below for more information about GameState and Move objects. 
    Returning an invalid move will result in discarding the first card in
    your hand.

* **playerPlayed(player, move)**
    Called whenever a player makes a move, including yourself. Return value
    is ignored.  See below for more information about Player objects.

* **handEnded(scoreSummary)**
    Called when a hand is complete. The score summary is just a big
    multi-line text string suitable to be printed for human consuption. 
    Unless you want to do some end-of-hand processing in your AI, you
    probably don't need to implement this.

* **playCoupFourre(attackCard, gameState)**
    Decide whether or not to coup fourre an attack card being played on your
    team.  Returns True or False.  This will only be called if you legally
    *can* play a coup fourre, so it's quite reasonable just to return True
    all the time.

* **goForExtension(gameState)**
    Decide whether or not to go for the extension. Returns True or False. 
    Will be called when you play the last mileage card necessary to reach
    700 miles in a three-team game.

### Sample AIs ###

The sampleais.py file includes several sample AIs to use when developing
your own.

**BasicAI** plays a passable game despite being very simple. 

**ManualAI** asks the person at the keyboard to make moves, and so lets you play
against other AIs.

**JonsAwesomeAI** implements Jon's master Mille Bornes strategy: If you have a 25,
discard it.  Otherwise, discard another card.

### The Cards Class ###

Cards are represented by constants defined in the Cards static class. To
display them in human-readable form, use Cards.cardToString (for a single
card) or Cards.cardsToStrings (for a list of cards). 

There are various other static methods in the class that may be useful to AI
developers:

* **cardToMileage(card)**
    Returns the integer number of miles for a given mileage card. For
    MILEAGE_25, for example, it would return 25.

* **cardToString(card)**
    Returns a human-readable string describing the card. For MILEAGE_25, for
    example, it would return "25 Miles".

* **cardsToString(cards)**
    Returns a list of human-readable strings describing each card in the
    list.  For [MILEAGE_25], for example, it would return ["25 Miles"].

* **cardToType(card)**
    Returns a constant describing the type of card - MILEAGE, REMEDY,
    ATTACK, or SAFETY.  These constants are defined in the Cards class as
    well.

* **attackToRemedy(card)**
    Returns the remedy card that matches a given attack card. For
    ATTACK_STOP, for example, it would return REMEDY_GO.

* **attackToSafety(card)**
    Returns the safety card that matches a given attack card. For
    ATTACK_STOP, for example, it would return SAFETY_RIGHT_OF_WAY.

* **remedyToSafety(card)**
    Returns the safety card that matches a given remedy card. For REMEDY_GO,
    for example, it would return SAFETY_RIGHT_OF_WAY.

### GameState Objects ###

Each of the above methods will be passed a GameState object, which includes
all the information about the current state of the game that you need to
make a decision.  Its attributes are:

* **hand**
    A list of cards in your hand.

* **discardPile**
    A list of the cards in the discard pile. The most recently discarded is
    at the end of the list.

* **us**
    A Team object representing your team. See below for more information
    on Team objects.

* **opponents**
    A list of Team object representing the opposing
    teams.  Your own team is replaced with ``None``.  See below for more information
    on Team objects.

* **validMoves**
    A list of Move objects representing all of the legal moves available to
    you.  Only populated when passed to makeMove(), but if you really want
    it populated at other times you can call findValidPlays() on the
    GameState object yourself.

* **target**
    The current mileage target for the race. Will be either 700 or 1000
    depending on the number of players and whether anyone has chosen to go
    for the extension.

* **cardsLeft**
    The number of cards left in the deck.

It also has these methods:

* **findValidPlays**
    Updates the object's ``validMoves`` attribute.

* **teamNumberToTeam(teamNumber)**
    Given a team number of one of your opponents, returns the corresponding
    ``Team`` object.  Use this to get the ``Team`` for the target of an
    attack ``Move``.

### Team Objects ###

Describes a team, either your own or an opponents. Its attributes are:

* **number**
    The team number of this team.a

* **playerNumbers**
    A list of player numbers in the team.

* **totalScore**
    The team's score over multiple hands.

* **handScore**
    The team's score this hand. Not calculated until the end of the hand, so
    probably not interesting for AI developers.

* **mileage**
    How many miles the team has gone this hand.

* **mileagePile**
    A list representing the "mileage pile," which contains all mileage cards
    the team has played this hand.

* **speedPile**
    A list representing the "speed pile," which contains all Speed Limit
    cards played against the team and End of Limit cards played by the team
    during this hand.

* **battlePile**
    A list representing the "battle pile," which contains all non-Speed
    Limit attack cards played against the team and non-End of Limit remedy
    cards played by the team during this hand.

* **safeties**
    A list of the safeties this team has played this hand.

* **coupFourres**
    The number of coup fourres this team has played this hand.

* **moving**
    A boolean. Is this team moving?

* **speedLimit**
    A boolean. Is this team under a speed limit?

* **needRemedy**
    Which remedy card the team needs to move. Will be None if they're
    moving.

* **safeTrip**
    Has the team played any 200 mile cards this hand? Used in hand-end
    scoring.

* **twoHundredsPlayed**
    The number of 200 mile cards the team has played this hand. Teams
    are only allowed two per hand.

### Move Objects ###

A simple object describing a move: whether it's a discard or a play,
which card it is, and (for attacks) the number of the team it's
targetted at.  The constructor takes all of those attributes as
parameters.  Discard versus play is expressed as a constant defined in
this class, either DISCARD or PLAY.

For example:

```python
from move import Move
from cards import Cards

move1 = Move(Move.PLAY, Cards.REMEDY_GO)
move2 = Move(Move.DISCARD, Cards.MILEAGE_25)
move3 = Move(Move.PLAY, Cards.ATTACK_STOP, 0)
```
### Player Objects ###

Represents a player. Its attributes are:

* **number**
    The player number.

* **teamNumber**
    The number of the team the player is on.

* **hand**
    The cards in the player's hand. This will always be empty when it's
    passed to you.

* **ai**
    The AI object controlling the player. This will always be None when it's
    passed to you.
