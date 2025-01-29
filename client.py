import tkinter as tk
from tkinter import messagebox
import threading
import requests
import random
import pygame
import sys

class FlappyBird:
    def __init__(self, token):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 708))
        self.token = token
        self.bird = pygame.Rect(65, 50, 50, 50)
        
        # Загрузка изображений
        try:
            self.background = pygame.image.load("./assets/background.png").convert()
            self.birdSprites = [
                pygame.image.load("./assets/1.png").convert_alpha(),  # Птица летит вниз
                pygame.image.load("./assets/2.png").convert_alpha(),  # Птица летит вверх
                pygame.image.load("./assets/dead.png").convert_alpha()  # Мёртвая птица
            ]
            self.wallUp = pygame.image.load("./assets/bottom.png").convert_alpha()
            self.wallDown = pygame.image.load("./assets/top.png").convert_alpha()
            
            # Добавляем загрузку медалей
            self.medals = [
                pygame.image.load("./assets/first.png").convert_alpha(),
                pygame.image.load("./assets/second.png").convert_alpha(),
                pygame.image.load("./assets/3rd.png").convert_alpha()
            ]
            # Масштабируем медали до нужного размера (например, 30x30 пикселей)
            self.medals = [pygame.transform.scale(medal, (30, 30)) for medal in self.medals]
            
        except pygame.error as e:
            print(f"Ошибка загрузки изображений: {e}")
            print("Убедитесь, что все файлы находятся в папке assets:")
            print("- background.png (задний фон)")
            print("- 1.png (птица летит вниз)")
            print("- 2.png (птица летит вверх)")
            print("- dead.png (мёртвая птица)")
            print("- bottom.png (нижняя труба)")
            print("- top.png (верхняя труба)")
            print("- first.png (медаль за первое место)")
            print("- second.png (медаль за второе место)")
            print("- 3rd.png (медаль за третье место)")
            sys.exit(1)

        self.gap = 130
        self.wallx = 400
        self.birdY = 350
        self.jump = 0
        self.jumpSpeed = 10
        self.gravity = 5
        self.dead = False
        self.sprite = 0  # Индекс текущего спрайта
        self.counter = 0
        self.offset = random.randint(-110, 110)
        self.show_leaderboard = False
        self.leaderboard_data = []
        self.update_leaderboard()
        self.reset_game()  # Вызываем reset_game при инициализации

    def update_leaderboard(self):
        try:
            response = requests.get("http://127.0.0.1:8001/leaderboard")
            self.leaderboard_data = response.json()
        except requests.RequestException:
            self.leaderboard_data = []

    def save_score(self):
        try:
            # Проверяем наличие токена
            if not self.token:
                print("Error: No authentication token")
                return

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Отправляем счет как JSON
            data = {"score": self.counter}
            response = requests.post(
                "http://127.0.0.1:8001/scores",
                json=data,  # Изменяем params на json
                headers=headers
            )
            
            print(f"Score saved response: {response.status_code}, {response.text}")
            if response.status_code != 200:
                print(f"Error saving score: {response.json()}")
        except requests.RequestException as e:
            print(f"Error saving score: {e}")

    def draw_leaderboard(self):
        font = pygame.font.SysFont("Arial", 25)
        y = 50
        
        # Заголовок таблицы
        title = font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen.get_width() // 2, y=y)
        self.screen.blit(title, title_rect)
        y += 50
        
        # Если данных нет
        if not self.leaderboard_data:
            text = font.render("Нет рекордов", True, (255, 255, 255))
            text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
            self.screen.blit(text, text_rect)
            return
        
        # Отображение результатов
        for item in self.leaderboard_data:
            position = item["position"]
            if position <= 3:
                # Отрисовка медали
                medal = self.medals[position - 1]
                medal_rect = medal.get_rect(
                    right=self.screen.get_width() // 2 - 70,  # Позиция медали слева от имени
                    centery=y + 15  # Центрируем медаль по вертикали
                )
                self.screen.blit(medal, medal_rect)
                
                # Отрисовка имени игрока
                name_text = font.render(item['username'], True, (255, 255, 255))
                name_rect = name_text.get_rect(
                    centerx=self.screen.get_width() // 2 - 20,
                    centery=y + 15
                )
                self.screen.blit(name_text, name_rect)
                
                # Отрисовка счета
                score_text = font.render(str(item['score']), True, (255, 255, 255))
                score_rect = score_text.get_rect(
                    left=name_rect.right + 20,
                    centery=y + 15
                )
                self.screen.blit(score_text, score_rect)
                
                y += 40  # Увеличиваем отступ для следующей записи

    def reset_game(self):
        # Сбрасываем все параметры игры
        self.birdY = 350
        self.wallx = 400
        self.jump = 0
        self.jumpSpeed = 10
        self.gravity = 5
        self.dead = False
        self.sprite = 0
        self.counter = 0
        self.offset = random.randint(-110, 110)
        self.show_leaderboard = False

    def run(self):
        pygame.init()
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Игровой цикл
            while not self.dead:
                self.game_loop()
                clock.tick(60)
            
            # После смерти
            self.sprite = 2  # Показываем спрайт мёртвой птицы
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))
            pygame.display.update()
            
            # Небольшая задержка перед показом экрана окончания игры
            pygame.time.wait(500)
            
            # Сохраняем результат
            self.save_score()
            self.update_leaderboard()
            
            # Показываем экран окончания игры
            if self.show_game_over():  # Если игрок нажал Enter
                self.reset_game()  # Сбрасываем игру
            else:  # Если игрок нажал ESC или закрыл окно
                running = False
                pygame.quit()

    def game_loop(self):
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or event.type == pygame.MOUSEBUTTONDOWN:
                    self.jump = 17
                    self.gravity = 5
                    self.jumpSpeed = 10
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    self.show_leaderboard = not self.show_leaderboard
                    if self.show_leaderboard:
                        self.update_leaderboard()

        # Обновление позиции птицы
        if self.jump:
            self.jumpSpeed -= 1
            self.birdY -= self.jumpSpeed
            self.jump -= 1
            self.sprite = 1  # Птица летит вверх
        else:
            self.birdY += self.gravity
            self.gravity += 0.2
            self.sprite = 0  # Птица летит вниз

        # Проверка столкновений
        self.bird[1] = self.birdY
        upRect = pygame.Rect(self.wallx, 360 + self.gap - self.offset + 10,
                           self.wallUp.get_width() - 10, self.wallUp.get_height())
        downRect = pygame.Rect(self.wallx, 0 - self.gap - self.offset - 10,
                             self.wallDown.get_width() - 10, self.wallDown.get_height())

        if upRect.colliderect(self.bird) or downRect.colliderect(self.bird):
            self.dead = True
        if not 0 < self.bird[1] < 720:
            self.dead = True

        # Отрисовка
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.background, (0, 0))

        if self.show_leaderboard:
            self.draw_leaderboard()
        else:
            # Обновление позиции труб
            self.wallx -= 2
            if self.wallx < -80:
                self.wallx = 400
                self.counter += 1
                self.offset = random.randint(-110, 110)

            self.screen.blit(self.wallUp, (self.wallx, 360 + self.gap - self.offset))
            self.screen.blit(self.wallDown, (self.wallx, 0 - self.gap - self.offset))
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))

            font = pygame.font.SysFont("Arial", 50)
            score_text = font.render(str(self.counter), True, (255, 255, 255))
            self.screen.blit(score_text, (200, 50))

        pygame.display.update()

    def show_game_over(self):
        clock = pygame.time.Clock()
        self.update_leaderboard()  # Обновляем таблицу лидеров сразу
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return True
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return False
            
            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))
            
            # Шрифты
            title_font = pygame.font.SysFont("Arial", 50)
            font = pygame.font.SysFont("Arial", 30)
            
            # Тексты
            game_over = title_font.render("ИГРА ОКОНЧЕНА!", True, (255, 255, 255))
            score = font.render(f"ВАШ СЧЁТ: {self.counter}", True, (255, 255, 255))
            continue_text = font.render("ENTER - НОВАЯ ИГРА", True, (255, 255, 255))
            exit_text = font.render("ESC - ВЫХОД", True, (255, 255, 255))
            
            # Позиционирование (изменяем координаты y)
            game_over_rect = game_over.get_rect(centerx=self.screen.get_width() // 2, y=50)
            score_rect = score.get_rect(centerx=self.screen.get_width() // 2, y=120)
            
            # Отрисовка заголовка и счета
            self.screen.blit(game_over, game_over_rect)
            self.screen.blit(score, score_rect)
            
            # Отрисовка таблицы лидеров со смещенной позицией y
            font = pygame.font.SysFont("Arial", 25)
            leaderboard_title = font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
            leaderboard_rect = leaderboard_title.get_rect(centerx=self.screen.get_width() // 2, y=200)
            self.screen.blit(leaderboard_title, leaderboard_rect)
            
            # Отображение результатов таблицы лидеров
            y = 250  # Начальная позиция для записей таблицы лидеров
            if not self.leaderboard_data:
                text = font.render("Нет рекордов", True, (255, 255, 255))
                text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
                self.screen.blit(text, text_rect)
            else:
                for item in self.leaderboard_data:
                    position = item["position"]
                    if position <= 3:
                        # Отрисовка медали
                        medal = self.medals[position - 1]
                        medal_rect = medal.get_rect(
                            right=self.screen.get_width() // 2 - 70,  # Позиция медали слева от имени
                            centery=y + 15  # Центрируем медаль по вертикали
                        )
                        self.screen.blit(medal, medal_rect)
                        
                        # Отрисовка имени игрока
                        name_text = font.render(item['username'], True, (255, 255, 255))
                        name_rect = name_text.get_rect(
                            centerx=self.screen.get_width() // 2 - 20,
                            centery=y + 15
                        )
                        self.screen.blit(name_text, name_rect)
                        
                        # Отрисовка счета
                        score_text = font.render(str(item['score']), True, (255, 255, 255))
                        score_rect = score_text.get_rect(
                            left=name_rect.right + 20,
                            centery=y + 15
                        )
                        self.screen.blit(score_text, score_rect)
                        
                        y += 40  # Увеличиваем отступ для следующей записи
            
            # Отрисовка кнопок внизу
            continue_rect = continue_text.get_rect(centerx=self.screen.get_width() // 2, y=550)
            exit_rect = exit_text.get_rect(centerx=self.screen.get_width() // 2, y=600)
            
            self.screen.blit(continue_text, continue_rect)
            self.screen.blit(exit_text, exit_rect)
            
            pygame.display.update()
            clock.tick(60)

class AuthApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flappy Bird - Авторизация")
        self.root.geometry("500x600")  # Увеличиваем размер окна
        self.root.resizable(False, False)
        
        # Центрируем окно
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2  # Обновляем координаты с учетом новой ширины
        y = (screen_height - 600) // 2  # Обновляем координаты с учетом новой высоты
        self.root.geometry(f"500x600+{x}+{y}")
        
        # Создаем основной контейнер с отступами
        main_frame = tk.Frame(self.root, padx=50, pady=30)  # Увеличиваем отступы
        main_frame.pack(expand=True, fill='both')
        
        # Заголовок с измененными параметрами
        title_label = tk.Label(
            main_frame, 
            text="Добро пожаловать\nв Flappy Bird!", 
            font=("Arial", 24, "bold"),  # Увеличиваем размер шрифта
            pady=30,
            justify=tk.CENTER  # Центрируем текст
        )
        title_label.pack()
        
        # Создаем рамку для формы
        form_frame = tk.Frame(main_frame, pady=20)
        form_frame.pack()
        
        # Поля ввода
        tk.Label(form_frame, text="Логин:", font=("Arial", 12)).pack()
        self.username_entry = tk.Entry(
            form_frame, 
            font=("Arial", 12),
            width=30
        )
        self.username_entry.pack(pady=(5, 15))
        
        tk.Label(form_frame, text="Пароль:", font=("Arial", 12)).pack()
        self.password_entry = tk.Entry(
            form_frame, 
            show="•",
            font=("Arial", 12),
            width=30
        )
        self.password_entry.pack(pady=(5, 20))
        
        # Кнопки
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        login_btn = tk.Button(
            buttons_frame,
            text="Войти",
            command=self.login,
            width=15,
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        login_btn.pack(pady=5)
        
        register_btn = tk.Button(
            buttons_frame,
            text="Регистрация",
            command=self.open_registration,
            width=15,
            font=("Arial", 11),
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        register_btn.pack(pady=5)
        
        exit_btn = tk.Button(
            buttons_frame,
            text="Выход",
            command=self.root.quit,
            width=15,
            font=("Arial", 11),
            bg="#f44336",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        exit_btn.pack(pady=5)
        
        self.token = None

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # Проверка на пустые поля
        if not username or not password:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля")
            return
        
        try:
            response = requests.post(
                "http://127.0.0.1:8001/login", 
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                self.token = response.json().get("token")
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                self.root.destroy()
                self.start_game()
            elif response.status_code == 401:
                messagebox.showerror("Ошибка", "Неверный логин или пароль")
            else:
                messagebox.showerror("Ошибка", "Ошибка сервера. Попробуйте позже")
            
        except requests.ConnectionError:
            messagebox.showerror(
                "Ошибка подключения", 
                "Не удалось подключиться к серверу.\nПроверьте подключение к интернету или попробуйте позже."
            )
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def open_registration(self):
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Flappy Bird - Регистрация")
        reg_window.geometry("400x550")
        reg_window.resizable(False, False)
        
        # Центрируем окно регистрации
        screen_width = reg_window.winfo_screenwidth()
        screen_height = reg_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 550) // 2
        reg_window.geometry(f"400x550+{x}+{y}")
        
        # Основной контейнер
        main_frame = tk.Frame(reg_window, padx=40, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Заголовок
        title_label = tk.Label(
            main_frame,
            text="Регистрация нового игрока",
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
        # Форма регистрации
        form_frame = tk.Frame(main_frame)
        form_frame.pack(pady=20)
        
        tk.Label(
            form_frame,
            text="Логин (минимум 3 символа):",
            font=("Arial", 12)
        ).pack()
        username_entry = tk.Entry(
            form_frame,
            font=("Arial", 12),
            width=30
        )
        username_entry.pack(pady=(5, 15))
        
        tk.Label(
            form_frame,
            text="Пароль (минимум 4 символа):",
            font=("Arial", 12)
        ).pack()
        password_entry = tk.Entry(
            form_frame,
            show="•",
            font=("Arial", 12),
            width=30
        )
        password_entry.pack(pady=(5, 15))
        
        tk.Label(
            form_frame,
            text="Подтверждение пароля:",
            font=("Arial", 12)
        ).pack()
        confirm_password_entry = tk.Entry(
            form_frame,
            show="•",
            font=("Arial", 12),
            width=30
        )
        confirm_password_entry.pack(pady=(5, 20))
        
        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm_password = confirm_password_entry.get()
            
            # Проверки ввода
            if not username or not password or not confirm_password:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля")
                return
            
            if len(username) < 3:
                messagebox.showerror("Ошибка", "Логин должен содержать минимум 3 символа")
                return
            
            if len(password) < 4:
                messagebox.showerror("Ошибка", "Пароль должен содержать минимум 4 символа")
                return

            if password != confirm_password:
                messagebox.showerror("Ошибка", "Пароли не совпадают")
                return

            try:
                data = {
                    "username": username,
                    "password": password
                }
                response = requests.post(
                    "http://127.0.0.1:8001/register", 
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo(
                        "Успех", 
                        "Регистрация успешна!\nТеперь вы можете войти в игру."
                    )
                    reg_window.destroy()
                else:
                    # Обрабатываем все ошибки сервера единообразно
                    try:
                        error_detail = response.json().get("detail", "")
                        if "Username already exists" in error_detail:
                            messagebox.showerror(
                                "Ошибка регистрации", 
                                "Пользователь с таким именем уже существует.\nПожалуйста, выберите другое имя пользователя."
                            )
                        else:
                            messagebox.showerror(
                                "Ошибка регистрации", 
                                "Не удалось зарегистрировать пользователя.\nПожалуйста, попробуйте позже."
                            )
                    except ValueError:
                        messagebox.showerror(
                            "Ошибка сервера", 
                            "Произошла ошибка при обработке запроса.\nПожалуйста, попробуйте позже."
                        )
                
            except requests.ConnectionError:
                messagebox.showerror(
                    "Ошибка подключения", 
                    "Не удалось подключиться к серверу.\nПроверьте подключение к интернету или попробуйте позже."
                )
            except requests.RequestException as e:
                messagebox.showerror(
                    "Ошибка соединения", 
                    "Произошла ошибка при подключении к серверу.\nПожалуйста, попробуйте позже."
                )

        # Кнопка регистрации
        register_btn = tk.Button(
            form_frame,
            text="Зарегистрироваться",
            command=register,
            width=20,
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        register_btn.pack(pady=20)

    def start_game(self):
        if not self.token:
            messagebox.showerror("Ошибка", "Не удалось получить токен авторизации")
            return
        
        try:
            # Проверяем валидность токена
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get("http://127.0.0.1:8001/me", headers=headers)
            
            if response.status_code == 200:
                game = FlappyBird(self.token)
                game.run()
            else:
                error_message = response.json().get("detail", "Неизвестная ошибка")
                messagebox.showerror("Ошибка", f"Ошибка авторизации: {error_message}")
                # Можно добавить перенаправление на окно входа
                self.__init__()
                self.run()
                
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка проверки токена: {str(e)}")
            return

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AuthApp()
    app.run()
