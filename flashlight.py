import pygame, math
from world import World
from player import Player


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

    if r_mag == 0 or s_mag == 0: return None

    if r_dx/r_mag == s_dx/s_mag and r_dy/r_mag == s_dy/s_mag: return None

    if r_dx == 0 or r_dy == 0: return None

    # get parameter T2 for segment, 0<=T2<=1 if hits that segment of line
    T2 = (r_dx*(s_py-r_py) + r_dy*(r_px-s_px))/float(s_dx*r_dy - s_dy*r_dx)
    if not 0<=T2<=1: return None

    # get parameter T1 for ray, 0<=T1 if ray hits a segment
    T1 = (s_px+s_dx*T2-r_px)/float(r_dx)
    if not 0<=T1: return None

    return (r_px + r_dx*T1, r_py + r_dy*T1)  # (x, y)


def getActualAng(x, y):
    if x>0 and y>0: return math.atan2(y,x)
    elif x<0 and y>0: return math.atan2(-x, y) + 0.5*math.pi
    elif x<0 and y<0: return math.atan2(-y, -x) + math.pi
    elif x>0 and y<0: return 2*math.pi - math.atan2(-y, x)
    elif x==0: return math.pi*0.5 if y>0 else math.pi*(-0.5)
    elif y==0: return 0 if x>0 else math.pi


