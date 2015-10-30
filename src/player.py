import pygame
from world import World

STANDING = 0
RUNNING = 1
WALKING = 2
SNEAKING = 3


class Player(object):

    def __init__(self, xPos, yPos):
        self.xPos = xPos
        self.yPos = yPos
        self.footstepSounds = {SNEAKING: pygame.mixer.Sound("resources/sound/footstepsSneaking.wav"),
                                WALKING: pygame.mixer.Sound("resources/sound/footstepsWalking.wav"),
                                RUNNING: pygame.mixer.Sound("resources/sound/footstepsRunning.wav")}
        self.lightAng = 0  # angle of light above rightwards vector, in radians
        self.dx = 0  # x and y components of own velocity
        self.dy = 0
        self.speed = 6  # general speed of player when moving (pixels per update)
        self.state = STANDING  # used by enemy to determine if player can be heard
        self.stamina = 1.0  # 1 if full stamina, 0 if depleted (used for running)

    def update(self, state, world):
        """Get speed of user in x and y based on keys pressed, detect collisions, and move player."""
        # reset speed values
        self.dx = 0; self.dy = 0
        prevState = self.state  # state before potential state change
        # take user input
        if state[pygame.K_LSHIFT] and self.stamina>0:
            self.state = RUNNING
            self.speed = 10
            self.stamina -= 0.01
        elif state[pygame.K_LCTRL]:
            self.state = SNEAKING
            self.speed = 2
        else:
            self.state = WALKING
            self.speed = 6
        if state[pygame.K_w]: self.dy -= self.speed
        if state[pygame.K_a]: self.dx -= self.speed
        if state[pygame.K_s]: self.dy += self.speed
        if state[pygame.K_d]: self.dx += self.speed
        if self.dx==0 and self.dy==0:
            self.state = STANDING
        if self.state != RUNNING and not state[pygame.K_LSHIFT] and self.stamina < 1.0:
            self.stamina += 0.01
        # check if will remain in world in 2 of same turn; if not, negate movement (collision detection)
        if not world.isInWorld(self.xPos + 2*self.dx, self.yPos): self.dx = 0
        if not world.isInWorld(self.xPos, self.yPos + 2*self.dy): self.dy = 0
        if self.dx!=0 and self.dy!=0 and not world.isInWorld(self.xPos+ 2*self.dx, self.yPos+ 2*self.dy):  # may be hitting edge of a corner
            self.dx = 0; self.dy = 0
        # update position
        self.xPos += self.dx
        self.yPos += self.dy
        # play sound of footsteps
        if (self.dx!=0 or self.dy!=0) and prevState != self.state:  # is moving and state has changed, so update sound
            if prevState != STANDING:
                self.footstepSounds[prevState].stop()  # stop previous sound
            self.footstepSounds[self.state].play(loops=-1)  # play on repeat indefinitely
        elif (self.dx==0 and self.dy==0) and prevState != STANDING:
            self.footstepSounds[prevState].stop()  # when player stops moving, stop footstep sound loop

    def getHeardRadius(self, world):
        """Return maximum distance enemy can currently be from player while still hearing player."""
        if self.state == STANDING:   return 0  # player cannot be heard if standing still
        elif self.state == WALKING:  return 5*(world.hallWidth + world.hallLength)
        elif self.state == SNEAKING: return world.hallWidth/2
        elif self.state == RUNNING:  return 10**10  # if running, enemy will always hear player

    def drawTo(self, screen):
        x, y = screen.get_size()
        pygame.draw.circle(screen, (127, 0, 0), (x/2,y/2), 15, 0)
        pygame.draw.circle(screen, (255, 0, 0), (x/2,y/2), int(15*self.stamina), 0)
