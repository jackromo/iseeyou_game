import pygame, random, math, copy
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
        self.currentPath = Path(world.grid)
        gridX = (self.xPos - world.hallWidth) / (world.hallWidth + world.hallLength)
        gridY = (self.yPos - world.hallWidth) / (world.hallWidth + world.hallLength)
        self.currentPath.setPathBetween((gridX, gridY), (gridX, gridY))
        self.distDownPath = 0
        self.currentAI = FOLLOWING

    def update(self, state, world, player):
        self.dx = 0; self.dy = 0
        self.dx, self.dy = self.getAIDecision(world, player)

        # collision detection
        if not world.isInWorld(self.xPos + 2*self.dx, self.yPos): self.dx = 0
        if not world.isInWorld(self.xPos, self.yPos + 2*self.dy): self.dy = 0
        if self.dx!=0 and self.dy!=0 and not world.isInWorld(self.xPos+ 2*self.dx, self.yPos+ 2*self.dy):  # may be hitting edge of a corner
            self.dx = 0; self.dy = 0
        self.xPos += self.dx
        self.yPos += self.dy

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
            return int(dx)*self.speed, int(dy)*self.speed

    def getAIDecision(self, world, player):
        """Returns a pair of (dx, dy) for next update movement."""
        if self.currentAI == WANDERING or self.currentAI == FOLLOWING:
            # Is following predetermined paths from intersection to intersection.
            dx, dy = self.followPathUpdate(world)
            if dx==0 and dy==0:  # has reached destination bc. no further movement needed
                self.distDownPath += 1
                if self.distDownPath == self.currentPath.getPathLength()-1: # reset path randomly if completed
                    pntLs = [(x, y) for y, row in enumerate(world.grid) \
                                    for x, pntDict in enumerate(row) if any(pntDict.values())]
                    self.distDownPath = 0
                    gridX = (self.xPos - world.hallWidth) / (world.hallWidth + world.hallLength) # get which intersect enemy is in from its real position
                    gridY = (self.yPos - world.hallWidth) / (world.hallWidth + world.hallLength)
                    pnt1 = (gridX, gridY)
                    pntLs.remove(pnt1)
                    if self.currentAI == WANDERING:
                        pnt2 = random.choice(pntLs)
                        self.currentPath.setPathBetween(pnt1, pnt2)
                    elif self.currentAI == FOLLOWING:
                        playerCoords = world.getClosestIntersectPoint(player)
                        self.currentPath.setPathBetween(pnt1, playerCoords)
                dx, dy = self.followPathUpdate(world)  # reset goal point to next one in path
            return dx, dy
        elif self.currentAI == CLOSE:
            # Is moving directly towards player at speed < player speed.
            pass
        elif self.currentAI == CHASING:
            # Is moving directly towards player very fast - flashlight aimed at enemy.
            pass
        elif self.currentAI == RETURNING:
            # Is returning from directly following player to closest intersection, then WANDERING.
            pass

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
            pygame.draw.rect(screen, (0,0,255), pygame.Rect(self.xPos - camPos[0], self.yPos - camPos[1], 10, 10))



class Path(object):
    """A path object which can be reset to be a new path between points."""

    def __init__(self, worldGrid):
        self.worldGrid = worldGrid
        self.pntLs = [(x, y) for y, row in enumerate(worldGrid) \
                             for x, pntDict in enumerate(row) if any(pntDict.values())]
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
