import pygame
import copy
import random
import time

class World(object):
    """World object for horror game. A series of random sprawling hallways in all directions."""


    def __init__(self, width=20, height=20):
        assert(type(width) is int)
        assert(type(height) is int)
        self.width = width
        self.height = height
        self.grid = [[{ (x-1, y): False,
                        (x, y-1): False,
                        (x+1, y): False,
                        (x, y+1): False} for x in range(width)] for y in range(height)]
        self.hallWidth = 200
        self.hallLength = 800
        self.startX = 0; self.startY = 0
        self.floorColor = (127, 127, 127)

    def resetWorld(self):
        self.grid = [[{ (x-1, y): False,
                        (x, y-1): False,
                        (x+1, y): False,
                        (x, y+1): False} for x in range(width)] for y in range(height)]

    def genWorld(self, startX = 10, startY = 10):
        """Initializes grid of hallways in world. Starts at a point and expands out to random points adjacent to it."""
        assert(type(startX) is int)
        assert(type(startY) is int)
        self.startX = startX; self.startY = startY
        connectedNodes = []  # nodes which have been expanded
        activeNodes = [(startX, startY)]  # nodes which have yet to be expanded
        while len(connectedNodes) < self.width*self.height*0.4 and len(activeNodes)>0:  # while less than 40% of world is accessible
            for x, y in activeNodes:
                sidePnts = []
                if x > 0:                   sidePnts.append((x-1, y))
                if x < len(self.grid[0])-1: sidePnts.append((x+1, y))
                if y > 0:                   sidePnts.append((x, y-1))
                if y < len(self.grid)-1:    sidePnts.append((x, y+1))
                gridNewVal = {p: False for p in sidePnts}
                # if adjacent node connected to self, then self connected to adj node too
                for p in sidePnts:
                    if self.grid[p[1]][p[0]][(x,y)] is True:
                        gridNewVal[p] = True
                # assign more random connections other than ones already touched
                nTruesNow = len([i for i in gridNewVal.values() if i==True])  # how many connections already made before adding new ones
                nTruesNeeded = 4 if nTruesNow==4 else random.randrange(nTruesNow+1, 5)  # random value for how many points self will extend to
                sidePntsTemp = copy.deepcopy(sidePnts); random.shuffle(sidePntsTemp)
                for p in sidePntsTemp:  # assign new True's to random adjacent nodes to self
                    if self.grid[p[1]][p[0]][(x,y)] is False and nTruesNow < nTruesNeeded:
                        gridNewVal[p] = True; nTruesNow += 1
                self.grid[y][x] = gridNewVal
                connectedNodes.append((x,y)) # node is now connected to system
                activeNodes.remove((x,y)) # node has been expanded, no longer active
                sidePnts = [p for p in sidePnts if gridNewVal[p]]
                activeNodes.extend([p for p in sidePnts if p not in activeNodes and p not in connectedNodes])

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
        #print isInInt, isInHall
        return isInHall or isInInt

    def drawWorld(self, screen, xCam, yCam):
        """Draws world to screen with camera offset of (xCam, yCam)."""
        worldWidth = self.width*self.hallWidth + (self.width-1)*self.hallLength
        worldHeight = self.height*self.hallWidth + (self.height-1)*self.hallLength
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(0, 0, worldWidth, worldHeight))  # black background
        hallways = self.getHallways()
        intersects = self.getHallIntersectPoints()
        for p0, p1 in hallways:
            # starting x pnt of line = one intercept + many intercept-hallLength pairs + another intercept if line goes to right
            xStart = self.hallWidth + p0[0]*(self.hallWidth + self.hallLength) + (self.hallWidth if p1[0]-p0[0]==1 else 0)
            # starting y pnt of line = one intercept + many intercept-hallLength pairs + another intercept if line goes down
            yStart = self.hallWidth + p0[1]*(self.hallWidth + self.hallLength) + (self.hallWidth if p1[1]-p0[1]==1 else 0)
            xWidth = self.hallWidth if p1[0]-p0[0]==0 else self.hallLength*(p1[0]-p0[0])
            yHeight = self.hallWidth if p1[1]-p0[1]==0 else self.hallLength*(p1[1]-p0[1])
            rect = pygame.Rect(xStart-xCam, yStart-yCam, xWidth, yHeight)
            pygame.draw.rect(screen, self.floorColor, rect)
        for p in intersects:
            xLeft = p[0]*(self.hallWidth + self.hallLength) + self.hallWidth
            yUp = p[1]*(self.hallWidth + self.hallLength) + self.hallWidth
            rect = pygame.Rect(xLeft-xCam, yUp-yCam, self.hallWidth, self.hallWidth)
            pygame.draw.rect(screen, self.floorColor, rect)



if __name__ == "__main__":
    # makes random world, scrolls diagonally down it, prints if exits or re-enters bounds of world
    world = World(10, 10)
    world.genWorld(5, 5)
    pygame.init()
    screen = pygame.display.set_mode((1000, 1000))
    v = 0; inWorld = False
    while v<2000:
        world.drawWorld(screen, v, v)
        v+=1
        time.sleep(0.01)
        iPrev = inWorld; inWorld = world.isInWorld(v+500, v+500)
        if iPrev and not inWorld:   print "exited world"
        elif not iPrev and inWorld: print "re-entered world"
        pygame.draw.rect(screen, (255,0,0), pygame.Rect(498, 498, 4, 4))
        pygame.display.flip()
