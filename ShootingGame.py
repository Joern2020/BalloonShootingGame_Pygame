import pygame
import random
import sys
from pygame import mixer
from pygame.math import Vector2


class ScoringAnimation(pygame.sprite.Sprite):
    def __init__(self, position, offset_Y, color_index, scoring_amplifier, delta_t):
        super().__init__()
        self.image = Score_font.render(f'+{scoring_amplifier}', True, pygame.Color(ColorList[color_index]))
        self.rect = self.image.get_rect()
        self.initialY = position[1]-offset_Y
        self.rect.center = self.position = Vector2(position[0], self.initialY)
        self.velocity = Vector2(0, -0.2)
        self.d_t = delta_t

    def update(self):
        self.position += self.velocity * self.d_t
        self.rect.center = self.position

        if self.position.y - self.initialY <= -50:  # the sprite is removed after it moved 50 pixels
            self.kill()


class Target(pygame.sprite.Sprite):  # define a Target(Balloon) class
    def __init__(self, randnum, position, velocity, scale, delta_t):
        super().__init__()
        img_idle_list = Balloon_idle_Set[randnum]
        img_quit_list = Balloon_quit_Set[randnum]
        img_width, img_height = img_idle_list[0].get_rect().size
        img_width = int(img_width * scale)
        img_height = int(img_height * scale)  # scale the image width and height
        self.ColorIndex = randnum
        self.ImgIdle_list_scaled = []
        self.ImgQuit_list_scaled = []

        # scale all the images in the lists
        for list_num in range(len(img_idle_list)):
            Tmp_img = img_idle_list[list_num]
            Tmp_img = pygame.transform.smoothscale(Tmp_img, (img_width, img_height))
            self.ImgIdle_list_scaled.append(Tmp_img)
        for list_num in range(len(img_quit_list)):
            Tmp_img = img_quit_list[list_num]
            Tmp_img = pygame.transform.smoothscale(Tmp_img, (img_width, img_height))
            self.ImgQuit_list_scaled.append(Tmp_img)

        self.image = self.ImgIdle_list_scaled[0]
        self.rect = self.image.get_rect()
        self.rect.center = self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.d_t = delta_t
        self.mask = pygame.mask.from_surface(self.image)  # Creates a Mask from the given surface
        self.quit_trigger = False
        self.time_counter = 0
        self.frame = 0
        self.ani_frametime = self.d_t * FPS_value * 0.05

    def update(self, env_movement):
        if self.quit_trigger:  # if triggered to quit, run quitting animation
            self.quit_animation()
        else:
            self.idle_animation()
            self.position += self.velocity * self.d_t

        self.position += env_movement  # add the scrolled movement to the position
        self.rect.center = self.position

        if self.rect.center[1] < -50:
            self.kill()  # sprite is removed if it is out of the top screen

    def set_quit_trigger(self):
        self.quit_trigger = True
        self.time_counter = 0
        self.frame = 0
        # print("Hit! Score: ", score)
        channel3.play(hit_sound)

    def require_parameters(self):
        return self.position, self.rect.height, self.ColorIndex

    def idle_animation(self):
        self.time_counter += self.d_t
        if self.time_counter >= self.ani_frametime * 4:
            self.frame += 1
            self.time_counter = 0
        if self.frame > len(self.ImgIdle_list_scaled) - 1:
            self.frame = 0
        self.image = self.ImgIdle_list_scaled[self.frame]

    def quit_animation(self):
        self.time_counter += self.d_t
        if self.frame <= len(self.ImgQuit_list_scaled) - 1:
            self.image = self.ImgQuit_list_scaled[self.frame]
            if self.time_counter >= self.ani_frametime:
                self.frame += 1
                self.time_counter = 0
            quit_velocity = Vector2(self.velocity.x, 0.05)  # set a velocity for the quitting animation
            self.position += quit_velocity * self.d_t
        elif self.frame > len(self.ImgQuit_list_scaled) - 1:
            self.kill()
            self.time_counter = 0
            self.frame = 0
            self.quit_trigger = False

    def is_quit_trigger(self):
        return self.quit_trigger


