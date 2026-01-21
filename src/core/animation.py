import pygame

class AnimationClip:
    def __init__(self, name, frames, fps=10, loop=True):
        self.name = name
        self.frames = frames  # List of pygame.Surface
        self.fps = fps
        self.loop = loop
        self.duration = len(frames) / fps if fps > 0 else 0

class AnimationController:
    def __init__(self):
        self.animations = {}
        self.current_animation = None
        self.current_frame_index = 0.0
        self.playing = False
        self.flip_x = False

    def add_animation(self, name, sheet, frame_data_list):
        """
        frame_data_list: List of dicts or tuples with (x, y, w, h)
        """
        frames = []
        sheet_rect = sheet.get_rect()
        
        for data in frame_data_list:
            x, y, w, h = data['x'], data['y'], data['w'], data['h']
            rect = pygame.Rect(x, y, w, h)
            
            # Clip rect to sheet
            clipped_rect = rect.clip(sheet_rect)
            
            # If clipping made it smaller, or empty, handle it
            if clipped_rect.width <= 0 or clipped_rect.height <= 0:
                print(f"Warning: Frame for {name} is out of bounds {rect}. Using empty frame.")
                frame = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
            else:
                try:
                    frame = sheet.subsurface(clipped_rect)
                except ValueError as e:
                    print(f"Error creating subsurface for {name} {rect}: {e}")
                    # Fallback
                    frame = pygame.Surface((w, h), pygame.SRCALPHA)

            frames.append(frame)
        
        # Default settings, can be overridden
        fps = 10
        if 'fps' in frame_data_list[0]:
            fps = frame_data_list[0]['fps']
            
        loop = True
        if 'loop' in frame_data_list[0]:
            loop = frame_data_list[0]['loop']

        self.animations[name] = AnimationClip(name, frames, fps, loop)

    def play(self, name, force_restart=False):
        if name not in self.animations:
            print(f"Animation {name} not found!") # Debug
            return

        if self.current_animation and self.current_animation.name == name and not force_restart:
            return

        self.current_animation = self.animations[name]
        self.current_frame_index = 0.0
        self.playing = True

    def update(self, dt):
        if not self.playing or not self.current_animation:
            return

        # Advance frame
        self.current_frame_index += self.current_animation.fps * dt

        # Handle looping / ending
        if self.current_frame_index >= len(self.current_animation.frames):
            if self.current_animation.loop:
                self.current_frame_index %= len(self.current_animation.frames)
            else:
                self.current_frame_index = len(self.current_animation.frames) - 1
                self.playing = False

    def get_frame(self):
        if not self.current_animation:
            return None
        
        idx = int(self.current_frame_index)
        # Safety clamp
        idx = max(0, min(idx, len(self.current_animation.frames) - 1))
        
        frame = self.current_animation.frames[idx]
        
        if self.flip_x:
            frame = pygame.transform.flip(frame, True, False)
            
        return frame

    def load_from_csv(self, csv_path, sprite_sheet):
        import csv
        import os
        
        print(f"Loading animations from CSV: {csv_path}")

        if not os.path.exists(csv_path):
            print(f"Animation CSV not found: {csv_path}")
            return

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            try:
                header = next(reader) # Skip header
                print(f"CSV Header: {header}")
            except StopIteration:
                print("CSV is empty!")
                return

            loaded_count = 0
            for row in reader:
                # Name,StartX,StartY,Width,Height,Count,FPS,Loop
                if len(row) < 8: 
                    print(f"Skipping malformed row: {row}")
                    continue
                
                name = row[0].strip()
                try:
                    x = int(row[1])
                    y = int(row[2])
                    w = int(row[3])
                    h = int(row[4])
                    count = int(row[5])
                    fps = int(row[6])
                    loop_val = row[7].strip()
                    loop = loop_val.lower() == 'true'
                except ValueError as e:
                    print(f"Error parsing row for {name}: {e}")
                    continue

                frames_data = []
                for i in range(count):
                    frames_data.append({
                        'x': x + i * w,
                        'y': y,
                        'w': w,
                        'h': h,
                        'fps': fps,
                        'loop': loop
                    })
                
                self.add_animation(name, sprite_sheet, frames_data)
                print(f"Registered animation: '{name}' with {count} frames.")
                loaded_count += 1
            
            print(f"Total animations loaded: {loaded_count}")
            print(f"Available keys: {list(self.animations.keys())}")

    def load_from_paths(self, csv_path, sprite_sheet_path):
        import pygame
        import os
        
        if not os.path.exists(sprite_sheet_path):
            print(f"Sprite sheet not found: {sprite_sheet_path}")
            return False

        if not os.path.exists(csv_path):
            print(f"Animation CSV not found: {csv_path}")
            return False
            
        try:
            sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
            self.load_from_csv(csv_path, sheet)
            return True
        except Exception as e:
            print(f"Error loading animation from paths ({csv_path}, {sprite_sheet_path}): {e}")
            return False
