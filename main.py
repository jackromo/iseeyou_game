import pygame
from gamesession import GameSession

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    session = GameSession(screen)
    session.start()

if __name__ == "__main__":
    main()