class BulletIcon(pygame.sprite.Sprite):  # define a BulletIcon class
    def __init__(self, position, delta_t, Img_List):
        super().__init__()
        self.img_list = Img_List

        self.image = self.img_list[0]
        self.rect = self.image.get_rect()
        self.rect.center = self.position = Vector2(position)
        self.velocity = Vector2(random.random()*0.5+0.1, random.random()*-1-0.3)
        self.acceleration = Vector2(0, 0.006)
        self.delta_t = delta_t
        self.quit_trigger = False
        self.rotate_angle = 0
        self.delta_angle = 0

    def update(self):
        if self.quit_trigger:
            self.quit_animation()

    def quit_animation(self):
        self.image = pygame.transform.rotozoom(self.img_list[1], self.rotate_angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.velocity += self.acceleration * self.delta_t
        self.position += self.velocity * self.delta_t
        self.rect.center = self.position
        self.rotate_angle += self.delta_angle * self.delta_t

        if self.rect.center[1] > screen_height + 20:  # sprite removed if out of the bottom screen
            self.kill()
            self.quit_trigger = False

    def set_quit_trigger(self):
        self.quit_trigger = True
        self.rotate_angle = random.randint(-30, 30)
        self.delta_angle = (random.random()*2-1) * 3
        self.image = pygame.transform.rotozoom(self.img_list[1], self.rotate_angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def is_quit_trigger(self):
        return self.quit_trigger


def add_target(group, env_x, scale, number, dt):  # add Target sprites into a group
    count = len(group)
    if count < number:
        position = start_position_generation()
        position.x += env_x
        velocity = start_velocity_generation(scale)
        ran_num = random.randint(0, len(Balloon_idle_Set) - 1)
        target = Target(ran_num, position, velocity, scale, dt)
        group.add(target)


def start_position_generation():  # initialize positions of the target sprites
    position = Vector2(random.randint(0, 3000), screen_height + random.randint(0, 100))
    return position


def start_velocity_generation(scale):  # initialize velocities of the target sprites
    vel_x = random.random() * 0.3 - 0.15               # range (-0.15, 0.15)
    vel_y = random.random() * -0.1 - 0.1 * scale    # range (-0.2, -0.1) * scale
    velocity = Vector2(vel_x, vel_y)
    return velocity


def bullet_clear(group):  # empty bullets
    group.empty()
    return False


def bullet_reload(group, delta_time, Img_list):  # reload bullets
    group.empty()
    ammo_number = 10
    position = Vector2(screen_width - 20 * ammo_number, screen_height - 40)
    for bullet_count in range(ammo_number):
        bullet_icon = BulletIcon(position, delta_time, Img_list)
        position.x += 20
        group.add(bullet_icon)
    # print("Ammo reloaded")
    channel2.play(reload_sound)
    return True


def bullet_reduction(group):  # reduce bullets
    bullet_list = group.sprites()
    bullet_index = len(bullet_list) - 1
    if bullet_list:
        while bullet_list[bullet_index].is_quit_trigger():
            bullet_index -= 1
            if bullet_index < 0:
                # print("Out of ammo!!")
                channel2.play(no_ammo_sound)
                return False
        bullet_list[bullet_index].set_quit_trigger()
        channel2.play(shoot_sound)
        # print("Biu~")
        return True
    else:
        # print("Out of ammo!!")
        channel2.play(no_ammo_sound)
        return False


def set_cursor(path):   # set a customized cursor
    image = pygame.image.load(path).convert_alpha()
    img_width, img_height = image.get_rect().size
    defined_cursor = pygame.cursors.Cursor((int(img_width/2), int(img_height/2)), image)
    pygame.mouse.set_cursor(defined_cursor)


def check_shooting(group, score_amplifier, d_t):  # shooting checking function
    global score
    mouse_pos = pygame.mouse.get_pos()
    real_shot_list = []

    for collide_sprite in group:
        if collide_sprite.rect.collidepoint(mouse_pos):
            pos_in_mask = mouse_pos[0] - collide_sprite.rect.x, mouse_pos[1] - collide_sprite.rect.y
            if collide_sprite.mask.get_at(pos_in_mask):  # check if the mouse position is within the mask
                real_shot_list.append(collide_sprite)

    if real_shot_list:
        if not real_shot_list[-1].is_quit_trigger():
            real_shot_list[-1].set_quit_trigger()

            score += 1 * score_amplifier  # score accumulation

            position, height, color_index = real_shot_list[-1].require_parameters()
            scoring_ani_group.add(ScoringAnimation(position, height / 2, color_index, score_amplifier, d_t))

            real_shot_list[-1].remove()
        return True
    return False


def update_fps():
    fps = str(int(clock.get_fps()))
    fps_text = FPS_font.render(f'FPS: {fps}', True, pygame.Color(WHITE))
    return fps_text


def update_time(seconds):
    is_end = False
    time_limit = 60
    countdown = int((time_limit - seconds) * 10) / 10  # 1 decimal remained
    time_text = Score_font.render(f'TIME LEFT: {countdown} s', True, pygame.Color(WHITE))

    if countdown < 10 and (int(countdown) + 1) % 2 == 0: # flash effect on the text when <10s
        time_text = Score_font.render(f'TIME LEFT: {countdown} s', True, pygame.Color(DARK_RED))

    if countdown <= 0:
        is_end = True

    return time_text, is_end


def update_score():
    score_text = Score_font.render(f'SCORE: {score}', True, pygame.Color(WHITE))
    return score_text


def require_state(prepare_trigger, start_trigger, end_trigger):
    if not prepare_trigger and not start_trigger and not end_trigger:
        state = 0  # initial state, not playing
    elif prepare_trigger and not start_trigger and not end_trigger:
        state = 1  # countdown state, get ready to play
    elif not prepare_trigger and start_trigger and not end_trigger:
        state = 2  # playing state
    elif not prepare_trigger and not start_trigger and end_trigger:
        state = 3  # end state
    else:
        state = 4  # error
        print("Error")
    return state


def load_balloon(condition, color_name):  # function to load image sequences
    res = []
    for count in range(1, 5):
        im = pygame.image.load(f"res/balloon/{condition}_{color_name}_{count}.png")
        res.append(im.convert_alpha())
    return res


pygame.init()
clock = pygame.time.Clock()
FPS_value = 60

# load sounds and define channels

announce_sound = mixer.Sound('res/audio/announce.mp3')

hit_sound = mixer.Sound('res/audio/Hit.ogg')

shoot_sound = mixer.Sound('res/audio/LaserGun.ogg')
no_ammo_sound = mixer.Sound('res/audio/NoAmmo.ogg')
reload_sound = mixer.Sound('res/audio/GunCocking.ogg')

MUSICSTOP = pygame.event.custom_type()  # define event

channel1 = pygame.mixer.Channel(0)
channel1.set_volume(0.3)
channel1.set_endevent(MUSICSTOP)  # define the event that's sent when a sound stops playing
channel2 = pygame.mixer.Channel(1)
channel2.set_volume(0.5)
channel3 = pygame.mixer.Channel(2)

# create screen
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))

