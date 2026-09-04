import pygame
import sys
import random
import copy

# ─────────────────────────────────────────────
#  Константи
# ─────────────────────────────────────────────
WIDTH, HEIGHT    = 560, 700
CELL_SIZE        = 56
GRID_ORIGIN_X    = 28
GRID_ORIGIN_Y    = 28
FPS              = 120
CONFLICT_SHOW_MS = 1500

DIFFICULTY = {
    "Легкий":   45,
    "Середній": 35,
    "Важкий":   25,
}

# Кольори
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GRAY       = (40,  40,  40)
LIGHT_GRAY = (150, 150, 160)
BLUE       = (50,  110, 200)
LIGHT_BLUE = (210, 230, 255)
RED        = (210, 50,  50)
GREEN      = (50,  180, 80)
BG_COLOR   = (248, 248, 252)
BTN_COLOR  = (70,  130, 220)
BTN_HOVER  = (50,  100, 190)
MENU_BG    = (30,  40,  70)
MENU_CARD  = (45,  58,  95)


# ─────────────────────────────────────────────
#  Логіка Генерації (з гарантією унікальності)
# ─────────────────────────────────────────────
def is_valid_gen(board, row, col, num):
    if num in board[row]:
        return False
    if num in [board[r][col] for r in range(9)]:
        return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == num:
                return False
    return True

def solve(board):
    """Стандартний бектрекінг для повного заповнення дошки."""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if is_valid_gen(board, row, col, num):
                        board[row][col] = num
                        if solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def count_solutions(board):
    """Рахує кількість розв'язків. Потрібно для гарантії єдиного варіанту."""
    count = [0]
    
    def solve_count():
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    for num in range(1, 10):
                        if is_valid_gen(board, row, col, num):
                            board[row][col] = num
                            solve_count()
                            board[row][col] = 0
                            if count[0] >= 2: return # Зупинка, якщо знайдено більше одного
                    return
        count[0] += 1
        
    solve_count()
    return count[0]

def generate_puzzle(clues=35):
    """Генерує пазл, де кожна цифра на своєму місці — єдино правильна."""
    board = [[0] * 9 for _ in range(9)]
    solve(board)
    solution = copy.deepcopy(board)
    
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    
    removed = 0
    target_remove = 81 - clues
    
    for r, c in cells:
        if removed >= target_remove:
            break
        
        backup = board[r][c]
        board[r][c] = 0
        
        # Якщо видалення створює другий розв'язок — повертаємо число
        if count_solutions(board) != 1:
            board[r][c] = backup
        else:
            removed += 1
            
    return board, solution


