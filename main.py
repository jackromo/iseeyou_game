import pygame
from gamesession import GameSession

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((800, 800))
    session = GameSession(screen)
    print session.startGame()
    pygame.mixer.quit()

if __name__ == "__main__":
    main()
