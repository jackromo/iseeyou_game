import pygame, math
from world import World
from player import Player
from enemy import Enemy


def getIntersect(ray, segment):

    # ray in parametric form: r_p + r_d*T1
    r_px = ray["a"][0]
    r_py = ray["a"][1]
    r_dx = ray["b"][0] - ray["a"][0]
    r_dy = ray["b"][1] - ray["a"][1]

    # segment in parametric form: s_p + s_d*T2
    s_px = segment["a"][0]
    s_py = segment["a"][1]
    s_dx = segment["b"][0] - segment["a"][0]
    s_dy = segment["b"][1] - segment["a"][1]

    # check if parallel
    r_mag = math.sqrt(r_dx*r_dx + r_dy*r_dy)
    s_mag = math.sqrt(s_dx*s_dx + s_dy*s_dy)

    if r_mag == 0 or s_mag == 0:
        return None

    if r_dx/r_mag == s_dx/s_mag and r_dy/r_mag == s_dy/s_mag:
        return None

    if r_dx == 0 or r_dy == 0:
        return None

    # get parameter T2 for segment, 0<=T2<=1 if hits that segment of line
    T2 = (r_dx*(s_py-r_py) + r_dy*(r_px-s_px))/float(s_dx*r_dy - s_dy*r_dx)
    if not 0<=T2<=1:
        return None

    # get parameter T1 for ray, 0<=T1 if ray hits a segment
    T1 = (s_px+s_dx*T2-r_px)/float(r_dx)
    if not 0<=T1:
        return None

    return (r_px + r_dx*T1, r_py + r_dy*T1)  # (x, y)

def getActualAng(x, y):
    if x>0 and y>0: return math.atan2(y,x)
    elif x<0 and y>0: return math.atan2(-x, y) + 0.5*math.pi
    elif x<0 and y<0: return math.atan2(-y, -x) + math.pi
    elif x>0 and y<0: return 2*math.pi - math.atan2(-y, x)
    elif x==0: return math.pi*0.5 if y>0 else math.pi*(-0.5)
    elif y==0: return 0 if x>0 else math.pi


