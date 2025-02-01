import pygame 
from os.path import join
from random import randint, uniform

# Initialize pygame
pygame.init()

# Set up display window
WINDOW_WIDTH, WINDOW_HEIGHT = 1600, 900
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space Shooter')  # Set the window title
clock = pygame.time.Clock()  # Create clock to manage the frame rate

# Load assets (images, fonts, sounds)
star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]
laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
laser_sound.set_volume(0.5)
explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
game_music.set_volume(0.4)

# Button for starting the game
button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 50, 200, 100)

# Game states and variables
game_running = False  # Keeps track of whether the game is running or not
score = 0  # Variable to track the score

# Sprite groups to manage different types of game objects
all_sprites = pygame.sprite.Group()  
meteor_sprites = pygame.sprite.Group()  
laser_sprites = pygame.sprite.Group()  

# Player class represents the player character in the game
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()  # Load player image
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))  # Set initial position
        self.direction = pygame.Vector2()  # Store movement direction
        self.speed = 300  # Player speed
        self.can_shoot = True  # Whether the player can shoot
        self.laser_shoot_time = 0  # Time of last shot (for cooldown)
        self.cooldown_duration = 400  # Cooldown in milliseconds for shooting
        self.mask = pygame.mask.from_surface(self.image)  # Used for pixel-perfect collisions
    
    def laser_timer(self):
        """Handles the shooting cooldown, allowing the player to shoot again after a set time."""
        if not self.can_shoot and pygame.time.get_ticks() - self.laser_shoot_time >= self.cooldown_duration:
            self.can_shoot = True
    
    def update(self, dt):
        """Handles player movement and shooting."""
        keys = pygame.key.get_pressed()  # Get the current key presses
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])  # Horizontal movement
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])  # Vertical movement
        self.direction = self.direction.normalize() if self.direction else self.direction  # Normalize direction vector
        self.rect.center += self.direction * self.speed * dt  # Move player
        
        if keys[pygame.K_SPACE] and self.can_shoot:  # If spacebar is pressed and the player can shoot
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))  # Create new laser object
            self.can_shoot = False  # Set shooting cooldown
            self.laser_shoot_time = pygame.time.get_ticks()  # Record the time of shot
            laser_sound.play()  # Play laser sound
        
        self.laser_timer()  # Check and handle laser cooldown

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf  # Laser image
        self.rect = self.image.get_rect(midbottom=pos)  # Position the laser at the player's position
    
    def update(self, dt):
        """Move the laser upwards and delete it if it goes off-screen."""
        self.rect.centery -= 400 * dt  # Move laser upwards
        if self.rect.bottom < 0:  # If the laser goes off-screen, remove it
            self.kill()

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf  # Star image
        self.rect = self.image.get_rect(center=(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))  # Random position

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf  # Save original meteor image for rotation
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)  # Random direction
        self.speed = randint(400, 500)  # Random speed for each meteor
        self.rotation_speed = randint(40, 80)  # Random rotation speed
        self.rotation = 0
        self.mask = pygame.mask.from_surface(self.image)  # Collision mask
    
    def update(self, dt):
        """Update meteor position and rotation."""
        self.rect.center += self.direction * self.speed * dt  # Move meteor
        self.rotation += self.rotation_speed * dt  # Apply rotation
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)  # Apply rotation to image
        self.rect = self.image.get_rect(center=self.rect.center)  # Update the rect with the new rotated image

        if self.rect.top > WINDOW_HEIGHT:  # If meteor moves off-screen, remove it
            self.kill()

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames  # List of frames for explosion animation
        self.frame_index = 0  # Current frame index
        self.image = self.frames[self.frame_index]  # Set initial frame as the first explosion frame
        self.rect = self.image.get_rect(center=pos)  # Position of explosion
        explosion_sound.play()  # Play explosion sound
    
    def update(self, dt):
        """Animate the explosion frames."""
        self.frame_index += 20 * dt  # Move through frames over time
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]  # Update to the next frame
        else:
            self.kill()  # After all frames are shown, remove explosion

# Function to clear all game objects (called at the start of a new game)
def clear_game_objects():
    all_sprites.empty()  
    meteor_sprites.empty()  
    laser_sprites.empty() 

# Collision Handling function
def check_collisions():
    global game_running

    # If the player collides with a meteor, end the game
    if pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask):
        game_running = False  # End the game if player is hit
        return  

    # If lasers hit meteors, destroy them and show an explosion
    for laser in laser_sprites:
        collided_meteors = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if collided_meteors:
            laser.kill()  # Remove laser
            for meteor in collided_meteors:
                AnimatedExplosion(explosion_frames, meteor.rect.center, all_sprites)  # Show explosion

# Display the current score on the screen
def display_score():
    text_surf = font.render(str(score), True, (240,240,240))  # Render the score text
    text_rect = text_surf.get_frect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))  # Position the score at the bottom
    display_surface.blit(text_surf, text_rect)  # Draw the score
    pygame.draw.rect(display_surface, (240,240,240), text_rect.inflate(20, 10).move(0, -8), 5, 10)  # Draw a border around score

# Main menu function
def main_menu():
    global game_running 
    
    while not game_running:
        display_surface.fill((30, 30, 30))  # Fill the screen with colour
        pygame.draw.rect(display_surface, (255, 255, 255), button_rect, border_radius=10)  # Draw the "Start Game" button
        text_surf = font.render("Start Game", True, (0, 0, 0))  # Render text on button
        text_rect = text_surf.get_rect(center=button_rect.center)
        display_surface.blit(text_surf, text_rect)  # Draw the text
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # If the player closes the game window
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):  # If the button is clicked
                game_running = True
                game_loop()  # Start the game loop
        
        pygame.display.update()  # Update the screen

# Main game loop
def game_loop():
    global game_running, player, score

    score = 0  # Reset the score at the start of each new game
    clear_game_objects()  # Clear previous game objects

    player = Player(all_sprites)  # Create player object

    # Add stars to the background
    for _ in range(20):
        all_sprites.add(Star(all_sprites, star_surf))
    
    # Event to spawn meteors periodically
    meteor_event = pygame.USEREVENT + 1
    pygame.time.set_timer(meteor_event, 200)  # Set meteor spawn interval
    
    # Track the start time of the game to calculate score
    start_time = pygame.time.get_ticks()

    while game_running:
        dt = clock.tick(60) / 1000  # Time difference per frame (in seconds)

        # Update score based on the time since the game started
        score = (pygame.time.get_ticks() - start_time) // 100 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == meteor_event:
                # Spawn a new meteor
                Meteor(meteor_surf, (randint(0, WINDOW_WIDTH), randint(-100, 0)), (all_sprites, meteor_sprites))
        
        all_sprites.update(dt)  # Update all sprites
        check_collisions()  # Check for collisions (player with meteors, lasers with meteors)

        display_surface.fill('#3a2e3f')  # Fill the screen with a background color
        all_sprites.draw(display_surface)  # Draw all sprites (player, meteors, lasers, etc.)

        display_score()  # Display the score on the screen

        pygame.display.update()  # Update the screen

    main_menu()  # If game ends, show the main menu again

# Start the main menu
main_menu()  # Begin with the main menu
