"""Persistent game transcriptions.

File format: A series of games, each consisting of:
* Game header:
  * One byte number of players
  * For each player, in player number order:
    * One byte: Team number.
    * 16-bit network-order number: Length of player name.
    * Player name.
* For each hand:
    * Six bytes for each player: Initial hand, one card per byte.
    * Or, six 0xFF bytes (just once, not once per player) to indicate no more hands in game.
* For each move in a hand:
  * A 16-bit network-order number:
    * Bits 00-02: Player number of moving player; values of 6 and 7 are special, see below.
    * Bits 03-07: Card drawn.  Value of 31 means no card was drawn (because deck was exhausted.)
    * Bit  08:    Move type: 0=discard, 1=play
    * Bits 09-13: Card played
    * Bits 14-15: Target team (ignored for non-attacks)
  * If player number is 6, this isn't a move, but the remaining bits should instead be interpreted as:
    * Bit 3: The next move is a coup fourre.
    * Bit 4: The player moving next will be declaring an extension.
  * If player number is 7, all other fields are disregarded and there are no more moves in the hand.
"""
from mille.game import Game
from mille.move import Move
from mille.player import Player
from mille.team import Team

import struct
import weakref


MOVE_STRUCT = "!H"
PLAYERNO_SPECIAL_MOVE = 6
PLAYERNO_HAND_OVER = 7
SPECIAL_MOVE_COUP_FOURRE = 1 << 3
SPECIAL_MOVE_EXTENSION = 1 << 4
GAME_OVER_CARD = 0xFF
NO_DRAW_CARD = 0b11111

class TranscriptWriter(object):
  def __init__(self, path, game):
    """Args:
         path: File to append transcript to.
         game: Game object to write a transcript for.
    """
    if len(game.teams) > 4:
      raise Exception("TranscriptWriter only supports up to 4 teams!")
    if len(game.players) > 6:
      raise Exception("TranscriptWriter only supports up to 6 players!")

    self.stream = open(path, "ab")
    self.game = weakref.ref(game)
    game.transcriptWriter = self

  def writeGameStart(self):
    self.stream.write(struct.pack("!B", len(self.game().players)))
    for player in self.game().players:
      playerStr = "%s.%s" % (player.ai.__class__.__module__,
                             player.ai.__class__.__name__)
      self.stream.write(struct.pack("!BH",
                                    player.teamNumber,
                                    len(playerStr)))
      self.stream.write(playerStr)

  def writeHandStart(self):
    for player in self.game().players:
      self.stream.write(struct.pack("!BBBBBB", *player.hand))

  def writeMove(self, player, drawnCard, move, playerDeclaredExtension):
    if move.coupFourre:
      self.stream.write(struct.pack(MOVE_STRUCT,
                                    (PLAYERNO_SPECIAL_MOVE |
                                     SPECIAL_MOVE_COUP_FOURRE)))
    elif playerDeclaredExtension:
      self.stream.write(struct.pack(MOVE_STRUCT,
                                    (PLAYERNO_SPECIAL_MOVE |
                                     SPECIAL_MOVE_EXTENSION)))

    if move.target:
      target = move.target
    else:
      target = 0

    if drawnCard is None:
      drawnCard = NO_DRAW_CARD

    self.stream.write(struct.pack(MOVE_STRUCT,
                                  (player           |
                                   (drawnCard << 3) |
                                   (move.type << 8) |
                                   (move.card << 9) |
                                   (target << 14))))

  def writeHandEnd(self):
    self.stream.write(struct.pack(MOVE_STRUCT, PLAYERNO_HAND_OVER))

  def writeGameEnd(self):
    # Must be called after writeHandEnd!
    self.stream.write(struct.pack("!BBBBBB",
                                  GAME_OVER_CARD,
                                  GAME_OVER_CARD,
                                  GAME_OVER_CARD,
                                  GAME_OVER_CARD,
                                  GAME_OVER_CARD,
                                  GAME_OVER_CARD))
    self.stream.flush()


