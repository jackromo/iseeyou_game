import pygame
from world import World
from player import Player
from enemy import Enemy


class GameSession(object):
    """A sessionn of playing the game."""

    def __init__(self, screen):
        self.world = World(10, 10)
        self.world.genWorld(5, 5)
        self.player = Player()
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
        pass
        #player.update(self.keys)
        #enemy.update()

    def render(self):
        self.world.drawWorld(self.screen, self.xCam, self.yCam)
        #self.player.drawTo(self.screen)
        #self.enemy.drawTo(self.screen)


def main():
    pygame.init()
    screen = pygame.display.set_mode((1000,1000))
    session = GameSession(screen)
    session.start()

if __name__ == "__main__":
    main()
