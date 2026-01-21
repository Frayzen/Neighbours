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
        for data in frame_data_list:
            x, y, w, h = data['x'], data['y'], data['w'], data['h']
            rect = pygame.Rect(x, y, w, h)
            frame = sheet.subsurface(rect)
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

    def _remove_background(self, surface, threshold=50):
        """
        Removes background color (based on top-left pixel) with a tolerance.
        """
        # Ensure alpha channel
        surface = surface.convert_alpha()
        
        # Get key color from top-left
        bg_color = surface.get_at((0, 0))
        
        # Use pygame.transform.threshold to find matching pixels and set them to transparent
        # search_color = bg_color
        # threshold = (threshold, threshold, threshold)
        # set_color = (0, 0, 0, 0) (Transparent)
        # set_behavior = 1 (Set color)
        
        pygame.transform.threshold(
            dest_surf=surface,           
            surf=surface,                
            search_color=bg_color,
            threshold=(threshold, threshold, threshold),
            set_color=(0, 0, 0, 0),      
            set_behavior=1               
        )
        
        return surface

    def load_from_csv(self, csv_path, sprite_sheet):
        import csv
        import os
        
        # Pre-process sheet to remove background
        sprite_sheet = self._remove_background(sprite_sheet)

        if not os.path.exists(csv_path):
            print(f"Animation CSV not found: {csv_path}")
            return

        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            try:
                header = next(reader) # Skip header
            except StopIteration:
                return

            for row in reader:
                # Name,StartX,StartY,Width,Height,Count,FPS,Loop
                if len(row) < 8: continue
                
                name = row[0]
                x = int(row[1])
                y = int(row[2])
                w = int(row[3])
                h = int(row[4])
                count = int(row[5])
                fps = int(row[6])
                loop_val = row[7]
                loop = loop_val.lower() == 'true'

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
