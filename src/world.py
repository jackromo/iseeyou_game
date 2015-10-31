import pygame
import copy
import random
import math
import time

class World(object):
    """World object for horror game. A series of random sprawling hallways in all directions."""

    def __init__(self, width, height, screen):
        assert(type(width) is int)
        assert(type(height) is int)
        self.width = width
        self.height = height
        self.screen = screen
        self.grid = [[{ (x-1, y): False,
                        (x, y-1): False,
                        (x+1, y): False,
                        (x, y+1): False} for x in range(width)] for y in range(height)]
        self.hallWidth = 300
        self.hallLength = 1200
        self.startX = 0; self.startY = 0
        self.floorColor = (127, 127, 127)
        self.exitArea = None  # hall intersect containing exit point

    def resetWorld(self):
        self.grid = [[{ (x-1, y): False,
                        (x, y-1): False,
                        (x+1, y): False,
                        (x, y+1): False} for x in range(self.width)] for y in range(self.height)]

    def getSidePnts(self, x, y):
        """Get all intersect points adjacent to a point. Ignore points outside of grid boundaries."""
        sidePnts = []
        if x > 0:                   sidePnts.append((x-1, y))
        if x < len(self.grid[0])-1: sidePnts.append((x+1, y))
        if y > 0:                   sidePnts.append((x, y-1))
        if y < len(self.grid)-1:    sidePnts.append((x, y+1))
        return sidePnts

    def genWorld(self, startX = 10, startY = 10):
        """Initializes grid of hallways in world. Starts at a point and expands out to random points adjacent to it."""
        assert(type(startX) is int)
        assert(type(startY) is int)
        self.startX = startX; self.startY = startY
        connectedNodes = []  # nodes which have been expanded
        activeNodes = [(startX, startY)]  # nodes which have yet to be expanded
        while len(connectedNodes) < self.width*self.height*0.4 and len(activeNodes)>0:  # while less than 40% of world is accessible
            for x, y in activeNodes:
                sidePnts = self.getSidePnts(x, y)
                gridNewVal = {p: False for p in self.grid[y][x].keys()}
                # if adjacent node connected to self, then self connected to adj node too
                for p in sidePnts:
                    if self.grid[p[1]][p[0]][(x,y)] is True:
                        gridNewVal[p] = True
                # assign more random connections other than ones already touched
                nTruesNow = len([i for i in gridNewVal.values() if i==True])  # how many connections already made before adding new ones
                nTruesNeeded = 4 if nTruesNow==4 else random.randrange(nTruesNow+1, 5)  # random value for how many points self will extend to
                # assign new True's to random adjacent nodes to self
                for p in sorted(sidePnts, key=lambda x: random.random()):
                    if self.grid[p[1]][p[0]][(x,y)] is False and nTruesNow < nTruesNeeded:
                        gridNewVal[p] = True; nTruesNow += 1
                self.grid[y][x] = gridNewVal
                connectedNodes.append((x,y)) # node is now connected to system
                activeNodes.remove((x,y)) # node has been expanded, no longer active
                sidePnts = [p for p in sidePnts if gridNewVal[p]]
                activeNodes.extend([p for p in sidePnts if p not in activeNodes and p not in connectedNodes])
        self.correctStrayIntersects()
        # choose exit area to be somewhere at least 5x5 hallways away from player
        exitAreaPossibilities = [p for p in self.getPntList() if abs(p[0]-startX)>=3 and abs(p[1]-startY)>=3]
        self.exitArea = random.choice(self.getPntList() if len(exitAreaPossibilities)==0 \
                                      else exitAreaPossibilities)

    def getPntList(self):
        return [(x, y) for y, row in enumerate(self.grid) \
                       for x, pntDict in enumerate(row) if any(pntDict.values())]

    def correctStrayIntersects(self):
        """After setting all values, some hallways may be disconnected, so connect all dissonant hallways."""
        for y, row in enumerate(self.grid):
            for x, valDict in enumerate(row):
                sidePnts = self.getSidePnts(x, y)
                # if adjacent node connected to self, then self connected to adj node too
                for p in sidePnts:
                    if self.grid[p[1]][p[0]][(x,y)] is True:
                        self.grid[y][x][p] = True

    def getHallways(self):
        """Returns a list of 2-tuples, each of which contains the two sets of XY coords at the start and end of a hallway."""
        return [((x1, y1), p2) for y1, col in enumerate(self.grid) \
                               for x1, pntDict in enumerate(col) \
                               for p2, isConnected in pntDict.items() if isConnected]

    def getHallIntersectPoints(self):
        """Returns a list of all coordinates that are connected to a hallway."""
        return [(x, y) for y, col in enumerate(self.grid) \
                       for x, pntDict in enumerate(col) if any(pntDict.values())]

    def getHallBoundingBox(self, p0, p1):
        # starting x pnt of line = one intercept + many intercept-hallLength pairs + another intercept if line goes to right
        xStart = self.hallWidth + p0[0]*(self.hallWidth + self.hallLength) + (self.hallWidth if p1[0]-p0[0]==1 else 0)
        # starting y pnt of line = one intercept + many intercept-hallLength pairs + another intercept if line goes down
        yStart = self.hallWidth + p0[1]*(self.hallWidth + self.hallLength) + (self.hallWidth if p1[1]-p0[1]==1 else 0)
        xEnd = xStart + (self.hallWidth if p1[0]-p0[0]==0 else self.hallLength*(p1[0]-p0[0]))
        yEnd = yStart + (self.hallWidth if p1[1]-p0[1]==0 else self.hallLength*(p1[1]-p0[1]))
        return (min([xStart, xEnd]), min([yStart, yEnd]), max([xStart, xEnd]), max([yStart, yEnd]))

    def getIntersectBoundingBox(self, p):
        xLeft = p[0]*(self.hallWidth + self.hallLength) + self.hallWidth
        yUp = p[1]*(self.hallWidth + self.hallLength) + self.hallWidth
        return (xLeft, yUp, xLeft+self.hallWidth, yUp+self.hallWidth)

    def isInWorld(self, x, y):
        hallBoxes = [self.getHallBoundingBox(p0, p1) for p0, p1 in self.getHallways()]
        isInHall = any([xMin <= x <= xMax and yMin <= y <= yMax for xMin,yMin,xMax,yMax in hallBoxes])
        intBoxes = [self.getIntersectBoundingBox(p) for p in self.getHallIntersectPoints()]
        isInInt = any([xMin <= x <= xMax and yMin <= y <= yMax for xMin,yMin,xMax,yMax in intBoxes])
        return isInHall or isInInt

    def getStartPoint(self):
        x, y, _, _ = self.getIntersectBoundingBox((self.startX, self.startY))
        return (x+ (self.hallWidth/2), y + (self.hallWidth/2))

    def getClosestIntersectPoint(self, player):
        intBoxes = [self.getIntersectBoundingBox(inter) for inter in self.getHallIntersectPoints()]
        xPlayer = player.xPos; yPlayer = player.yPos
        getBoxDistToSelf = lambda box: math.sqrt(((box[0]+box[2])/2.0 - xPlayer)**2 + ((box[1]+box[3])/2.0 - yPlayer)**2)
        closestBox = min(intBoxes, key=getBoxDistToSelf)
        xl, yu, xr, yd = closestBox
        xIntReal = int((xl - self.hallWidth) / (self.hallWidth + self.hallLength))
        yIntReal = int((yu - self.hallWidth) / (self.hallWidth + self.hallLength))
        return (xIntReal, yIntReal)

    def hasReachedExit(self, player):
        xl, yu, xr, yd = self.getIntersectBoundingBox(self.exitArea)
        centerPnt = ((xl+xr)/2, (yu+yd)/2)
        dist = math.sqrt((centerPnt[0]-player.xPos)**2 + (centerPnt[1]-player.yPos)**2)
        return dist <= 50

    def drawWorld(self, xCam, yCam, player):
        """Draws world to screen with camera offset of (xCam, yCam)."""
        w, h = self.screen.get_size()
        pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(0, 0, w, h))  # black background
        intersect = self.getClosestIntersectPoint(player)
        hallways = [(sidePnts, intersect) for sidePnts in self.getSidePnts(*intersect)]
        for p0, p1 in hallways:
            # starting x pnt of line = one intercept + many intercept-hallLength pairs + another intercept if line goes to right
            xStart = self.hallWidth + p0[0]*(self.hallWidth + self.hallLength) + (self.hallWidth if p1[0]-p0[0]==1 else 0)
            # starting y pnt of line = one intercept + many intercept-hallLength pairs + another intercept if line goes down
            yStart = self.hallWidth + p0[1]*(self.hallWidth + self.hallLength) + (self.hallWidth if p1[1]-p0[1]==1 else 0)
            xWidth = self.hallWidth if p1[0]-p0[0]==0 else self.hallLength*(p1[0]-p0[0])
            yHeight = self.hallWidth if p1[1]-p0[1]==0 else self.hallLength*(p1[1]-p0[1])
            rect = pygame.Rect(xStart-xCam, yStart-yCam, xWidth, yHeight)
            pygame.draw.rect(self.screen, self.floorColor, rect)
        # draw closest intersect
        xLeft = intersect[0]*(self.hallWidth + self.hallLength) + self.hallWidth
        yUp = intersect[1]*(self.hallWidth + self.hallLength) + self.hallWidth
        rect = pygame.Rect(xLeft-xCam, yUp-yCam, self.hallWidth, self.hallWidth)
        if intersect == self.exitArea:
            pygame.draw.rect(self.screen, self.floorColor, rect)
            rect2 = pygame.Rect(xLeft-xCam+50, yUp-yCam+50, self.hallWidth-(2*50), self.hallWidth-(2*50))
            pygame.draw.rect(self.screen, (63, 63, 63), rect2)
            rect3 = pygame.Rect(xLeft-xCam+100, yUp-yCam+100, self.hallWidth-(2*100), self.hallWidth-(2*100))
            pygame.draw.rect(self.screen, (0, 0, 0), rect3)
        else:
            pygame.draw.rect(self.screen, self.floorColor, rect)