set_cursor("res/crosshair.png")

# load images
Bullet_List = [pygame.image.load("res/bullet_icon.png").convert_alpha(),
               pygame.image.load("res/bullet_shell_icon.png").convert_alpha()]

RedBalloon_idle_list = load_balloon("idle", "red")
RedBalloon_quit_list = load_balloon("explode", "red")
BlueBalloon_idle_list = load_balloon("idle", "blue")
BlueBalloon_quit_list = load_balloon("explode", "blue")
GreenBalloon_idle_list = load_balloon("idle", "lightgreen")
GreenBalloon_quit_list = load_balloon("explode", "lightgreen")
Balloon_idle_Set = [RedBalloon_idle_list, BlueBalloon_idle_list, GreenBalloon_idle_list]
Balloon_quit_Set = [RedBalloon_quit_list, BlueBalloon_quit_list, GreenBalloon_quit_list]

bg_sky = pygame.image.load("res/background/BG_sky.png").convert()
bg_mountain = pygame.image.load("res/background/BG_mountain.png").convert_alpha()
mg_hill = pygame.image.load("res/background/MG_hill.png").convert_alpha()
mg_bush = pygame.image.load("res/background/MG_bush.png").convert_alpha()
fg_grass = pygame.image.load("res/background/FG_grass.png").convert_alpha()

bg_sky = pygame.transform.smoothscale(bg_sky, (screen_width, screen_height))
W_fg_grass, H_fg_grass = fg_grass.get_rect().size