# ─────────────────────────────────────────────
#  Клас Board
# ─────────────────────────────────────────────
class Board:
    def __init__(self, clues=35):
        self.puzzle, self.solution = generate_puzzle(clues=clues)
        self.grid    = copy.deepcopy(self.puzzle)
        self.fixed   = [[self.puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
        self.errors  = [[False] * 9 for _ in range(9)]
        self.victory = False

    def has_conflict(self, row, col, num):
        # Перевірка на миттєві правила судоку (для підказки конфлікту)
        for c in range(9):
            if c != col and self.grid[row][c] == num: return True
        for r in range(9):
            if r != row and self.grid[r][col] == num: return True
        br, bc = (row // 3) * 3, (col // 3) * 3
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if (r, c) != (row, col) and self.grid[r][c] == num: return True
        return False

    def set_cell(self, row, col, num):
        if not self.fixed[row][col]:
            self.grid[row][col] = num
            self.errors[row][col] = False
            self.victory = False

    def clear_cell(self, row, col):
        if not self.fixed[row][col]:
            self.grid[row][col] = 0
            self.errors[row][col] = False
            self.victory = False

    def validate_all(self):
        # Оскільки розв'язок унікальний, порівняння з solution коректне на 100%
        self.victory = True
        for r in range(9):
            for c in range(9):
                val = self.grid[r][c]
                if val == 0:
                    self.victory = False
                    self.errors[r][c] = False
                elif val != self.solution[r][c]:
                    self.errors[r][c] = True
                    self.victory = False
                else:
                    self.errors[r][c] = False



#  Інтерфейс

def draw_menu(screen, fonts, selected_diff, mouse_pos):
    screen.fill(MENU_BG)
    title = fonts["title"].render("СУДОКУ", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 140)))
    
    sub = fonts["sub"].render("Оберіть рівень складності", True, (180, 195, 230))
    screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 200)))

    buttons = {}
    diff_info = {
        "Легкий":   ("45 підказок", GREEN),
        "Середній": ("35 підказок", (250, 180, 30)),
        "Важкий":   ("25 підказок", RED),
    }
    
    card_w, card_h = 140, 90
    start_x = (WIDTH - (3 * card_w + 40)) // 2
    
    for i, (lvl, (hint_txt, accent)) in enumerate(diff_info.items()):
        x = start_x + i * (card_w + 20)
        rect = pygame.Rect(x, 270, card_w, card_h)
        is_sel = (lvl == selected_diff)
        
        c = (70, 95, 150) if is_sel else (60, 80, 130) if rect.collidepoint(mouse_pos) else MENU_CARD
        pygame.draw.rect(screen, c, rect, border_radius=12)
        if is_sel: pygame.draw.rect(screen, accent, rect, width=3, border_radius=12)

        t_lvl = fonts["btn"].render(lvl, True, WHITE)
        screen.blit(t_lvl, t_lvl.get_rect(center=(x + card_w // 2, 302)))
        t_hint = fonts["label"].render(hint_txt, True, accent)
        screen.blit(t_hint, t_hint.get_rect(center=(x + card_w // 2, 332)))
        buttons[lvl] = rect

    play_rect = pygame.Rect(WIDTH // 2 - 110, 410, 220, 52)
    play_col = (40, 160, 80) if play_rect.collidepoint(mouse_pos) else (50, 180, 80)
    pygame.draw.rect(screen, play_col, play_rect, border_radius=12)
    t_play = fonts["btn"].render("Грати", True, WHITE)
    screen.blit(t_play, t_play.get_rect(center=play_rect.center))
    buttons["play"] = play_rect
    
    return buttons

def draw_game(screen, fonts, board, selected, conflict_active, mouse_pos):
    screen.fill(BG_COLOR)
    ox, oy = GRID_ORIGIN_X, GRID_ORIGIN_Y

    for row in range(9):
        for col in range(9):
            x, y = ox + col * CELL_SIZE, oy + row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            
            # Підсвічування
            if selected and (row, col) == selected:
                pygame.draw.rect(screen, LIGHT_BLUE, rect)
            elif selected and (row == selected[0] or col == selected[1] or (row//3 == selected[0]//3 and col//3 == selected[1]//3)):
                pygame.draw.rect(screen, (235, 242, 255), rect)
            else:
                pygame.draw.rect(screen, WHITE, rect)

            val = board.grid[row][col]
            if val != 0:
                color = BLACK if board.fixed[row][col] else RED if board.errors[row][col] else BLUE
                text = fonts["num"].render(str(val), True, color)
                screen.blit(text, text.get_rect(center=(x + CELL_SIZE//2, y + CELL_SIZE//2)))

    for i in range(10):
        thick = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, BLACK if i%3==0 else GRAY, (ox, oy + i*CELL_SIZE), (ox + 504, oy + i*CELL_SIZE), thick)
        pygame.draw.line(screen, BLACK if i%3==0 else GRAY, (ox + i*CELL_SIZE, oy), (ox + i*CELL_SIZE, oy + 504), thick)

    # Повідомлення
    msg, color = (None, None)
    if conflict_active: msg, color = "Це число вже є поруч!", RED
    elif board.victory: msg, color = "Чудово! Розв'язано правильно!", GREEN
    elif any(any(row) for row in board.errors): msg, color = "Є помилки, виправте їх", RED

    if msg:
        txt = fonts["msg"].render(msg, True, color)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 590)))

    buttons = {}
    btn_data = [("menu", "← Меню", 85), ("check", "Перевірити", 225), ("new", "Нова гра", 370), ("solve", "Підказка", 495)]
    for key, label, cx in btn_data:
        rect = pygame.Rect(cx - 55, 645, 110, 40)
        col = BTN_HOVER if rect.collidepoint(mouse_pos) else BTN_COLOR
        pygame.draw.rect(screen, col, rect, border_radius=8)
        screen.blit(fonts["btn_small"].render(label, True, WHITE), fonts["btn_small"].render(label, True, WHITE).get_rect(center=rect.center))
        buttons[key] = rect

    return buttons


# ─────────────────────────────────────────────
#  Головний цикл
# ─────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Sudoku Master")
    clock = pygame.time.Clock()

    # Спроба завантажити Segoe UI, інакше стандартний шрифт
    def get_font(size, bold=False):
        return pygame.font.SysFont("segoeui, arial, helvetica", size, bold=bold)

    fonts = {
        "title": get_font(64, True), "sub": get_font(22), "btn": get_font(20, True),
        "btn_small": get_font(16, True), "label": get_font(16), "num": get_font(30, True),
        "msg": get_font(22, True)
    }

    scene = "menu"
    selected_diff = "Середній"
    board = None
    selected = None
    conflict_timer = 0
    btn_cooldown = 0

    while True:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        if conflict_timer > 0: conflict_timer -= dt
        if btn_cooldown > 0: btn_cooldown -= dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN and scene == "game":
                if event.key == pygame.K_ESCAPE: scene = "menu"
                if selected:
                    r, c = selected
                    if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        board.clear_cell(r, c)
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        num = event.key - pygame.K_0
                        if board.has_conflict(r, c, num): conflict_timer = 1000
                        else: board.set_cell(r, c, num)
                    elif pygame.K_KP1 <= event.key <= pygame.K_KP9:
                        num = event.key - pygame.K_KP0
                        if board.has_conflict(r, c, num): conflict_timer = 1000
                        else: board.set_cell(r, c, num)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if scene == "game":
                    gx, gy = event.pos
                    if GRID_ORIGIN_X <= gx < GRID_ORIGIN_X + 504 and GRID_ORIGIN_Y <= gy < GRID_ORIGIN_Y + 504:
                        selected = ((gy - GRID_ORIGIN_Y)//CELL_SIZE, (gx - GRID_ORIGIN_X)//CELL_SIZE)
                        conflict_timer = 0
            if event.type == pygame.KEYDOWN:
                if selected:
                    r, c = selected
                    if event.key == pygame.K_UP:    r = (r - 1) % 9
                    if event.key == pygame.K_DOWN:  r = (r + 1) % 9
                    if event.key == pygame.K_LEFT:  c = (c - 1) % 9
                    if event.key == pygame.K_RIGHT: c = (c + 1) % 9
                    selected = (r, c)
                else:
                    selected = (0, 0) # Якщо нічого не вибрано, починаємо з верхнього кута

        if scene == "menu":
            btns = draw_menu(screen, fonts, selected_diff, mouse_pos)
            if pygame.mouse.get_pressed()[0] and btn_cooldown <= 0:
                for d in DIFFICULTY:
                    if btns[d].collidepoint(mouse_pos):
                        selected_diff = d; btn_cooldown = 200
                if btns["play"].collidepoint(mouse_pos):
                    board = Board(clues=DIFFICULTY[selected_diff])
                    scene = "game"; selected = None; btn_cooldown = 300

        elif scene == "game":
            btns = draw_game(screen, fonts, board, selected, conflict_timer > 0, mouse_pos)
            if pygame.mouse.get_pressed()[0] and btn_cooldown <= 0:
                if btns["menu"].collidepoint(mouse_pos): scene = "menu"; btn_cooldown = 300
                if btns["check"].collidepoint(mouse_pos): board.validate_all(); btn_cooldown = 300
                if btns["new"].collidepoint(mouse_pos):
                    board = Board(clues=DIFFICULTY[selected_diff])
                    selected = None; btn_cooldown = 300
                if btns["solve"].collidepoint(mouse_pos):
                    board.grid = copy.deepcopy(board.solution)
                    board.validate_all(); btn_cooldown = 300

        pygame.display.flip()

if __name__ == "__main__":
    main()