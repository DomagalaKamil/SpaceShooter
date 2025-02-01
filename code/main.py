import pygame 
import os
from os.path import join
from random import randint, uniform
import json

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

# Load assets
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
ship_images = ['red_ship.png', 'blue_ship.png', 'green_ship.png', 'orange_ship.png']
ship_index = 0

def load_ship(index):
    return pygame.image.load(join('images', ship_images[index])).convert_alpha()

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
    def __init__(self, groups, selected_ship):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', selected_ship)).convert_alpha()  # Load player image
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
        game_running = False # End the game if player is hit
        end_game()
        return  
    # If lasers hit meteors, destroy them and show an explosion
    for laser in laser_sprites:
        collided_meteors = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if collided_meteors:
            laser.kill() # Remove laser
            for meteor in collided_meteors:
                AnimatedExplosion(explosion_frames, meteor.rect.center, all_sprites) # Show explosion

def create_button(text, x, y, width, height, text_color, button_color, border_radius=10):
    button_rect = pygame.Rect(x, y, width, height)  # Create button rectangle
    pygame.draw.rect(display_surface, button_color, button_rect, border_radius=border_radius)  # Draw button with rounded corners
    text_surf = font.render(text, True, text_color)  # Render text surface
    text_rect = text_surf.get_rect(center=button_rect.center)  # Center text inside button
    display_surface.blit(text_surf, text_rect)  # Draw text on button
    return button_rect  # Return button rect for interaction handling

# Display the current score on the screen
def display_score():
    text_surf = font.render(str(score), True, (240,240,240))  # Render the score text
    text_rect = text_surf.get_frect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))  # Position the score at the bottom
    display_surface.blit(text_surf, text_rect)  # Draw the score
    pygame.draw.rect(display_surface, (240,240,240), text_rect.inflate(20, 10).move(0, -8), 5, 10)  # Draw a border around score

# Main menu function
def main_menu():
    global game_running
    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 125, WINDOW_HEIGHT // 1.5, 250, 100)  # Button position and size
    
    while True:
        display_surface.fill((30, 30, 30))  # Fill background with dark gray
        button_text = font.render("Start Game", True, (0, 0, 0))  # Render the "Start Game" text
        pygame.draw.rect(display_surface, (255, 255, 255), button_rect)  # Draw the button rectangle in white
        display_surface.blit(button_text, button_text.get_rect(center=button_rect.center))  # Place the text in the center of the button
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Check if the user clicked the close button
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):  # If mouse clicked on button
                selected_ship = ship_selection_menu()  # Open ship selection menu and get the selected ship
                game_running = True  # Set game_running flag to True
                game_loop(selected_ship)  # Start the game loop with the selected ship
        
        pygame.display.update()  # Update the display

# Skip selection function
def ship_selection_menu():
    global ship_index
    selected_ship = None
    
    # Define the positions and sizes of navigation arrows and select button
    left_arrow = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2, 50, 50)
    right_arrow = pygame.Rect(WINDOW_WIDTH // 2 + 150, WINDOW_HEIGHT // 2, 50, 50)
    select_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 1.5, 200, 100)
    
    while selected_ship is None:
        display_surface.fill((30, 30, 30))  # Fill background with dark gray
        
        # Load and display the ship image based on current ship_index
        ship_surf = load_ship(ship_index)
        ship_rect = ship_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        display_surface.blit(ship_surf, ship_rect)
        
        # Draw arrows and select button
        pygame.draw.rect(display_surface, (255, 255, 255), left_arrow)
        pygame.draw.rect(display_surface, (255, 255, 255), right_arrow)
        pygame.draw.rect(display_surface, (255, 255, 255), select_button)
        
        # Render text for the arrows and select button
        left_text = font.render("<", True, (0, 0, 0))
        right_text = font.render(">", True, (0, 0, 0))
        select_text = font.render("Select", True, (0, 0, 0))
        
        # Display text on the respective UI elements
        display_surface.blit(left_text, left_text.get_rect(center=left_arrow.center))
        display_surface.blit(right_text, right_text.get_rect(center=right_arrow.center))
        display_surface.blit(select_text, select_text.get_rect(center=select_button.center))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Handle quit event
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if left_arrow.collidepoint(event.pos):  # Decrease ship_index to show previous ship
                    ship_index = (ship_index - 1) % len(ship_images)
                elif right_arrow.collidepoint(event.pos):  # Increase ship_index to show next ship
                    ship_index = (ship_index + 1) % len(ship_images)
                elif select_button.collidepoint(event.pos):  # Select current ship
                    selected_ship = ship_images[ship_index]
                    return selected_ship
        
        pygame.display.update()  # Update display to reflect changes


# Main game loop
def game_loop(selected_ship):
    global game_running, player, score

    score = 0  # Reset the score at the start of each new game
    clear_game_objects()  # Clear previous game objects

    player = Player(all_sprites, selected_ship)  # Create player object

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

def end_game():
    global game_running
    
    # Button dimensions and positions
    button_width, button_height = 280, 110
    play_again_x = WINDOW_WIDTH // 2 - 275
    back_to_menu_x = WINDOW_WIDTH // 2 + 25
    button_y = WINDOW_HEIGHT // 1.5
    
    while not game_running:
        display_surface.fill((30, 30, 30))  # Fill background with dark gray
        
        # Display Game Over text in red
        game_over_surf = font.render("Game Over", True, (255, 0, 0))
        game_over_rect = game_over_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        display_surface.blit(game_over_surf, game_over_rect)
        
        # Display the final score in white
        score_surf = font.render(f"Score: {score}", True, (255, 255, 255))
        score_rect = score_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        display_surface.blit(score_surf, score_rect)
        
        # Create buttons: Play Again and Back to Menu
        play_again_rect = create_button("Play Again", play_again_x, button_y, button_width, button_height, (0, 0, 0), (255, 255, 255))
        back_to_menu_rect = create_button("Back to Menu", back_to_menu_x, button_y, button_width, button_height, (0, 0, 0), (255, 255, 255))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Handle quit event
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_rect.collidepoint(event.pos):  # Restart the game with a new ship selection
                    selected_ship = ship_selection_menu()
                    game_running = True
                    game_loop(selected_ship)
                elif back_to_menu_rect.collidepoint(event.pos):  # Go back to the main menu
                    game_running = False
                    main_menu()
        
        pygame.display.update()  # Update display to show changes


# Start the main menu
main_menu()  # Begin with the main menu