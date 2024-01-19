import sys
import pygame
import queue
from functools import reduce

class Game:
    quit_action = staticmethod(lambda: sys.exit(0))

    def is_valid_value(self, char):
        return char in [' ', '#', '@', '.', '*', '$', '+']

    def __init__(self, filename, level):
        self.queue = queue.LifoQueue()
        self.matrix = []

        if level < 1:
            print(f"ERROR: Level {level} is out of range")
            sys.exit(1)
        else:
            with open(filename, 'r') as file:
                level_found = False
                for line in file:
                    row = []
                    if not level_found:
                        if f"Level {level}" == line.strip():
                            level_found = True
                    else:
                        if line.strip() != "":
                            row = [c for c in line if c != '\n' and self.is_valid_value(c)]
                            self.matrix.append(row)
                        else:
                            break

    def load_size(self):
        x = max(len(row) for row in self.matrix)
        y = len(self.matrix)
        return (x * 64, y * 64)

    def get_matrix(self):
        return self.matrix

    def get_content(self, x, y):
        return self.matrix[y][x]

    def set_content(self, x, y, content):
        if self.is_valid_value(content):
            self.matrix[y][x] = content
        else:
            print(f"ERROR: Value '{content}' to be added is not valid")

    def worker(self):
        for y, row in enumerate(self.matrix):
            for x, char in enumerate(row):
                if char == '@' or char == '+':
                    return (x, y, char)

    def can_move(self, x, y):
        return self.get_content(self.worker()[0] + x, self.worker()[1] + y) not in ['#', '*', '$']

    def next(self, x, y):
        return self.get_content(self.worker()[0] + x, self.worker()[1] + y)

    def can_push(self, x, y):
        next_char = self.next(x, y)
        next_next_char = self.next(x + x, y + y)
        return next_char in ['*', '$'] and next_next_char in [' ', '.']

    def is_completed(self):
        return all('$' not in row for row in self.matrix)

    move_box = lambda self, x, y, a, b: (
        (lambda current_box, future_box:
         (self.set_content(x + a, y + b, '$') and self.set_content(x, y,
                                                                   ' ') if current_box == '$' and future_box == ' ' else
          self.set_content(x + a, y + b, '*') and self.set_content(x, y,
                                                                   ' ') if current_box == '$' and future_box == '.' else
          self.set_content(x + a, y + b, '$') and self.set_content(x, y,
                                                                   ' ') if current_box == '*' and future_box == ' ' else
          self.set_content(x + a, y + b, '*') and self.set_content(x, y,
                                                                   '.') if current_box == '*' and future_box == '.'
          else None)
         )(self.get_content(x, y), self.get_content(x + a, y + b))
    )
    def unmove(self):
        if not self.queue.empty():
            movement = self.queue.get()
            if movement[2]:
                current = self.worker()
                self.move(movement[0] * -1, movement[1] * -1, False)
                self.move_box(current[0] + movement[0], current[1] + movement[1], movement[0] * -1, movement[1] * -1)
            else:
                self.move(movement[0] * -1, movement[1] * -1, False)

    move_worker = lambda self, x, y, save: (
        (lambda current, future:
            (self.set_content(current[0] + x, current[1] + y, '@') if current[2] == '@' and future == ' ' else
             self.set_content(current[0] + x, current[1] + y, '+') if current[2] == '@' and future == '.' else
             self.set_content(current[0] + x, current[1] + y, '@') if current[2] == '+' and future == ' ' else
             self.set_content(current[0] + x, current[1] + y, '+') if current[2] == '+' and future == '.' else None)
        )(self.worker(), self.next(x, y)) if self.can_move(x, y) else None
    )
    def move(self, x, y, save):
        if self.can_move(x, y):
            current = self.worker()
            future = self.next(x, y)
            if current[2] == '@' and future == ' ':
                self.set_content(current[0] + x, current[1] + y, '@')
                self.set_content(current[0], current[1], ' ')
                if save:
                    self.queue.put((x, y, False))
            elif current[2] == '@' and future == '.':
                self.set_content(current[0] + x, current[1] + y, '+')
                self.set_content(current[0], current[1], ' ')
                if save:
                    self.queue.put((x, y, False))
            elif current[2] == '+' and future == ' ':
                self.set_content(current[0] + x, current[1] + y, '@')
                self.set_content(current[0], current[1], '.')
                if save:
                    self.queue.put((x, y, False))
            elif current[2] == '+' and future == '.':
                self.set_content(current[0] + x, current[1] + y, '+')
                self.set_content(current[0], current[1], '.')
                if save:
                    self.queue.put((x, y, False))
        elif self.can_push(x, y):
            current = self.worker()
            future = self.next(x, y)
            future_box = self.next(x + x, y + y)
            if current[2] == '@' and future == '$' and future_box == ' ':
                self.move_box(current[0] + x, current[1] + y, x, y)
                self.set_content(current[0], current[1], ' ')
                self.set_content(current[0] + x, current[1] + y, '@')
                if save:
                    self.queue.put((x, y, True))
            elif current[2] == '@' and future == '$' and future_box == '.':
                self.move_box(current[0] + x, current[1] + y, x, y)
                self.set_content(current[0], current[1], ' ')
                self.set_content(current[0] + x, current[1] + y, '@')
                if save:
                    self.queue.put((x, y, True))
            elif current[2] == '@' and future == '*' and future_box == ' ':
                self.move_box(current[0] + x, current[1] + y, x, y)
                self.set_content(current[0], current[1], ' ')
                self.set_content(current[0] + x, current[1] + y, '+')
                if save:
                    self.queue.put((x, y, True))
            elif current[2] == '@' and future == '*' and future_box == '.':
                self.move_box(current[0] + x, current[1] + y, x, y)
                self.set_content(current[0], current[1], ' ')
                self.set_content(current[0] + x, current[1] + y, '+')
                if save:
                    self.queue.put((x, y, True))
            if current[2] == '+' and future == '$' and future_box == ' ':
                self.move_box(current[0] + x, current[1] + y, x, y)
                self.set_content(current[0], current[1], '.')
                self.set_content(current[0] + x, current[1] + y, '@')
                if save:
                    self.queue.put((x, y, True))
            elif current[2] == '+' and future == '$' and future_box == '.':
                self.move_box(current[0] + x, current[1] + y, x, y)
                self.set_content(current[0], current[1], '.')
                self.set_content(current[0] + x, current[1] + y, '+')
                if save:
                    self.queue.put((x, y, True))

