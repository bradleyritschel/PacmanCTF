from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint
import time
from random import randint

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MyReflexAgent', second = 'MyReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)] # essentially this performs OffensiveReflexAgent(firstIndex)

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """

  def registerInitialState(self, gameState):
    self.lastEnemy1pos = (-1,-1)
    self.lastEnemy2pos = (-1,-1)
    if self.index in gameState.getRedTeamIndices():
      self.isRed = True
      self.isBlue = False
    else:
      self.isRed = False
      self.isBlue = True
    self.carrying = 0

    if self.isRed:
      self.enemy1Index = gameState.getBlueTeamIndices()[0]
      self.enemy2Index = gameState.getBlueTeamIndices()[1]
    else:
      self.enemy1Index = gameState.getRedTeamIndices()[0]
      self.enemy2Index = gameState.getRedTeamIndices()[1]

    self.enemy1Carrying = 0
    self.enemy2Carrying = 0
    self.lastFood = self.getFoodYouAreDefending(gameState).asList()
    self.numMovesWeScared = 0
    self.numMovesTheyScared = 0
    self.enemy1isScared = False
    self.enemy2isScared = False
    self.onOffense = True
    self.start = gameState.getAgentPosition(self.index)
    self.spawned = True
    self.returning = False
    self.IDnum = randint(0, 1000)
    self.lastCapsules = gameState.getCapsules()
    self.height = gameState.data.layout.height
    self.safeBoundaryXblue = gameState.data.layout.width / 2 - 1
    self.safeBoundaryXred = gameState.data.layout.width / 2
    self.dangerPos = []
    self.numMovesLeft = 300
    for x in range(gameState.data.layout.width):
      for y in range(self.height):
        if x-1 >= 0 and x+1 < gameState.data.layout.width and y+1 < self.height and y-1 >=0 and ((self.isBlue and x < self.safeBoundaryXred) or (self.isRed and x > self.safeBoundaryXblue)):
          numWalls = 0
          if gameState.getWalls()[x+1][y] or (x+1,y) in [pos[0] for pos in self.dangerPos]:
            numWalls += 1
          else:
            noWall = 'East'
          if gameState.getWalls()[x-1][y] or (x-1,y) in [pos[0] for pos in self.dangerPos]:
            numWalls += 1
          else:
            noWall = 'West'
          if gameState.getWalls()[x][y+1] or (x,y+1) in [pos[0] for pos in self.dangerPos]:
            numWalls += 1
          else:
            noWall = 'North'
          if gameState.getWalls()[x][y-1] or (x,y-1) in [pos[0] for pos in self.dangerPos]:
            numWalls += 1
          else:
            noWall = 'South'
          if numWalls == 3 and ((x,y),noWall) not in self.dangerPos:
            self.dangerPos.append(((x,y),noWall))
    numDangerPos = len(self.dangerPos)
    first = True
    newDangerPos = self.dangerPos
    while len(self.dangerPos) > numDangerPos or first:
      numDangerPos = len(self.dangerPos)
      first = False
          #[dangerPos[0] for dangerPos in self.dangerPos]:
      nextNewDangerPos = []
      for dangerPos in newDangerPos:
        pos, opening = dangerPos
        x,y = pos
        if x - 1 >= 0 and x + 1 < gameState.data.layout.width and y + 1 < self.height and y - 1 >= 0 and (
                (self.isBlue and x < self.safeBoundaryXred) or (self.isRed and x > self.safeBoundaryXblue)):
          if opening == 'North':
            if gameState.getWalls()[x-1][y+1] and gameState.getWalls()[x+1][y+1] and not gameState.getWalls()[x][y+1]: # if extension of current dead end
              if ((x, y+1), 'North') not in self.dangerPos:
                self.dangerPos.append(((x, y+1), 'North'))
                nextNewDangerPos.append(((x, y+1), 'North'))
            # if opening has a dead end two above it and a wall on one side one square above it, then the square above it is dangerous
            elif (x, y+2) in [danger[0] for danger in self.dangerPos] and (gameState.getWalls()[x-1][y+1] or gameState.getWalls()[x+1][y+1]):
              if gameState.getWalls()[x-1][y+1]: # wall to the west, so opening to the east
                if ((x, y+1), 'East') not in self.dangerPos:
                  self.dangerPos.append(((x, y+1), 'East'))
                  nextNewDangerPos.append(((x, y+1), 'East'))
              elif gameState.getWalls()[x+1][y+1]: # wall to the east, so opening to the west
                if ((x, y+1), 'West') not in self.dangerPos:
                  self.dangerPos.append(((x, y+1), 'West'))
                  nextNewDangerPos.append(((x, y+1), 'West'))
          elif opening == 'South':
            if gameState.getWalls()[x-1][y-1] and gameState.getWalls()[x+1][y-1] and not gameState.getWalls()[x][y-1]:
              if ((x, y-1), 'South') not in self.dangerPos:
                self.dangerPos.append(((x, y-1), 'South'))
                nextNewDangerPos.append(((x, y-1), 'South'))
            # if opening has a dead end two below it and a wall on one side one square below it, then the square below it is dangerous
            elif (x, y - 2) in [danger[0] for danger in self.dangerPos] and (
                      gameState.getWalls()[x - 1][y - 1] or gameState.getWalls()[x + 1][y - 1]):
              if gameState.getWalls()[x - 1][y + 1]:  # wall to the West, so opening to the east
                if ((x, y - 1), 'East') not in self.dangerPos:
                  self.dangerPos.append(((x, y - 1), 'East'))
                  nextNewDangerPos.append(((x, y - 1), 'East'))
              elif gameState.getWalls()[x + 1][y - 1]:  # wall to the east, so opening to the west
                if ((x, y - 1), 'West') not in self.dangerPos:
                  self.dangerPos.append(((x, y - 1), 'West'))
                  nextNewDangerPos.append(((x, y - 1), 'West'))
          elif opening == 'East':
            if gameState.getWalls()[x+1][y+1] and gameState.getWalls()[x+1][y-1] and not gameState.getWalls()[x+1][y]:
              if ((x+1, y), 'East') not in self.dangerPos:
                self.dangerPos.append(((x+1, y), 'East'))
                nextNewDangerPos.append(((x+1, y), 'East'))
            # if opening has a dead end two to the east of it and a wall on top or bottom one square east of it, then the square east it is dangerous
            elif (x+2, y) in [danger[0] for danger in self.dangerPos] and (
                      gameState.getWalls()[x+1][y+1] or gameState.getWalls()[x+1][y-1]):
              if gameState.getWalls()[x+1][y+1]:  # wall above, so opening south
                if ((x+1, y), 'South') not in self.dangerPos:
                  self.dangerPos.append(((x+1, y), 'South'))
                  nextNewDangerPos.append(((x+1, y), 'South'))
              elif gameState.getWalls()[x+1][y-1]:  # wall below, so opening north
                if ((x+1, y), 'North') not in self.dangerPos:
                  self.dangerPos.append(((x+1, y), 'North'))
                  nextNewDangerPos.append(((x+1, y), 'North'))
          elif opening == 'West':
            if gameState.getWalls()[x-1][y+1] and gameState.getWalls()[x-1][y-1] and not gameState.getWalls()[x-1][y]:
              if ((x-1, y), 'West') not in self.dangerPos:
                self.dangerPos.append(((x-1, y), 'West'))
                nextNewDangerPos.append(((x-1, y), 'West'))
            # if opening has a dead end two west of it and a wall on top or bottom one square west of it, then the square west of it is dangerous
            elif (x - 2, y) in [danger[0] for danger in self.dangerPos] and (
                    gameState.getWalls()[x - 1][y + 1] or gameState.getWalls()[x - 1][y - 1]):
              if gameState.getWalls()[x - 1][y + 1]:  # wall above, so opening south
                if ((x - 1, y), 'South') not in self.dangerPos:
                  self.dangerPos.append(((x - 1, y), 'South'))
                  nextNewDangerPos.append(((x - 1, y), 'South'))
              elif gameState.getWalls()[x + 1][y - 1]:  # wall below, so opening north
                if ((x - 1, y), 'North') not in self.dangerPos:
                  self.dangerPos.append(((x - 1, y), 'North'))
                  nextNewDangerPos.append(((x - 1, y), 'North'))
        for x in range(gameState.data.layout.width):
          for y in range(self.height):
            if x - 1 >= 0 and x + 1 < gameState.data.layout.width and y + 1 < self.height and y - 1 >= 0 and (
                    (self.isBlue and x < self.safeBoundaryXred) or (self.isRed and x > self.safeBoundaryXblue)):
              numWalls = 0
              if gameState.getWalls()[x + 1][y] or (x + 1, y) in [pos[0] for pos in self.dangerPos]:
                numWalls += 1
              else:
                noWall = 'East'
              if gameState.getWalls()[x - 1][y] or (x - 1, y) in [pos[0] for pos in self.dangerPos]:
                numWalls += 1
              else:
                noWall = 'West'
              if gameState.getWalls()[x][y + 1] or (x, y + 1) in [pos[0] for pos in self.dangerPos]:
                numWalls += 1
              else:
                noWall = 'North'
              if gameState.getWalls()[x][y - 1] or (x, y - 1) in [pos[0] for pos in self.dangerPos]:
                numWalls += 1
              else:
                noWall = 'South'
              if numWalls == 3 and ((x, y), noWall) not in self.dangerPos:
                self.dangerPos.append(((x, y), noWall))
                nextNewDangerPos.append(((x,y), noWall))
        newDangerPos = nextNewDangerPos

    # print(self.isRed)
    notWalls = []
    for pos in self.dangerPos:
      coord, direction = pos
      x,y = coord
      if not gameState.getWalls()[x][y]:
        notWalls.append(pos)
    self.dangerPos = notWalls

    # print("height, blue boundary, red boundary")
    # print(self.height, self.safeBoundaryXblue, self.safeBoundaryXred)
    CaptureAgent.registerInitialState(self, gameState)
    #debugDraw(self, cells, color, clear=False)

    dangerSquares = [dangerSquare[0] for dangerSquare in self.dangerPos]
    self.debugDraw(dangerSquares, [1, 0, 0], clear=False)

  def chooseAction(self, gameState):
    '''
    print("Number pellets enemy 1 carrying: ", self.enemy1Carrying)
    print("Number pellets enemy 2 carrying: ", self.enemy2Carrying)
    print("Number pellets I'm carrying: ", self.carrying)
    print(gameState.getInitialAgentPosition(self.getOpponents(gameState)[0]), gameState.getAgentState(self.getOpponents(gameState)[0]).getPosition())
    print(gameState.getInitialAgentPosition(self.getOpponents(gameState)[1]), gameState.getAgentState(self.getOpponents(gameState)[1]).getPosition())
    print("1: ", self.enemy1isScared)
    print("2: ", self.enemy2isScared)
    '''

    #if the enemy died, they are no longer scared
    enemy1pos = gameState.getAgentPosition(self.getOpponents(gameState)[0])
    e1x, e1y = enemy1pos
    lastE1x, lastE1y = self.lastEnemy1pos
    if abs(lastE1x - e1x) > 1:
      # print("Enemy Died")
      self.enemy1isScared = False
    self.lastEnemy1pos = enemy1pos

    enemy2pos = gameState.getAgentPosition(self.getOpponents(gameState)[1])
    e2x, e2y = enemy2pos
    lastE2x, lastE2y = self.lastEnemy2pos
    if abs(lastE2x - e2x) > 1:
      # print("Enemy Died")
      self.enemy2isScared = False
    self.lastEnemy2pos = enemy2pos




    '''
    if self.enemy1Index in gameState.getRedTeamIndices():
      spawnPos = (1, 4)
    else:
      spawnPos = (gameState.data.layout.width - 2, self.height-4)
    #print("Enemy spawn pos: ", spawnPos)
    self.debugDraw(spawnPos, [0, 1, 0], clear=False)
    if spawnPos == gameState.getAgentState(self.getOpponents(gameState)[0]).getPosition() or self.numMovesTheyScared <= 0:
      self.enemy1isScared = False
      if spawnPos == gameState.getAgentState(self.getOpponents(gameState)[0]).getPosition():
        print("ENEMY DIED")
    if spawnPos == gameState.getAgentState(self.getOpponents(gameState)[1]).getPosition() or self.numMovesTheyScared <= 0:
      self.enemy2isScared = False
      if spawnPos == gameState.getAgentState(self.getOpponents(gameState)[1]).getPosition():
        print("ENEMY DIED")
    '''


    self.numMovesLeft -= 1
    enemyFood = self.getFoodYouAreDefending(gameState).asList()
    if len(enemyFood) < len(self.lastFood): # update food that enemies are carrying
      eaten = []
      for food in self.lastFood:
        if food not in enemyFood:
          eaten.append(food)
      if gameState.getAgentPosition(self.enemy1Index) in eaten:
        self.enemy1Carrying += 1
        # print("Enemy 1 carrying: ", self.enemy1Carrying)
      if gameState.getAgentPosition(self.enemy2Index) in eaten:
        self.enemy2Carrying += 1
        # print("Enemy 2 carrying: ", self.enemy2Carrying)
    en1X, en1Y = gameState.getAgentPosition(self.enemy1Index)
    en2X, en2Y = gameState.getAgentPosition(self.enemy2Index)
    if (self.enemy1Index in gameState.getRedTeamIndices() and en1X < self.safeBoundaryXred) or \
    (self.enemy1Index not in gameState.getRedTeamIndices() and en1X > self.safeBoundaryXblue):
      self.enemy1Carrying = 0
    if (self.enemy2Index in gameState.getRedTeamIndices() and en2X < self.safeBoundaryXred) or \
    (self.enemy2Index not in gameState.getRedTeamIndices() and en2X > self.safeBoundaryXblue):
      self.enemy2Carrying = 0

    myX, myY = gameState.getAgentPosition(self.index)
    if (self.index in gameState.getRedTeamIndices() and myX < self.safeBoundaryXred) or \
            (self.index not in gameState.getRedTeamIndices() and myX > self.safeBoundaryXblue):
      self.carrying = 0

    '''
    if red, safeBoundaryX = gameState.data.layout.width / 2 - 1
    gameState.data.layout.height
    '''
    # print(self.IDnum)
    self.lastFood = self.getFoodYouAreDefending(gameState).asList()
    # print("Carrying: ", self.carrying)
    #time.sleep(1)
    # update whether on offense or defense
    # when we go offensive, we want to stay offensive until we return or are killed
    # if you are carrying a pellet and next to home, just go home
    if self.carrying > 0:
      x,y = gameState.getAgentState(self.index).getPosition()
      if self.isRed and x == self.safeBoundaryXred and gameState.getWalls()[self.safeBoundaryXblue][int(y)] == False:
        self.carrying = 0
        return 'West'
      elif self.isBlue and x == self.safeBoundaryXblue and gameState.getWalls()[self.safeBoundaryXred][int(y)] == False:
        self.carrying = 0
        return 'East'
    if len(gameState.getCapsules()) < len(self.lastCapsules): # new power pellet activated
      for capsule in self.lastCapsules:
        if capsule not in gameState.getCapsules():
          eatenCapsule = capsule
      x,y = eatenCapsule
      if self.isRed:
        if x < self.safeBoundaryXred:
          self.numMovesWeScared = 40
        else:
          self.numMovesTheyScared = 40
          self.enemy1isScared = True
          self.enemy2isScared = True
      else:
        if x > self.safeBoundaryXblue:
          self.numMovesWeScared = 40
        else:
          self.numMovesTheyScared = 40
          self.enemy1isScared = True
          self.enemy2isScared = True
      self.lastCapsules = gameState.getCapsules()
    foodLeft = len(self.getFood(gameState).asList())
    score = self.getScore(gameState)
    '''
    # Red team scores are positive, while Blue team scores are negative. <- score is always positive is good for you
    if (self.isRed and score < 0) or (self.isBlue and score > 0):
      weAreLosing = True
    else:
      weAreLosing = False
    if weAreLosing:
      print("We are losing")
    else:
      print("We are winning")
    '''
    x, y = gameState.getAgentState(self.index).getPosition()
    if (self.isRed and x > self.safeBoundaryXblue) or (self.isBlue and x < self.safeBoundaryXred): #boundary blue is 16, boundary red is 17
      notHome = True
    else:
      notHome = False
    validMiddleCoords = []
    if self.index in gameState.getRedTeamIndices():
      x = self.safeBoundaryXblue
    else:
      x = self.safeBoundaryXred
    walls = gameState.getWalls()
    for y in range(self.height):
      if not walls[x][y]:
        validMiddleCoords.append((x, y))
    curPos = gameState.getAgentState(self.index).getPosition()
    distanceHome = max(1, min([self.getMazeDistance(curPos, centerPoint) for centerPoint in validMiddleCoords]))
    if (foodLeft <= 2 or (len(self.getFoodYouAreDefending(gameState).asList()) <= 2) or
        (len(self.getFoodYouAreDefending(gameState).asList()) <= 6 and score >= 0)) and notHome\
            or self.numMovesLeft < 2*distanceHome: # if 2 or less food, return home ASAP and go on defense
      x, y = gameState.getAgentState(self.index).getPosition()
      if self.red:
        if x > self.safeBoundaryXblue:
          self.returning = True
        else:
          self.returning = False
          self.onOffense = False
      else:
        if x < self.safeBoundaryXred:
          self.returning = True
        else:
          self.returning = False
          self.onOffense = False
    elif (self.numMovesWeScared > 0 or self.numMovesTheyScared > 0) and len(self.getFood(gameState).asList()) > 5: # power pellet is active
      self.onOffense = True
      self.numMovesWeScared -= 1
      self.numMovesTheyScared -= 1
      if self.numMovesTheyScared == 1:
        pass
        # print("Enemy being scared about to expire")
        # time.sleep(2)
      elif self.numMovesWeScared == 1:
        pass
        # print("Us being scared about to expire")
        # time.sleep(2)
    # print(gameState.getCapsules())
    elif gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition() and not self.spawned:
      self.onOffense = False #when killed, default to defense
      self.carrying = 0
      self.returning = False
    elif not self.onOffense: # if we are not on offense, determine whether to go offensive depending on who the closest invader is and how many pellets they are carrying, and how close the closest food is that we wish to capture
      if self.index in gameState.getRedTeamIndices():
        enemies = gameState.getBlueTeamIndices()
        for enemy in enemies:
          x,y = gameState.getAgentPosition(enemy)
          if x > self.safeBoundaryXblue:
            enemies.remove(enemy)
      else:
        enemies = gameState.getRedTeamIndices()
        for enemy in enemies:
          x,y = gameState.getAgentPosition(enemy)
          if x < self.safeBoundaryXred:
            enemies.remove(enemy)
      if enemies == []:
        distClosestEnemy = 999
      elif len(enemies) == 1:
        enemyIndex = enemies[0]
        distClosestEnemy = self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(enemyIndex))
        if enemyIndex == self.getOpponents(gameState)[0]:
          numPelletsEnemyCarrying = self.enemy1Carrying
        else:
          numPelletsEnemyCarrying = self.enemy2Carrying
      else:
        if self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(enemies[0])) < self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(enemies[1])):
          distClosestEnemy = self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(enemies[0]))
          numPelletsEnemyCarrying = self.enemy1Carrying
        else:
          distClosestEnemy = self.getMazeDistance(gameState.getAgentPosition(self.index),
                                                  gameState.getAgentPosition(enemies[1]))
          numPelletsEnemyCarrying = self.enemy2Carrying
      foodList = self.getFood(gameState).asList() + self.getCapsules(gameState)
      if len(foodList) == 0:
        distClosestFood = 999
      else:
        distClosestFood = min([self.getMazeDistance(gameState.getAgentPosition(self.index), food) for food in foodList])
      # distClosestFood = min([self.getMazeDistance(gameState.getAgentPosition(self.index), food) for food in foodList])
      if numPelletsEnemyCarrying == 0:
        numPelletsEnemyCarrying = 1
      else:
        numPelletsEnemyCarrying += 1
      if distClosestFood < (distClosestEnemy/(numPelletsEnemyCarrying*numPelletsEnemyCarrying)) and len(self.getFoodYouAreDefending(gameState).asList()) > 2: #how close closest food is to our side would be better
        self.onOffense = True
    elif self.onOffense: # if on offense on our side and an enemy on our side is closer than the closest pellet, go defensive
      onOurSide = []
      myPos = gameState.getAgentPosition(self.index)
      x,y = myPos
      if self.index in gameState.getRedTeamIndices():
        if x < self.safeBoundaryXred:
          enemies = gameState.getBlueTeamIndices()
          for enemy in enemies:
            x,y = gameState.getAgentPosition(enemy)
            if x < self.safeBoundaryXred:
              onOurSide.append(enemy)
      else:
        if x >= self.safeBoundaryXred:
          enemies = gameState.getRedTeamIndices()
          for enemy in enemies:
            x, y = gameState.getAgentPosition(enemy)
            if x >= self.safeBoundaryXred:
              onOurSide.append(enemy)
      if len(onOurSide) != 0:
        if len(onOurSide) == 1:
          enemyIndex = onOurSide[0]
          distClosestEnemy = self.getMazeDistance(gameState.getAgentPosition(self.index),
                                                  gameState.getAgentPosition(enemyIndex))
          if enemyIndex == self.getOpponents(gameState)[0]:
            numPelletsEnemyCarrying = self.enemy1Carrying
          else:
            numPelletsEnemyCarrying = self.enemy2Carrying
        elif len(onOurSide) == 2:
          if self.getMazeDistance(gameState.getAgentPosition(self.index),
                                  gameState.getAgentPosition(enemies[0])) < self.getMazeDistance(
                  gameState.getAgentPosition(self.index), gameState.getAgentPosition(enemies[1])):
            distClosestEnemy = self.getMazeDistance(gameState.getAgentPosition(self.index),
                                                    gameState.getAgentPosition(enemies[0]))
            numPelletsEnemyCarrying = self.enemy1Carrying
          else:
            distClosestEnemy = self.getMazeDistance(gameState.getAgentPosition(self.index),
                                                    gameState.getAgentPosition(enemies[1]))
            numPelletsEnemyCarrying = self.enemy2Carrying
        foodList = self.getFood(gameState).asList() + self.getCapsules(gameState)
        if len(foodList) == 0:
          distClosestFood = 999
        else:
          distClosestFood = min([self.getMazeDistance(gameState.getAgentPosition(self.index), food) for food in foodList])
        if numPelletsEnemyCarrying == 0:
          numPelletsEnemyCarrying = 1
        else:
          numPelletsEnemyCarrying += 1

        distClosestEnemy = min([self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(enemy)) for enemy in onOurSide])
        if (distClosestEnemy/ (numPelletsEnemyCarrying*numPelletsEnemyCarrying)) < distClosestFood: # consider number of pellets enemy carrying
          self.onOffense = False
    # print(self.onOffense)
    self.spawned = False
    """
    Picks among the actions with the highest Q(s,a).
    """
    #if we are on defense and on our side and an enemy is on our side right next to us, kill them
    # to be on blue side x must be greater than safeboundary blue, to be on red side x must be less than safeboundary red
    myX, myY = gameState.getAgentState(self.index).getPosition()
    weAreOnOurSide = (self.index in gameState.getRedTeamIndices() and myX < self.safeBoundaryXred) or \
            (self.index not in gameState.getRedTeamIndices() and myX > self.safeBoundaryXblue)
    if not self.onOffense and weAreOnOurSide:
      for opponentIndex in self.getOpponents(gameState):
        theyAreOnOurSide = (opponentIndex not in gameState.getRedTeamIndices() and gameState.getAgentPosition(opponentIndex)[0] < self.safeBoundaryXred) or \
                           (opponentIndex in gameState.getRedTeamIndices() and gameState.getAgentPosition(opponentIndex)[0] > self.safeBoundaryXblue)
        if theyAreOnOurSide:
          enX, enY = gameState.getAgentPosition(opponentIndex)
          myX, myY = gameState.getAgentState(self.index).getPosition()
          if enX == myX + 1 and enY == myY:
            # print("Next to enemy, killing")
            return 'East'
          elif enX == myX - 1 and enY == myY:
            # print("Next to enemy, killing")
            return 'West'
          elif enX == myX and enY == myY + 1:
            # print("Next to enemy, killing")
            return 'North'
          elif enX == myX and enY == myY - 1:
            # print("Next to enemy, killing")
            return 'South'
        # if we are on defense and on our side and an enemy is on our side right next to us, kill them
        # to be on blue side x must be greater than safeboundary blue, to be on red side x must be less than safeboundary red
    
    if self.onOffense and not weAreOnOurSide: # if we are on offense and on the enemy side, if an enemy is next to us that is scared, then just kkill them
      for opponentIndex in self.getOpponents(gameState):
        theyAreOnOurSide = (opponentIndex not in gameState.getRedTeamIndices() and
                            gameState.getAgentPosition(opponentIndex)[0] < self.safeBoundaryXred) or \
                           (opponentIndex in gameState.getRedTeamIndices() and
                            gameState.getAgentPosition(opponentIndex)[0] > self.safeBoundaryXblue)
        if opponentIndex == self.getOpponents(gameState)[0]:
          isScared = self.enemy1isScared
        else:
          isScared = self.enemy2isScared
        if not theyAreOnOurSide and isScared: # if they are on their side and is scared, kill them
          enX, enY = gameState.getAgentPosition(opponentIndex)
          myX, myY = gameState.getAgentState(self.index).getPosition()
          if enX == myX + 1 and enY == myY:
            # print("Next to enemy, killing")
            return 'East'
          elif enX == myX - 1 and enY == myY:
            # print("Next to enemy, killing")
            return 'West'
          elif enX == myX and enY == myY + 1:
            # print("Next to enemy, killing")
            return 'North'
          elif enX == myX and enY == myY - 1:
            # print("Next to enemy, killing")
            return 'South'


    actions = gameState.getLegalActions(self.index) #if on defense, remove actions that would put us on the other side
    actions.remove('Stop')
    e1pos = gameState.getAgentPosition(self.enemy1Index)
    e2pos = gameState.getAgentPosition(self.enemy2Index)
    badMoves = []
    for action in actions:
      successor = gameState.generateSuccessor(self.index, action)
      successorPos = successor.getAgentState(self.index).getPosition()
      myPos = gameState.getAgentState(self.index).getPosition()
      if ((self.getMazeDistance(myPos, e1pos) <= 2 or self.getMazeDistance(myPos, e2pos) <= 2) and not self.numMovesTheyScared > 0) and successorPos in [pos[0] for pos in self.dangerPos]:
        # print("Trap square!")
        actions.remove(action)
        badMoves.append(action)
    for action in actions:
      successor = gameState.generateSuccessor(self.index, action)
      successorPos = successor.getAgentState(self.index).getPosition()
      myPos = gameState.getAgentState(self.index).getPosition()
      if successorPos in [pos[0] for pos in self.dangerPos]:
        # print("Possible trap!")
        for pos in self.dangerPos:
          if successorPos == pos[0]:
            dangerPos = pos
            break
        pos, move = dangerPos #move is the opening
        x, y = pos
        foodList = self.getFood(gameState).asList()
        if move == 'North': #nearest food is northmost, so greatest y, while being less than or equal to current y of danger square
          closestFood = (-1, -1)
          for food in foodList:
            if food[0] == x and food[1] <= y and food[1] > closestFood[1]:
              closestFood = food
        elif move == 'South': #nearest food is southmost, so greatest y, while being less than current y
          closestFood = (100, 100)
          for food in foodList:
            if food[0] == x and food[1] >= y and food[1] < closestFood[1]:
              closestFood = food
        elif move == 'East': #nearest food is eastmost, so least x, while being greater than current x
          closestFood = (-1, -1)
          for food in foodList:
            if food[1] == y and food[0] <= x and food[0] > closestFood[0]:
              closestFood = food
        elif move == 'West': #nearest food is westmost, so greatest x, while being less than current x
          closestFood = (100, 100)
          for food in foodList:
            if food[1] == y and food[0] >= x and food[0] < closestFood[0]:
              closestFood = food
        if closestFood != (-1, -1) and closestFood != (100, 100):
          xFood, yFood = closestFood
          if move == 'North': #nearest food is northmost, so greatest y, while being less than or equal to current y of danger square
            searchSpace = ([x], range(yFood+1, y))
          elif move == 'South':
            searchSpace = ([x], range(y+1, yFood))
          elif move == 'East':
            searchSpace = (range(xFood+1, x+1), [y])
          elif move == 'West':
            searchSpace = (range(x+1,xFood+1), [y])
          possibleWalls = []
          xRange, yRange = searchSpace
          wallInPath = False
          for x in xRange:
            for y in yRange:
              # print(x, y)
              if gameState.getWalls()[x][y]:
                wallInPath = True

        if closestFood != (-1,-1) and closestFood != (100, 100) and not wallInPath:
          # print("Closest food found!")
          distSquareToFood = self.getMazeDistance(pos, closestFood)
          # you will get trapped if either enemy is ((not scared or they wont be scared when they reach you), and they are closer than twice the distance to the food)
          if (((not self.enemy1isScared or (self.numMovesTheyScared - (2 * distSquareToFood)) < 0)) and (self.getMazeDistance(myPos, e1pos) <= 1 + (2 * distSquareToFood))) or \
            (((not self.enemy2isScared or (self.numMovesTheyScared - (2 * distSquareToFood)) < 0)) and (self.getMazeDistance(myPos, e2pos) <= 1 + (2 * distSquareToFood))):
          # if (self.getMazeDistance(myPos, e1pos) <= 1+(2*distSquareToFood) or self.getMazeDistance(myPos, e2pos) <= 1+(2*distSquareToFood)) and \
          #        not (self.numMovesTheyScared - 2*distSquareToFood) > 0:
            '''
            print("enemy distance 1: ", self.getMazeDistance(myPos, e1pos))
            print("enemy distance 2: ", self.getMazeDistance(myPos, e2pos))
            print("My position", pos)
            print("Closest food", closestFood)
            print("Distance to food", distSquareToFood)
            print(1 + (2 * distSquareToFood))
            print("Would get trapped!")
            '''
            successor = gameState.generateSuccessor(self.index, action)
            successorPos = successor.getAgentPosition(self.index)
            myPos = gameState.getAgentPosition(self.index)
            if self.index in gameState.getRedTeamIndices():
              x = self.safeBoundaryXblue
            else:
              x = self.safeBoundaryXred
            for y in range(self.height):
              if not walls[x][y]:
                validMiddleCoords.append((x, y))
            sucDistanceHome = max(1, min([self.getMazeDistance(successorPos, centerPoint) for centerPoint in validMiddleCoords]))
            curDistanceHome = max(1, min([self.getMazeDistance(myPos, centerPoint) for centerpoint in validMiddleCoords]))
            if curDistanceHome < sucDistanceHome: # move would put us further from home
              actions.remove(action)
              badMoves.append(action)
    if self.returning:
      # print("RETURNING FTW!")
      values = [self.evaluateReturn(gameState, a) for a in actions]
      # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
      for a, v in zip(actions, values):
        # print(a, v)
        pass
      if len(values) == 0:
        return random.choice(gameState.getLegalActions(self.index))
      maxValue = max(values)
      bestActions = [a for a, v in zip(actions, values) if v == maxValue]

      # print(bestActions)
      choice = random.choice(bestActions)

      successor = gameState.generateSuccessor(self.index, choice)
      foodList = self.getFood(gameState).asList() + self.getCapsules(gameState)
      if successor.getAgentState(self.index).getPosition() in foodList:
        self.carrying += 1
      # update carrying count to 0 if about to cross to our side
      sx, sy = successor.getAgentState(self.index).getPosition()
      curx, cury = gameState.getAgentPosition(self.index)
      if self.isRed and sx == self.safeBoundaryXblue and curx == self.safeBoundaryXred:
        self.carrying = 0
        self.returning = False
      elif self.isBlue and sx == self.safeBoundaryXred and curx == self.safeBoundaryXblue:
        self.carrying = 0
        self.returning = False

      return choice
    # or add a feature and weight that crossing to the other side on defense is bad
    actions = gameState.getLegalActions(self.index)  # if on defense, remove actions that would put us on the other side
    actions.remove('Stop')
    if not self.onOffense:
      if self.isRed:
        for action in actions:
          successor = gameState.generateSuccessor(self.index, action)
          pos = successor.getAgentState(self.index).getPosition()
          x, y = pos
          if x > self.safeBoundaryXblue:
            actions.remove(action)
      else:
        for action in actions:
          successor = gameState.generateSuccessor(self.index, action)
          pos = successor.getAgentState(self.index).getPosition()
          x, y = pos
          if x < self.safeBoundaryXred:
            actions.remove(action)
    for action in badMoves:
      actions.remove(action)
    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
    for a, v in zip(actions, values):
      # print(a, v)
      pass
    if len(values) == 0:
      return random.choice(gameState.getLegalActions(self.index))
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    # print(bestActions)
    choice = random.choice(bestActions)
    successor = gameState.generateSuccessor(self.index, choice)
    foodList = self.getFood(gameState).asList() + self.getCapsules(gameState)
    if successor.getAgentState(self.index).getPosition() in foodList:
      self.carrying += 1
    #update carrying count to 0 if about to cross to our side
    sx, sy = successor.getAgentState(self.index).getPosition()
    curx, cury = gameState.getAgentPosition(self.index)
    if self.isRed and sx == self.safeBoundaryXblue and curx == self.safeBoundaryXred:
      self.carrying = 0
    elif self.isBlue and sx == self.safeBoundaryXred and curx == self.safeBoundaryXblue:
      self.carrying = 0
    return choice

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluateReturn(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    pos = successor.getAgentState(self.index).getPosition()
    x,y = pos
    enemies = self.getOpponents(gameState)
    ghosts = []
    for index, enemy in enumerate(enemies): # ignore enemies that are scared
      if self.getOpponents(gameState)[0] == index:
        isScared = self.enemy1isScared
      else:
        isScared = self.enemy2isScared
      if not gameState.getAgentState(enemy).isPacman and not isScared:
        # print("Enemy is a ghost")
        ghosts.append(enemy)
    invaders = [gameState.getAgentPosition(a) for a in ghosts]
    if len(invaders) == 0:
      minDistance = 999
    else:
      minDistance = max(1, min([self.getMazeDistance(pos, invader) for invader in invaders]))
    features['distanceToEnemyGhost'] = (1.0 / minDistance) * (1.0 / minDistance)

    validMiddleCoords = []
    if self.index in gameState.getRedTeamIndices():
      x = self.safeBoundaryXblue
    else:
      x = self.safeBoundaryXred
    walls = gameState.getWalls()
    for y in range(self.height):
      if not walls[x][y]:
        validMiddleCoords.append((x, y))
    distance = max(1, min([self.getMazeDistance(pos, centerPoint) for centerPoint in validMiddleCoords]))
    features['distanceHome'] = distance

    weights = {'distanceToEnemyGhost': -50, 'distanceHome': -10} #-1 and -5000 worked
    return features * weights


  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    # print(features)
    weights = self.getWeights(gameState, action)
    # print(weights)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class MyReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def __init__(self, index):
    ReflexCaptureAgent.__init__(self, index)

  def getFeatures(self, gameState, action):
    if self.onOffense:
      features = util.Counter()
      successor = self.getSuccessor(gameState, action)
      foodList = self.getFood(successor).asList() + self.getCapsules(gameState)
      features['successorScore'] = -len(foodList)#self.getScore(successor)

      if self.index == self.getTeam(gameState)[1]:
        teammateIndex = self.getTeam(gameState)[0]
      else:
        teammateIndex = self.getTeam(gameState)[1]

      myPos = gameState.getAgentState(self.index).getPosition()
      myX, myY = myPos
      teammatePos = gameState.getAgentState(teammateIndex).getPosition()
      teammateX, teammateY = teammatePos

      if (self.isRed and teammateX > self.safeBoundaryXblue and myX > self.safeBoundaryXblue) or (self.isBlue and teammateX < self.safeBoundaryXred and myX < self.safeBoundaryXred):
        #we don't want our agents stepping on eachothers' toes when they are both offensive, on the other side
        if self.index == self.getTeam(gameState)[1]:
          teammateIndex = self.getTeam(gameState)[0]
        else:
          teammateIndex = self.getTeam(gameState)[1]
        teammateState = gameState.getAgentState(teammateIndex)
        teammatePos = teammateState.getPosition()
        nextPos = successor.getAgentState(self.index).getPosition()
        # print(nextPos, teammatePos)
        # print(self.getMazeDistance(nextPos, teammatePos))
        mateDistance = max(1,self.getMazeDistance(nextPos, teammatePos))
        features['distanceToPartner'] = (1.0/mateDistance)*(1.0/mateDistance) # make sure does not do integer division to 0

      # Compute distance to the nearest food

      if len(foodList) > 0: # This should always be True,  but better safe than sorry
        myPos = successor.getAgentState(self.index).getPosition()
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance

      # compute distance to nearest enemy ghost
      x,y = myPos
      if not (self.enemy1isScared and self.enemy2isScared) and ((self.index in gameState.getRedTeamIndices() and x > self.safeBoundaryXblue) or (self.index in gameState.getBlueTeamIndices() and x < self.safeBoundaryXred)):
        enemies = self.getOpponents(gameState)
        ghosts = []
        enemyNumber = 0
        for enemy in enemies:
          if enemyNumber == 0:
            isScared = self.enemy1isScared
          else:
            isScared = self.enemy2isScared
          if not gameState.getAgentState(enemy).isPacman and not isScared:
            ghosts.append(enemy)
          enemyNumber += 1

        invaders = [gameState.getAgentPosition(a) for a in ghosts]
        '''
        if self.index in gameState.getRedTeamIndices(): # red team
          for invader in invaders:
            x,y = invader
        else: #blue team
          for invader in invaders:
       '''
        if len(invaders) != 0:
          minDistance = max(1,min([self.getMazeDistance(myPos, invader) for invader in invaders]))
          features['distanceToEnemyGhost'] = (1.0/minDistance)*(1.0/minDistance)
        # minDistance = min([self.getMazeDistance(myPos, invader.getPosition()) for invader in invaders])
      # we want to explore less the more pellets we are carrying
      # -1*(number pellets carrying)(min maze distance from home)
      if not self.numMovesTheyScared > 0:
        validMiddleCoords = []
        if self.index in gameState.getRedTeamIndices():
          x = self.safeBoundaryXblue
        else:
          x = self.safeBoundaryXred
        walls = gameState.getWalls()
        for y in range(self.height):
          if not walls[x][y]:
            validMiddleCoords.append((x, y))
        distance = max(1, min([self.getMazeDistance(myPos, centerPoint) for centerPoint in validMiddleCoords]))
        features['riskOfPelletLoss'] = self.carrying * distance
      return features

    else: # defensive
      features = util.Counter()
      successor = self.getSuccessor(gameState, action)

      myState = successor.getAgentState(self.index)
      myPos = myState.getPosition()

      # Computes distance to invaders we can see
      enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
      invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
      features['numInvaders'] = len(invaders)
      if len(invaders) > 0:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
        features['invaderDistance'] = min(dists)

      #if action == Directions.STOP: features['stop'] = 1
      rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
      if action == rev: features['reverse'] = 1

      # we want to defend closer to the middle to prevent entries and exits
      validMiddleCoords = []
      '''
      if self.index in gameState.getRedTeamIndices(): # always red team left, blue team right
        bottomLeft = gameState.getInitialAgentPosition(self.index)
        topRight = gameState.getInitialAgentPosition(gameState.getBlueTeamIndices()[0])
      else:
        bottomLeft = gameState.getInitialAgentPosition(gameState.getBlueTeamIndices()[0])
        topRight = gameState.getInitialAgentPosition(self.index)
      print(bottomLeft, topRight)
      '''
      if self.index in gameState.getRedTeamIndices():
        x = self.safeBoundaryXblue
      else:
        x = self.safeBoundaryXred
      walls = gameState.getWalls()
      for y in range(self.height):
        if not walls[x][y]:
          validMiddleCoords.append((x,y))
      distance = max(1, min([self.getMazeDistance(myPos, centerPoint) for centerPoint in validMiddleCoords]))
      features['distToCenter'] = distance

      return features

  def getWeights(self, gameState, action):
    if self.onOffense:
      return {'successorScore': 100, 'distanceToPartner': -10, 'distanceToFood': -4, 'distanceToEnemyGhost': -20, 'riskOfPelletLoss': -2} # add one for minimum distance from enemy that is a ghost
    else: #defensive
      return {'numInvaders': 10, 'invaderDistance': -5, 'reverse': -2, 'distToCenter': -1}