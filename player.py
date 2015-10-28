import pygame
from world import World


class Player(object):

    def __init__(self, xPos, yPos):
        self.xPos = xPos
        self.yPos = yPos
        self.footstepSound = pygame.mixer.Sound("resources/sound/footsteps.wav")
        self.isFootstepsPlaying = False
        self.lightAng = 0  # angle of light above rightwards vector, in radians
        self.dx = 0  # x and y components of own velocity
        self.dy = 0
        self.speed = 6  # general speed of player when moving (pixels per update)

    def update(self, state, world):
        """Get speed of user in x and y based on keys pressed, detect collisions, and move player."""
        # reset speed values
        self.dx = 0; self.dy = 0
        # take user input
        if state[pygame.K_w]: self.dy -= self.speed
        if state[pygame.K_a]: self.dx -= self.speed
        if state[pygame.K_s]: self.dy += self.speed
        if state[pygame.K_d]: self.dx += self.speed
        # check if will remain in world in 2 of same turn; if not, negate movement (collision detection)
        if not world.isInWorld(self.xPos + 2*self.dx, self.yPos): self.dx = 0
        if not world.isInWorld(self.xPos, self.yPos + 2*self.dy): self.dy = 0
        if self.dx!=0 and self.dy!=0 and not world.isInWorld(self.xPos+ 2*self.dx, self.yPos+ 2*self.dy):  # may be hitting edge of a corner
            self.dx = 0; self.dy = 0
        # update position
        self.xPos += self.dx
        self.yPos += self.dy
        # play sound of footsteps
        if (self.dx!=0 or self.dy!=0) and not self.isFootstepsPlaying:
            self.footstepSound.play(loops=-1)  # play on repeat indefinitely
            self.isFootstepsPlaying = True
        elif (self.dx==0 and self.dy==0) and self.isFootstepsPlaying:
            self.footstepSound.stop()  # when player stops moving, stop footstep sound loop
            self.isFootstepsPlaying = False


    def kill(self):
        pass

    def drawTo(self, screen):
        x, y = screen.get_size()
        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(x/2 - 10, y/2 - 10, 20, 20))
