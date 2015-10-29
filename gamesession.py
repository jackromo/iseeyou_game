import pygame, math, time, random
from world import World
from player import Player
from enemy import Enemy
from flashlight import Flashlight


class GameSession(object):
    """A session of playing the game."""

    def __init__(self, screen):
        self.world = World(10, 10)
        self.world.genWorld(5, 5)
        self.player = Player(*self.world.getStartPoint())
        # get enemy's random position
        pntLs = self.world.getPntList()
        pntLs.remove(self.world.getClosestIntersectPoint(self.player))
        pnt = random.choice(pntLs)
        xl, yu, xr, yd = self.world.getIntersectBoundingBox(pnt)
        px, py = ((xl+xr)/2, (yu+yd)/2)
        self.enemy = Enemy(px, py, self.world)
        self.flashlight = Flashlight(screen, 1)  # flashlight w/ range of 1 radian
        self.screen = screen
        self.keys = None
        self.xCam = 0
        self.yCam = 0

    def start(self):
        self.keys = pygame.key.get_pressed()
        wasESCPressed = False  # was ESC pressed last turn
        paused = False
        while not self.keys[pygame.K_q]:
            self.keys = pygame.key.get_pressed()
            if not self.keys[pygame.K_ESCAPE] and wasESCPressed:  # invert whether paused or not if escape pressed + released
                paused = not paused
                if paused: pygame.mixer.pause()
                else:      pygame.mixer.unpause()
            if paused:
                self.renderPause()
            else:
                self.update()
                self.render()
            wasESCPressed = self.keys[pygame.K_ESCAPE]
            pygame.display.flip()
            pygame.event.pump()

    def update(self):
        self.player.update(self.keys, self.world)
        self.enemy.update(self.world, self.player, self.flashlight, (self.xCam, self.yCam))
        x, y = self.screen.get_size()
        self.xCam = self.player.xPos - x/2
        self.yCam = self.player.yPos - y/2

    def render(self):
        self.world.drawWorld(self.screen, self.xCam, self.yCam)
        self.player.drawTo(self.screen)
        self.enemy.drawTo(self.screen, self.flashlight, self.player, (self.xCam, self.yCam))
        self.flashlight.drawLight(self.world, self.player, (self.xCam, self.yCam))

    def renderPause(self):
        font = pygame.font.SysFont("comicsans", 50)
        text = font.render("Paused", 1, (255, 255, 255))
        self.screen.blit(text, (0, 0))


def main():
    pygame.init()
    screen = pygame.display.set_mode((1000,1000))
    session = GameSession(screen)
    session.start()

if __name__ == "__main__":
    main()