class TranscriptReader(object):
  def __init__(self, path, gameStartFn, handStartFn, moveFn, handEndFn, gameEndFn):
    """Args:
         path: File to read transcripts from.
         gameStartFn: Function to call when a new game is seen.  Function will be passed arguments:
           game: A Game object.
           playerNames: A list of the player names, in player number order.
         handStartFn: Function to call when a hand has begun.  Function will be passed a Game object.
         moveFn: Function to call when a move is seen.  Function will be passed arguments:
           game: A Game object.
           player: Player number of the player making the move.
           drawnCard: Card drawn for this move.
           move: Move object representing the player's action.
         handEndFn: Function to call when all a hand's moves have been seen.  Function will be passed a Game object.
         gameEndFn: Function to call when all a game's hands have been seen.  Function will be passed a Game object.
    """
    self.stream = open(path, "rb")
    self.gameStartFn = gameStartFn
    self.handStartFn = handStartFn
    self.moveFn = moveFn
    self.handEndFn = handEndFn
    self.gameEndFn = gameEndFn

  def read(self, debug = False):
    """Read as much of the transcript as possible."""

    while self._readGame(debug):
      while self._readNextHandStart():
        self.handStartFn(self.game)
        while self._readMove():
          pass
        self.game.computeHandScores()
        self.handEndFn(self.game)
      self.gameEndFn(self.game)

  def _readGame(self, debug):
    playerCountChar = self.stream.read(1)
    if len(playerCountChar) == 0:
      return False

    players = []
    teams = []
    playerNames = []

    # Read the game header.
    (playerCount,) = struct.unpack("!B", playerCountChar)
    for i in xrange(playerCount):
      (teamNo, playerNameLen) = struct.unpack("!BH", self.stream.read(3))
      playerNames.append(self.stream.read(playerNameLen))

      player = Player()
      player.number = i
      player.teamNumber = teamNo
      players.append(player)
      
    for teamNo in set(map(lambda player: player.teamNumber, players)):
      team = Team(number = teamNo)
      team.playerNumbers = [player.number
                            for player in players
                            if player.teamNumber == teamNo]
      teams.append(team)

    self.game = Game(None, teams = teams, players = players, debug = debug)
    self.gameStartFn(self.game, playerNames)
    return True

  def _readNextHandStart(self):
    self.game.resetHandState()
    for playerNo in xrange(len(self.game.players)):
      cards = struct.unpack("!BBBBBB", self.stream.read(6))
      if cards[0] == GAME_OVER_CARD:
        return False
      self.game.players[playerNo].hand = list(cards)
    return True

  def _readMove(self, coupFourre = False, declaredExtension = False):
    (num,) = struct.unpack(MOVE_STRUCT, self.stream.read(2))
    player = num & 0b111
    if player == PLAYERNO_HAND_OVER:
      return False
    elif player == PLAYERNO_SPECIAL_MOVE:
      if num & SPECIAL_MOVE_COUP_FOURRE:
        return self._readMove(coupFourre = True)
      elif num & SPECIAL_MOVE_EXTENSION:
        return self._readMove(declaredExtension = True)

    drawnCard = (num >> 3) & 0b11111
    if drawnCard == NO_DRAW_CARD:
      drawnCard = None

    moveType = (num >> 8) & 0b1
    moveCard = (num >> 9) & 0b11111
    moveTarget = (num >> 14) & 0b11
    move = Move(moveType, moveCard, moveTarget, coupFourre)

    if drawnCard is None:
      self.game.delayedAction = True
    else:
      self.game.players[player].hand.append(drawnCard)

    self.game.players[player].hand.remove(moveCard)

    playerObj = self.game.players[player]
    self.game.handleMove(playerObj,
                         self.game.teams[playerObj.teamNumber],
                         move,
                         forceExtension = declaredExtension)
    self.moveFn(self.game, player, drawnCard, move)
    return True
