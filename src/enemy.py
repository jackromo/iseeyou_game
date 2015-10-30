import pygame, random, math, copy, time
from flashlight import Flashlight, getActualAng


# enemy AI states
WANDERING = 0   # wandering around randomly
FOLLOWING = 1   # slowly following player, has heard them from a distance, similar to WANDERING but goes to closest intersect to player
CLOSE = 2       # within several steps of player, dischordant noise w/ each step, deviates from rail
CHASING = 3     # quickly following player, has been shined w/ flashlight
RETURNING = 4   # returning to rail after failing to catch player


class Enemy(object):

    def __init__(self, xPos, yPos, world):
        self.xPos = xPos
        self.yPos = yPos
        self.dx = self.dy = 0
        self.speed = 4
        self.sound = pygame.mixer.Sound("resources/sound/enemyNoise.wav")
        self.isSoundPlaying = False
        self.maxPlayerDistForSound = 3*(world.hallWidth + world.hallLength)  # dist where sound plays + enemy follows player
        self.currentPath = Path(world)
        gridX = (self.xPos - world.hallWidth) / (world.hallWidth + world.hallLength)
        gridY = (self.yPos - world.hallWidth) / (world.hallWidth + world.hallLength)
        self.currentPath.setPathBetween((gridX, gridY), (gridX, gridY))
        self.distDownPath = 0
        self.currentAI = WANDERING

    def update(self, world, player, flashlight, camPos):
        self.dx = 0; self.dy = 0
        self.dx, self.dy = self.getAIDecision(world, player, flashlight, camPos)
        # collision detection
        if not world.isInWorld(self.xPos + 2*self.dx, self.yPos): self.dx = 0
        if not world.isInWorld(self.xPos, self.yPos + 2*self.dy): self.dy = 0
        if self.dx!=0 and self.dy!=0 and not world.isInWorld(self.xPos+ 2*self.dx, self.yPos+ 2*self.dy):  # may be hitting edge of a corner
            self.dx = 0; self.dy = 0
        self.xPos += self.dx
        self.yPos += self.dy
        # play sound, if closer to player then sound = louder
        self.updateSound(player)

    def updateSound(self, player):
        """Update static noise of enemy to be louder if enemy is closer. Silent if too far away."""
        distToPlayer = math.sqrt((self.xPos-player.xPos)**2 + (self.yPos-player.yPos)**2)
        volume = 1.0 - (distToPlayer/self.maxPlayerDistForSound)  # will equal 1 (max volume) if distToPlayer = 0, less if distToPlayer > 0
        if not self.isSoundPlaying:
            self.sound.play(loops=-1)
            self.isSoundPlaying=True
        self.sound.set_volume(0 if distToPlayer > self.maxPlayerDistForSound else volume)

    def followPathUpdate(self, world):
        """Return (dx, dy) result of update where enemy continues to follow its predecided path."""
        pathLs = self.currentPath.getPathList()  # sequence of steps to get to destination
        currentApproachedPnt = pathLs[self.distDownPath+1] # intersect 1 ahead of enemy in its predetermined path, ie. what it is approaching
        xl, yu, xr, yd = world.getIntersectBoundingBox(currentApproachedPnt) # get region of intersection enemy is approaching
        approachedCenterPnt = ((xl+xr)/2, (yu+yd)/2)  # actual point enemy is approaching in world
        dx, dy = (approachedCenterPnt[0]-self.xPos, approachedCenterPnt[1]-self.yPos)
        if dx == 0 and dy == 0:
            return 0, 0
        else:
            dx, dy = float(dx) / max([abs(dx),abs(dy)]), float(dy) / max([abs(dx), abs(dy)])
            return int(dx*self.speed), int(dy*self.speed)

    def changeAIState(self, world, player, flashlight, camPos):
        """Check if AI behaviour should now change, alter it appropriately if so."""
        distToPlayer = math.sqrt((self.xPos-player.xPos)**2 + (self.yPos-player.yPos)**2)
        if distToPlayer <= world.hallLength:
            if self.isInFlashlightRegion(flashlight, player, camPos) and self.currentAI != CHASING:
                self.currentAI = CHASING
            elif not self.isInFlashlightRegion(flashlight, player, camPos) and self.currentAI != CLOSE:
                self.currentAI = CLOSE
        elif distToPlayer <= player.getHeardRadius(world):
            if self.currentAI == CLOSE or self.currentAI == CHASING:
                self.currentAI = RETURNING
            elif self.currentAI == WANDERING:
                self.currentAI = FOLLOWING
                # is still following WANDERING path, reset path to closest intersect so new path can be made
                nextPos = world.getClosestIntersectPoint(self)
                self.currentPath.setPathBetween(nextPos, nextPos)
                self.distDownPath = 0

    def getAIDecision(self, world, player, flashlight, camPos):
        """Returns a pair of (dx, dy) for next update movement."""
        # check if AI behaviour should now change based on what is known currently
        self.changeAIState(world, player, flashlight, camPos)
        # make appropriate movement for current AI state
        if self.currentAI == WANDERING or self.currentAI == FOLLOWING:
            # Is following predetermined paths from intersection to intersection.
            self.speed = 5
            # If close enough to player, start following them. Otherwise, keep wandering.
            dx, dy = self.followPathUpdate(world)
            if dx==0 and dy==0:  # has reached destination bc. no further movement needed
                self.distDownPath += 1
                if self.distDownPath == self.currentPath.getPathLength()-1: # reset path randomly if completed
                    pntLs = world.getPntList()
                    self.distDownPath = 0
                    gridX = (self.xPos - world.hallWidth) / (world.hallWidth + world.hallLength) # get which intersect enemy is in from its real position
                    gridY = (self.yPos - world.hallWidth) / (world.hallWidth + world.hallLength)
                    pnt1 = (gridX, gridY)
                    pntLs.remove(pnt1)
                    # if has followed player to where it last heard them + player has left when enemy arrives, set self to WANDERING
                    # ie. lost track of where player is
                    distToPlayer = math.sqrt((self.xPos-player.xPos)**2 + (self.yPos-player.yPos)**2)
                    if distToPlayer > player.getHeardRadius(world) and self.currentAI != WANDERING:
                        self.currentAI = WANDERING
                    if self.currentAI == WANDERING:
                        pnt2 = random.choice(pntLs)
                        self.currentPath.setPathBetween(pnt1, pnt2)
                    elif self.currentAI == FOLLOWING:
                        playerCoords = world.getClosestIntersectPoint(player)
                        self.currentPath.setPathBetween(pnt1, playerCoords)
                dx, dy = self.followPathUpdate(world)  # reset goal point to next one in path
            return dx, dy
        elif self.currentAI == CLOSE or self.currentAI == CHASING:
            # Is moving directly towards player at speed = walking speed if close or > player speed if chasing (flashlight looking at enemy when chasing).
            self.speed = (player.speed*1.5) if self.currentAI == CHASING else 5
            diffX, diffY = (player.xPos - self.xPos, player.yPos - self.yPos)
            if diffX == 0 and diffY == 0:
                return 0, 0
            else:
                dx, dy = float(diffX) / max([abs(diffX), abs(diffY)]), float(diffY) / max([abs(diffX), abs(diffY)])
                return int(math.ceil(dx*self.speed)), int(math.ceil(dy*self.speed))
        elif self.currentAI == RETURNING:
            # Is returning from directly following player to closest intersection, then WANDERING.
            self.speed = 6
            closeInt = world.getClosestIntersectPoint(self)
            xl, yu, xr, yd = world.getIntersectBoundingBox(closeInt)
            approachedCenterPnt = ((xl+xr)/2, (yu+yd)/2)
            dx, dy = (approachedCenterPnt[0]-self.xPos, approachedCenterPnt[1]-self.yPos)
            if dx == 0 and dy == 0:
                self.currentAI = WANDERING
                return 0, 0
            elif -self.speed <= dx <= self.speed and -self.speed <= dy <= self.speed:
                # can't get exactly to return point bc. of rounding errors
                self.xPos, self.yPos = approachedCenterPnt
                self.currentAI = WANDERING
                return 0, 0
            else:
                dx, dy = float(dx) / max([abs(dx),abs(dy)]), float(dy) / max([abs(dx), abs(dy)])
                return int(dx*self.speed), int(dy*self.speed)

    def isInFlashlightRegion(self, flashlight, player, camPos):
        playerEnemyAng = getActualAng(self.xPos-player.xPos, self.yPos-player.yPos)
        xMouse, yMouse = pygame.mouse.get_pos()
        xMouse += camPos[0]; yMouse += camPos[1]
        mouseAng = getActualAng(xMouse - player.xPos, yMouse - player.yPos)
        lowerExtreme = mouseAng-(flashlight.angle/2.0)  # angle of lower-angled edge of flashlight's visible region
        if lowerExtreme<0: lowerExtreme += math.pi*2
        playerEnemyAng -= lowerExtreme  # rotate world as though flashlight region goes from angles 0 to flashlight.angle
        if playerEnemyAng<0: playerEnemyAng += math.pi*2
        return 0 <= playerEnemyAng <= flashlight.angle

    def drawTo(self, screen, flashlight, player, camPos):
        if self.isInFlashlightRegion(flashlight, player, camPos):
            pygame.draw.circle(screen, (0,0,0), (self.xPos - camPos[0], self.yPos - camPos[1]), 10, 0)