class UI:
    def __init__(self, game, images):
        self.game = game
        self.images = images
        self.background = (255, 226, 191)
        pygame.init()

def print_game(matrix, screen, images, background):
    screen.fill(background)
    x = 0
    y = 0
    for row in matrix:
        for char in row:
            screen.blit(images[char], (x, y))
            x = x + 64
        x = 0
        y = y + 64

def display_box(screen, message):
    font_object = pygame.font.Font(None, 18)
    pygame.draw.rect(screen, (0, 0, 0),
                     ((screen.get_width() / 2) - 100,
                      (screen.get_height() / 2) - 10,
                      200, 20), 0)
    pygame.draw.rect(screen, (255, 255, 255),
                     ((screen.get_width() / 2) - 102,
                      (screen.get_height() / 2) - 12,
                      204, 24), 1)
    if len(message) != 0:
        screen.blit(font_object.render(message, 1, (255, 255, 255)),
                    ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()

def display_end(screen):
    message = "Level Completed"
    font_object = pygame.font.Font(None, 18)
    pygame.draw.rect(screen, (0, 0, 0),
                     ((screen.get_width() / 2) - 100,
                      (screen.get_height() / 2) - 10,
                      200, 20), 0)
    pygame.draw.rect(screen, (255, 255, 255),
                     ((screen.get_width() / 2) - 102,
                      (screen.get_height() / 2) - 12,
                      204, 24), 1)
    screen.blit(font_object.render(message, 1, (255, 255, 255)),
                ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()

def ask(screen, question):
    pygame.font.init()
    current_string = []
    display_box(screen, question + ": " + ''.join(current_string))
    while True:
        inkey = get_key()
        if inkey == pygame.K_BACKSPACE:
            current_string = current_string[0:-1]
        elif inkey == pygame.K_RETURN:
            break
        elif inkey == pygame.K_MINUS:
            current_string.append("_")
        elif inkey <= 127:
            current_string.append(chr(inkey))
        display_box(screen, question + ": " + ''.join(current_string))
    return ''.join(current_string)

def get_key():
    while True:
        event = pygame.event.poll()
        if event.type == pygame.KEYDOWN:
            return event.key

def start_game():
    start = pygame.display.set_mode((320, 240))
    level_str = ask(start, "Select Level")
    try:
        level = int(level_str)
        if level > 0:
            return level
        else:
            print(f"ERROR: Invalid Level: {level}")
            sys.exit(2)
    except ValueError:
        print("ERROR: Invalid input. Please enter a valid level.")
        sys.exit(2)

def restart_game():
    level = start_game()
    game = Game('levels', level)
    size = game.load_size()
    screen = pygame.display.set_mode(size)
    ui = UI(game, images)
    return game, screen, ui

images = {
    'wall': pygame.image.load('images/wall1.png'),
    'floor': pygame.image.load('images/floor1.png'),
    'box': pygame.image.load('images/box1.png'),
    'box_docked': pygame.image.load('images/box1.png'),
    'worker': pygame.image.load('images/worker1.png'),
    'worker_dock': pygame.image.load('images/worker_dock1.png'),
    'dock': pygame.image.load('images/dock1.png'),

    '#': pygame.image.load('images/wall1.png'),
    ' ': pygame.image.load('images/floor1.png'),
    '.': pygame.image.load('images/dock1.png'),
    '@': pygame.image.load('images/worker1.png'),
    '$': pygame.image.load('images/box1.png'),
    '*': pygame.image.load('images/box1.png'),
    '+': pygame.image.load('images/worker_dock1.png'),
}

level = start_game()
game = Game('levels', level)
size = game.load_size()
screen = pygame.display.set_mode(size)

ui = UI(game, images)




while True:
    if game.is_completed():
        display_end(screen)
        pygame.display.update()
        pygame.time.delay(2000)  # Aguarda 2 segundos antes de reiniciar o jogo
        game, screen, ui = restart_game()  # Reinicia o jogo
    else:
        print_game(game.get_matrix(), screen, images, ui.background)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Game.quit_action()  # Executa a função lambda para sair do jogo
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    game.move(0, -1, True)
                elif event.key == pygame.K_DOWN:
                    game.move(0, 1, True)
                elif event.key == pygame.K_LEFT:
                    game.move(-1, 0, True)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0, True)
                elif event.key == pygame.K_q:
                    Game.quit_action()  # Executa a função lambda para sair do jogo
                elif event.key == pygame.K_d:
                    game.unmove()
    pygame.display.update()