# define sprites and groups
scoring_ani_group = pygame.sprite.Group()

target_group1 = pygame.sprite.Group()
target_group2 = pygame.sprite.Group()
target_group3 = pygame.sprite.Group()
target_group4 = pygame.sprite.Group()

bullet_group = pygame.sprite.Group()

# define colors
ColorList = []
for i in range(len(Balloon_idle_Set)):
    tmp_img = Balloon_idle_Set[i][0]
    pixel_position = (32, 1)  # get a particular pixel on the image
    ColorList.append(tmp_img.get_at(pixel_position))
WHITE = (255, 255, 255)
DARK_RED = (205, 70, 80)

# define texts
FPS_font = pygame.font.SysFont("Arial", 18)
Score_font = pygame.font.SysFont("Showcard Gothic", 25)
Info_font = pygame.font.SysFont("Showcard Gothic", 30)

text_Ammo_Unavailable = Info_font.render(f'Out Of Ammo!!', True, pygame.Color(WHITE))
text_initial = Info_font.render(f'=== Click To Start ===', True, pygame.Color(DARK_RED))
text_initial_control1 = Info_font.render(f'Left: A                 Right: D', True, pygame.Color(WHITE))
text_initial_control2 = Info_font.render(f'Fire: L Click   Reload: R Click', True, pygame.Color(WHITE))
text_ready = Info_font.render(f'Ready?', True, pygame.Color(WHITE))
text_go = Info_font.render(f'GO!!', True, pygame.Color(DARK_RED))
text_end = Info_font.render(f'=== Game Over ===', True, pygame.Color(DARK_RED))
text_restart = Info_font.render(f'Press SPACE To Restart', True, pygame.Color(WHITE))

# define variables for scrolling effect
x = -300
v = 0
scrolling_speed = 0.1

# score initialization
score = 0

# define variables for time
delta_t = 0
Start_Time = 0
Current_Time = 0
Previous_Time = 0

# ammo initialization
ammo_available = False

# music initialization
mixer.music.load("res/audio/EndMusic.mp3")
pygame.mixer.music.set_volume(0.5)
mixer.music.play(-1)

# define triggers in game loop
edge_trigger = False

Prepare_trigger = False
StartPlay_trigger = False
EndPlay_trigger = False
MoveLeft_Flag = False
MoveRight_Flag = False

# initialize state for game loop
Loop_State = require_state(Prepare_trigger, StartPlay_trigger, EndPlay_trigger)