class GameSession(object):
    """A session of playing the game."""

    def __init__(self, screen):
        self.world = World(10, 10)
        self.world.genWorld(5, 5)
        self.player = Player(*self.world.getStartPoint())
        self.enemy = Enemy()
        self.screen = screen
        self.keys = None
        self.xCam = 0
        self.yCam = 0

    def start(self):
        self.keys = pygame.key.get_pressed()
        while not self.keys[pygame.K_q]:
            self.keys = pygame.key.get_pressed()
            self.update()
            self.render()
            pygame.display.flip()
            pygame.event.pump()

    def update(self):
        self.player.update(self.keys, self.world)
        x, y = self.screen.get_size()
        self.xCam = self.player.xPos - x/2
        self.yCam = self.player.yPos - y/2
        #enemy.update()

    def render(self):
        self.world.drawWorld(self.screen, self.xCam, self.yCam)
        self.player.drawTo(self.screen)

        # Shadow Drawing Algorithm:
        #
        # get closest hall intersection to self, rest are far away offscreen, so ignore for performance
        # get hallways linked to intersection + their bounding boxes + walls of intersect if no hallway there
        # use bounding boxes to get intersect lines (longest walls of halls + hall-less walls of intersect)
        # draw 4 line segments around all 4 edges of screen
        # cast ray to each line segment end + ray 0.0001 to left + ray 0.0001 to right
        # get all intersects of rays + closest line segment, draw polygon by lines between intersects in clockwise manner
        # draw white image w/ black polygon + subtract this from orig image, will now have shadows

        intBoxes = [self.world.getIntersectBoundingBox(inter) for inter in self.world.getHallIntersectPoints()]

        x = self.player.xPos; y = self.player.yPos
        getBoxDistToSelf = lambda box: math.sqrt(((box[0]+box[2])/2.0 - x)**2 + ((box[1]+box[3])/2.0 - y)**2)
        closestBox = min(intBoxes, key=getBoxDistToSelf)
        xl, yu, xr, yd = closestBox
        xIntReal = int((closestBox[0] - self.world.hallWidth) / (self.world.hallWidth + self.world.hallLength))
        yIntReal = int((closestBox[1] - self.world.hallWidth) / (self.world.hallWidth + self.world.hallLength))
        intDict = self.world.grid[yIntReal][xIntReal]
        w, h = self.screen.get_size()
        segments = []
        for p0, isConnected in intDict.items():
            if isConnected:
                hallway = (p0, (xIntReal, yIntReal))
                xl_h, yu_h, xr_h, yd_h = self.world.getHallBoundingBox(hallway[0], hallway[1])
                # get segments now
                xDiff = hallway[0][0] - hallway[1][0]
                yDiff = hallway[0][1] - hallway[1][1]
                if yDiff == 0:  # if vertical hall, walls = left and right sides
                    segments.append({"a": (xl_h, yu_h), "b": (xr_h, yu_h)})
                    segments.append({"a": (xl_h, yd_h), "b": (xr_h, yd_h)})
                elif xDiff == 0:  # if horizontal hall, walls = upper and lower sides
                    segments.append({"a": (xl_h, yu_h), "b": (xl_h, yd_h)})
                    segments.append({"a": (xr_h, yu_h), "b": (xr_h, yd_h)})
            else:
                # append segment of wall on intersect itself bc. no wall ahead
                if p0[0] < xIntReal: segments.append({"a": (xl, yu), "b": (xl, yd)})     # hall to left missing
                elif p0[0] > xIntReal: segments.append({"a": (xr, yu), "b": (xr, yd)})   # hall to right missing
                elif p0[1] < yIntReal: segments.append({"a": (xl, yu), "b": (xr, yu)})   # hall above missing
                elif p0[1] > yIntReal: segments.append({"a": (xl, yd), "b": (xr, yd)})   # hall below missing

        pnts = []
        finalInts = []

        for segment in segments:
            xA, yA = segment["a"]; xB, yB = segment["b"]
        #    pygame.draw.line(self.screen, (255, 0, 255), (xA-self.xCam, yA-self.yCam), (xB-self.xCam, yB-self.yCam))
        #    pygame.draw.rect(self.screen, (0, 0, 255), pygame.Rect(xA-self.xCam-5, yA-self.yCam-5, 10, 10))
        #    pygame.draw.rect(self.screen, (0, 0, 255), pygame.Rect(xB-self.xCam-5, yB-self.yCam-5, 10, 10))
            pnts.extend([(xA, yA), (xB, yB)])

        for p in pnts:
            rays = [{"a": (x, y), "b": (p[0], p[1])},
                    {"a": (x, y), "b": (p[0]+0.1, p[1])},
                    {"a": (x, y), "b": (p[0]-0.1, p[1])}]
            for ray in rays:
                intersects = []
                for seg in segments:
                    intersect = getIntersect(ray, seg)
                    if intersect == None: continue
                    intersects.append(intersect)
                if len(intersects) == 0: continue
                minIntersect = min(intersects, key=lambda i: math.sqrt((i[0]-x)**2 + (i[1]-y)**2))
                finalInts.append(minIntersect)

        #for intersect in finalInts:
        #    pygame.draw.line(self.screen, (255, 0, 255), (500, 500), (intersect[0]-self.xCam, intersect[1]-self.yCam))
        #    pygame.draw.rect(self.screen, (255, 0, 255), pygame.Rect(intersect[0]-self.xCam-5, intersect[1]-self.yCam-5, 10, 10))

        # sort out angles
        sortedInts = sorted(finalInts, key = lambda p: getActualAng(p[0]-x, p[1]-y))
        # temporary surface = white w/ black polygon of visible regions
        tempSurface = pygame.Surface(self.screen.get_size())
        pygame.draw.rect(tempSurface, (255 , 255, 255), pygame.Rect(0, 0, tempSurface.get_size()[0], tempSurface.get_size()[1]))
        pygame.draw.polygon(tempSurface, (0, 0, 0), [(xp-self.xCam, yp-self.yCam) for xp,yp in sortedInts])
        # subtract tempSurface from own screen, white tempSurf pixel -> black screen pixel, black tempSurf pixel -> screen pixel stays same
        self.screen.blit(tempSurface, (0,0), special_flags=pygame.BLEND_SUB)

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000,1000))
    session = GameSession(screen)
    session.start()

if __name__ == "__main__":
    main()
