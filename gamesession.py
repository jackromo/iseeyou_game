import pygame, math, time, random
from world import World
from player import Player
from enemy import Enemy
from flashlight import Flashlight


class GameSession(object):
    """A session of playing the game."""

    def __init__(self, screen):
        self.screen = screen
        self.world = World(10, 10)
        self.newGame()

    def newGame(self):
        pygame.mixer.stop()
        self.world.resetWorld()
        self.world.genWorld(5, 5)
        self.player = Player(*self.world.getStartPoint())
        # get enemy's random position
        pntLs = self.world.getPntList()
        # put enemy somewhere > 5 hallways away from player to start with
        enemyStartPositions = [p for p in pntLs if abs(p[0]-self.player.xPos)>5 and abs(p[1]-self.player.yPos)>5]
        pnt = random.choice(pntLs if len(enemyStartPositions)==0 else enemyStartPositions)
        xl, yu, xr, yd = self.world.getIntersectBoundingBox(pnt)
        px, py = ((xl+xr)/2, (yu+yd)/2)
        self.enemy = Enemy(px, py, self.world)
        self.flashlight = Flashlight(self.screen, 1)  # flashlight w/ range of 1 radian
        self.keys = None
        self.xCam = 0
        self.yCam = 0

    def startGame(self):
        """Start session of playing game."""
        beatLevel = True
        currentLevel = 0
        while beatLevel:
            beatLevel = self.startLevel()
            if beatLevel: currentLevel += 1
        return currentLevel

    def startLevel(self):
        """Start play of a level. Returns True if player got to end, False if killed by enemy or player quit."""
        self.newGame()
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
            if (-10 < self.enemy.xPos-self.player.xPos < 10) and (-10 < self.enemy.yPos-self.player.yPos < 10):
                # enemy got to player, player = killed
                return False
            elif self.world.hasReachedExit(self.player):
                # player reached exit
                return True
            pygame.display.flip()
            pygame.event.pump()
        return False  # player hit 'q' to quit game

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