while True:
    ##################### framerate independence calculation #########################
    clock.tick(FPS_value)
    Current_Time = pygame.time.get_ticks()
    delta_t = Current_Time - Previous_Time
    Previous_Time = Current_Time

    ##################### input check #########################
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if Loop_State == 0:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # initialization for state 1 if clicked
                    Prepare_trigger = True
                    ammo_available = bullet_reload(bullet_group, delta_t, Bullet_List)
                    channel1.play(announce_sound)
                    mixer.music.fadeout(4000)

        elif Loop_State == 1:
            if event.type == MUSICSTOP:  # initialization for state 2 if sound stops
                Prepare_trigger = False
                StartPlay_trigger = True
                Start_Time = pygame.time.get_ticks()
                mixer.music.load("res/audio/PlayMusic.mp3")
                pygame.mixer.music.set_volume(0.5)
                mixer.music.play(-1)

        elif Loop_State == 2:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click return 1
                    ammo_available = bullet_reduction(bullet_group) # L mouse clicking reduces bullets
                    if ammo_available:  # check shooting
                        if not check_shooting(target_group1, 1, delta_t):
                            if not check_shooting(target_group2, 2, delta_t):
                                if not check_shooting(target_group3, 5, delta_t):
                                    check_shooting(target_group4, 10, delta_t)
                elif event.button == 3:  # right click return 3
                    ammo_available = bullet_reload(bullet_group, delta_t,Bullet_List) # R mouse clicking reloads ammo

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:  # scrolling left
                    MoveLeft_Flag = True
                if event.key == pygame.K_d:  # scrolling left
                    MoveRight_Flag = True
                v = -scrolling_speed * (MoveRight_Flag - MoveLeft_Flag)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    MoveLeft_Flag = False
                if event.key == pygame.K_d:
                    MoveRight_Flag = False
                v = -scrolling_speed * (MoveRight_Flag - MoveLeft_Flag)

        elif Loop_State == 3:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # initialization for state 0 if SPACE pressed
                    EndPlay_trigger = False
                    x = -300
                    v = 0
                    score = 0
                    Start_Time = 0
                    Current_Time = 0
                    Previous_Time = 0
                    ammo_available = bullet_clear(bullet_group)
                    sound_count = 0

    Loop_State = require_state(Prepare_trigger, StartPlay_trigger, EndPlay_trigger)

    if channel2.get_busy() or channel3.get_busy():
        pygame.mixer.music.set_volume(0.3)
    else:
        pygame.mixer.music.set_volume(0.5)

    ##################### game logic ######################
    # scrolling
    movement_step = v * delta_t
    x += movement_step
    if x < -600:
        x = -600
        edge_trigger = True
    elif x > 0:
        x = 0
        edge_trigger = True
    else:
        edge_trigger = False
        
    # blit background scene
    screen.blit(bg_sky, (0, 0))
    if Loop_State != 2:
        screen.blit(bg_mountain, (x * 2, 150))
        screen.blit(mg_hill, (x * 3.6, 350))
        screen.blit(mg_bush, (x * 4.5, 350))
        screen.blit(fg_grass, (x * 6.8, screen_height - H_fg_grass))
        
    # blit elements in state 0
    if Loop_State == 0: 
        screen.blit(text_initial, (250, 150))
        screen.blit(text_initial_control1, (180, 300))
        screen.blit(text_initial_control2, (180, 340))
        
    # blit elements in state 1
    if Loop_State == 1:
        screen.blit(text_ready, (350, 150))

        bullet_group.draw(screen)
        bullet_group.update()   
        
    # blit elements in state 2
    if Loop_State == 2:
        if edge_trigger:
            target_group1.update((0, 0))
            target_group2.update((0, 0))
            target_group3.update((0, 0))
            target_group4.update((0, 0))
        else:
            target_group1.update((movement_step * 6.8, 0))
            target_group2.update((movement_step * 4.5, 0))
            target_group3.update((movement_step * 3.6, 0))
            target_group4.update((movement_step * 2, 0))

        add_target(target_group4, x, 0.2, 10, delta_t)
        target_group4.draw(screen)

        screen.blit(bg_mountain, (x * 2, 150))
        add_target(target_group3, x * 2, 0.4, 5, delta_t)
        target_group3.draw(screen)

        screen.blit(mg_hill, (x * 3.6, 350))
        add_target(target_group2, x * 3.6, 0.6, 5, delta_t)
        target_group2.draw(screen)

        screen.blit(mg_bush, (x * 4.5, 350))
        add_target(target_group1, x * 4.5, 1, 10, delta_t)
        target_group1.draw(screen)

        screen.blit(fg_grass, (x * 6.8, screen_height - H_fg_grass))

        scoring_ani_group.draw(screen)
        scoring_ani_group.update()

        bullet_group.draw(screen)
        bullet_group.update()

        screen.blit(update_score(), (20, 20))

        if Current_Time - Start_Time <= 500:
            screen.blit(text_go, (380, 150))

        if not ammo_available:
            screen.blit(text_Ammo_Unavailable, (screen_width - 230, screen_height - 40))

        Time_text, EndPlay_trigger = update_time((Current_Time - Start_Time) / 1000)
        screen.blit(Time_text, (screen_width - 220, 20))

        if EndPlay_trigger and StartPlay_trigger:  # initialization for state 3
            MoveLeft_Flag = False
            MoveRight_Flag = False
            StartPlay_trigger = False
            v = -0.05
            target_group1.empty()
            target_group2.empty()
            target_group3.empty()
            target_group4.empty()
            mixer.music.load("res/audio/EndMusic.mp3")
            pygame.mixer.music.set_volume(0.5)
            mixer.music.play(-1)
            
    # blit elements in state 3
    if Loop_State == 3:
        screen.blit(text_end, (290, 150))
        screen.blit(text_restart, (220, 280))
        screen.blit(update_score(), (350, 220))
        if edge_trigger:
            v *= -1

    screen.blit(update_fps(), (20, screen_height - 30))
    pygame.display.flip()