class Path(object):
    """A path object which can be reset to be a new path between points."""

    def __init__(self, world):
        self.worldGrid = world.grid
        self.pntLs = world.getPntList()
        self.currentPath = [self.pntLs[0], self.pntLs[0]]
        self.startPnt = self.pntLs[0]
        self.endPnt = self.pntLs[0]

    def setPathBetween(self, p1, p2):
        """Do breadth-first search of all intersects, following available paths until destination has been reached.
        Return whether or not path creation was successful."""
        self.startPnt = p1; self.endPnt = p2
        paths = [[self.startPnt]]
        coveredPnts = [self.startPnt]
        if self.startPnt == self.endPnt:
            self.currentPath = [self.startPnt, self.startPnt]
            return True
        elif self.startPnt not in self.pntLs or self.endPnt not in self.pntLs:
            return False
        else:
            while True:
                for path in paths:
                    # take last item in path being investigated, and extend it in all possible directions
                    pntToExpand = path[-1]
                    x, y = pntToExpand
                    newPnts = [p for p in self.worldGrid[y][x].keys() if self.worldGrid[y][x][p] and p not in coveredPnts]
                    if any([p == self.endPnt for p in newPnts]):
                        self.currentPath = path + [self.endPnt]
                        return True
                    elif len(newPnts) > 0:
                        newPaths = [path + [p] for p in newPnts]
                        paths.remove(path)
                        paths.extend(newPaths)
                        coveredPnts.extend(newPnts)

    def getPathList(self):
        return self.currentPath

    def getPathLength(self):
        return len(self.currentPath)
