import pygame
from gamesession import GameSession

PLAY = 0
CONTROLS = 1
QUIT = 2
NO_SELECTION = 3


class MenuSession(object):

    def __init__(self, screen):
        self.screen = screen
        self.fakeSession = GameSession(self.screen)
        self.fakeSession.newGame()
        self.gameSession = GameSession(self.screen)
        self.keys = None
        self.selectedOption = PLAY
        self.selectionBoxes = None
        self.isControlsMenu = False  # if False, on main menu, else on controls menu
        self.hasQuitted = False
        self.wasLeftClkDown = False

    def start(self):
        self.keys = pygame.key.get_pressed()
        while not self.hasQuitted:
            if not self.isControlsMenu:
                self.updateMain()
                self.renderMain()
            else:
                self.updateControls()
                self.renderControls()
            pygame.display.flip()
            pygame.event.pump()

    def updateMain(self):
        if self.selectionBoxes == None:
            return
        self.selectedOption = NO_SELECTION
        for choice, box in enumerate(self.selectionBoxes):
            if box.collidepoint(pygame.mouse.get_pos()):
                self.selectedOption = choice
        if pygame.mouse.get_pressed()[0]:
            self.wasLeftClkDown = True
        elif self.wasLeftClkDown:
            self.wasLeftClkDown = False
            if self.selectedOption == PLAY:
                self.gameSession.startGame()
                pygame.mixer.stop()
                self.gameOverScreen()
            elif self.selectedOption == CONTROLS:
                self.isControlsMenu = True
            elif self.selectedOption == QUIT:
                self.hasQuitted = True
        self.fakeSession.updateFake()

    def renderMain(self):
        w, h = self.screen.get_size()
        self.fakeSession.renderFake()
        titleFont = pygame.font.SysFont("comicsans", 100)
        title = titleFont.render("iseeyou", 1, (255, 63, 63))
        selectFont = pygame.font.SysFont("comicsans", 75)
        play = selectFont.render("Play", 1, (255, 255, 255))
        controls = selectFont.render("Controls", 1, (255, 255, 255))
        quit = selectFont.render("Quit", 1, (255, 255, 255))
        xT, yT = title.get_size()
        xC, yC = controls.get_size()
        xP, yP = play.get_size()
        xQ, yQ = quit.get_size()
        self.screen.blit(title, (w/2 - xT/2, h/2 - yT/2 - 350))
        self.screen.blit(play, (w/2 - xP/2 - 300, h/2 - yP/2))
        self.screen.blit(controls, (w/2 - xC/2, h/2 - yC/2 + 300))
        self.screen.blit(quit, (w/2 - xQ/2 + 300, h/2 - yQ/2))
        self.selectionBoxes = [pygame.Rect(w/2 - xP/2 - 300, h/2 - yP/2, xP, yP),
                               pygame.Rect(w/2 - xC/2, h/2 - yC/2 + 300, xC, yC),
                               pygame.Rect(w/2 - xQ/2 + 300, h/2 - yQ/2, xQ, yQ)]
        for box in self.selectionBoxes:
            if box.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (200, 200, 200), box, 3)

    def updateControls(self):
        if pygame.mouse.get_pressed()[0]:
            self.wasLeftClkDown = True
        elif self.wasLeftClkDown:
            self.wasLeftClkDown = False
            self.isControlsMenu = False

    def renderControls(self):
        w, h = self.screen.get_size()
        self.fakeSession.renderFake()
        titleFont = pygame.font.SysFont("comicsans", 100)
        title = titleFont.render("Controls", 1, (255, 63, 63))
        textFont = pygame.font.SysFont("comicsans", 75)
        lines = ["WASD - move", "Mouse - move flashlight", "Q - quit gameplay",
                 "ESC - pause game", "LCTRL - Sneak", "LSHIFT - Run", "(Click screen for main menu)"]
        renderedLines = [textFont.render(line, 1, (255,255,255)) for line in lines]
        xT, yT = title.get_size()
        self.screen.blit(title, (w/2 - xT/2, h/2 - yT/2 - 350))
        for i, line in enumerate(renderedLines):
            self.screen.blit(line, (100, 200 + (80*i)))

    def gameOverScreen(self):
        for counter in range(400):
            w, h = self.screen.get_size()
            pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(0,0,w,h))
            textFont = pygame.font.SysFont("comicsans", 50)
            line = textFont.render("igotyou", 1, (127, 0, 0))
            self.screen.blit(line, (400, 600))
            pygame.display.flip()