class Flashlight(object):

    def __init__(self, screen, angle):
        self.angle = angle
        self.xCam = 0; self.yCam = 0
        self.screen = screen

    def drawLight(self, world, player, camPos):
        """
        Shadow Drawing Algorithm:

        Get closest hall intersection to self, rest are far away offscreen, so ignore for performance.
        Get hallways linked to intersection + their bounding boxes + walls of intersect if no hallway there.
        Use bounding boxes to get intersect lines (longest walls of halls + hall-less walls of intersect).
        Draw 4 line segments around all 4 edges of screen.
        Cast ray to each line segment end + ray 0.1 to left + ray 0.1 to right.
        Get all intersects of rays + closest line segment, draw polygon by lines between intersects in clockwise manner.
        Draw white image w/ black polygon + subtract this from orig image, will now have shadows.
        Draw white image w/ black triangle for flashlight-illuminated region, subtract this from original image too, will now have img w/ flashlight effect.
        """

        self.xCam, self.yCam = camPos

        closestIntersect = self.getClosestIntersectPoint(world, player)
        segments = self.getCloseWallSegments(world, closestIntersect[0], closestIntersect[1])
        lightIntersects = self.getLightSegIntersects(segments, player)

        mask360NoFlashlight = self.get360LightMask(lightIntersects, player)
        maskFlashlightNoShadows = self.getFlashlightMaskNoShadows(player)

        # subtract 360 degree light emission mask and flashlight mask w/o shadows from own screen
        # from triangle mask, light grey region outside of triangle -> darkened version of screen pixel
        # white mask pixel -> black screen pixel, black mask pixel -> screen pixel stays same
        self.screen.blit(mask360NoFlashlight, (0,0), special_flags=pygame.BLEND_SUB)
        self.screen.blit(maskFlashlightNoShadows, (0,0), special_flags=pygame.BLEND_SUB)


    def getClosestIntersectPoint(self, world, player):
        intBoxes = [world.getIntersectBoundingBox(inter) for inter in world.getHallIntersectPoints()]

        xPlayer = player.xPos; yPlayer = player.yPos

        getBoxDistToSelf = lambda box: math.sqrt(((box[0]+box[2])/2.0 - xPlayer)**2 + ((box[1]+box[3])/2.0 - yPlayer)**2)
        closestBox = min(intBoxes, key=getBoxDistToSelf)
        xl, yu, xr, yd = closestBox
        xIntReal = int((xl - world.hallWidth) / (world.hallWidth + world.hallLength))
        yIntReal = int((yu - world.hallWidth) / (world.hallWidth + world.hallLength))

        return (xIntReal, yIntReal)


    def getCloseWallSegments(self, world, xIntersectReal, yIntersectReal):
        intDict = world.grid[yIntersectReal][xIntersectReal]
        segments = []  # list of all segments that light rays will hit + stop against

        # add box of segments around managed region to catch stray light rays + give them something to hit
        xl, yu, xr, yd = world.getIntersectBoundingBox((xIntersectReal, yIntersectReal))
        centerX, centerY = (xr+xl)/2, (yd+yu)/2
        regionW = regionH = world.hallWidth + 2*world.hallLength
        segments.extend([{"a": (centerX-regionW/2, centerY-regionH/2), "b": (centerX+regionW/2, centerY-regionH/2)},
                         {"a": (centerX+regionW/2, centerY-regionH/2), "b": (centerX+regionW/2, centerY+regionH/2)},
                         {"a": (centerX+regionW/2, centerY+regionH/2), "b": (centerX-regionW/2, centerY+regionH/2)},
                         {"a": (centerX-regionW/2, centerY+regionH/2), "b": (centerX-regionW/2, centerY-regionH/2)}])

        # get all line segments
        for p0, isConnected in intDict.items():
            if isConnected:
                hallway = (p0, (xIntersectReal, yIntersectReal))
                xl_h, yu_h, xr_h, yd_h = world.getHallBoundingBox(hallway[0], hallway[1])
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
                if p0[0] < xIntersectReal: segments.append({"a": (xl, yu), "b": (xl, yd)})     # hall to left missing
                elif p0[0] > xIntersectReal: segments.append({"a": (xr, yu), "b": (xr, yd)})   # hall to right missing
                elif p0[1] < yIntersectReal: segments.append({"a": (xl, yu), "b": (xr, yu)})   # hall above missing
                elif p0[1] > yIntersectReal: segments.append({"a": (xl, yd), "b": (xr, yd)})   # hall below missing

        return segments


    def getRayReceivingPoints(self, segments):
        pnts = []

        # list of points to send light rays to
        for segment in segments:
            #xA, yA = segment["a"]; xB, yB = segment["b"]
            #pygame.draw.line(self.screen, (255, 0, 255), (xA-self.xCam, yA-self.yCam), (xB-self.xCam, yB-self.yCam))
            #pygame.draw.rect(self.screen, (0, 0, 255), pygame.Rect(xA-self.xCam-5, yA-self.yCam-5, 10, 10))
            #pygame.draw.rect(self.screen, (0, 0, 255), pygame.Rect(xB-self.xCam-5, yB-self.yCam-5, 10, 10))
            pnts.extend([segment["a"], segment["b"]])

        return pnts


    def getLightSegIntersects(self, segments, player):
        finalInts = []
        pntLs = self.getRayReceivingPoints(segments)
        xPlayer = player.xPos; yPlayer = player.yPos
        for p in pntLs:
            rays = [{"a": (xPlayer, yPlayer), "b": p},
                    {"a": (xPlayer, yPlayer), "b": (p[0]+0.1, p[1])},
                    {"a": (xPlayer, yPlayer), "b": (p[0]-0.1, p[1])}]
            for ray in rays:
                intersects = []
                for seg in segments:
                    intersect = getIntersect(ray, seg)
                    if intersect == None: continue
                    intersects.append(intersect)
                if len(intersects) == 0: continue
                minIntersect = min(intersects, key=lambda i: math.sqrt((i[0]-xPlayer)**2 + (i[1]-yPlayer)**2))
                finalInts.append(minIntersect)

        #for intersect in finalInts:
        #    screenW, screenH = self.screen.get_size()
        #    pygame.draw.line(self.screen, (255, 0, 255), (screenW/2, screenH/2), (intersect[0]-self.xCam, intersect[1]-self.yCam))
        #    pygame.draw.rect(self.screen, (255, 0, 255), pygame.Rect(intersect[0]-self.xCam-5, intersect[1]-self.yCam-5, 10, 10))

        return finalInts


    def get360LightMask(self, lightIntLs, player):
        xPlayer = player.xPos; yPlayer = player.yPos
        # sort out angles
        sortedInts = sorted(lightIntLs, key = lambda p: getActualAng(p[0]-xPlayer, p[1]-yPlayer))

        # temporary surface = white w/ black polygon of visible regions
        tempSurface = pygame.Surface(self.screen.get_size())
        pygame.draw.rect(tempSurface, (255 , 255, 255), pygame.Rect(0, 0, tempSurface.get_size()[0], tempSurface.get_size()[1]))
        pygame.draw.polygon(tempSurface, (0, 0, 0), [(x-self.xCam, y-self.yCam) for x,y in sortedInts])

        return tempSurface


    def getFlashlightMaskNoShadows(self, player):
        # get region of flashlight-produced light triangle
        xMouse, yMouse = pygame.mouse.get_pos()
        xMouse += self.xCam; yMouse += self.yCam
        mouseAng = getActualAng(xMouse - player.xPos, yMouse - player.yPos)
        screenWidth, screenHeight = self.screen.get_size()
        mousePnt1 = (player.xPos + 2*screenWidth*math.cos(mouseAng-self.angle/2.0), player.yPos + 2*screenHeight*math.sin(mouseAng-self.angle/2.0))
        mousePnt2 = (player.xPos + 2*screenWidth*math.cos(mouseAng+self.angle/2.0), player.yPos + 2*screenHeight*math.sin(mouseAng+self.angle/2.0))

        # triangle surface = grey w/ black triangle of what flashlight reveals
        triangSurface = pygame.Surface(self.screen.get_size())
        pygame.draw.rect(triangSurface, (110 , 110, 110), pygame.Rect(0, 0, triangSurface.get_size()[0], triangSurface.get_size()[1]))
        triangLs = [(player.xPos, player.yPos), mousePnt1, mousePnt2]
        pygame.draw.polygon(triangSurface, (0, 0, 0), [(x-self.xCam, y-self.yCam) for x,y in triangLs])

        return triangSurface
