import pygame
from menusession import MenuSession

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("iseeyou")
    session = MenuSession(screen)
    session.start()
    pygame.mixer.quit()

if __name__ == "__main__":
    main()
