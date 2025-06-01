import sys
import math
import random
import platform
from PyQt6.QtWidgets import QApplication, QLabel, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QMovie, QCursor, QIcon, QPainter, QPixmap, QPaintEvent
import os
from pathlib import Path
import subprocess
import plistlib


class OnekoWindow(QLabel):
    CHASING = 1
    IDLE = 2
    SURPRISED = 3
    DIGGING = 4

    def __init__(self):
        super().__init__()
        self.current_movie = None  # Track current movie separately
        self.initialization_complete = False  # Track initialization state
        self.frame_skip_count = 0  # Track frame skips during init
        self.initUI()
        # Start at cursor position
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - self.SPRITE_SIZE // 2,
                  cursor_pos.y() - self.SPRITE_SIZE // 2)

    def complete_initialization(self):
        """Called after initialization period to optimize performance"""
        self.initialization_complete = True
        # Speed up the timer now that initialization is complete
        self.timer.setInterval(60)  # Faster updates for smooth motion
        print(f"Initialization complete! Frame skips during init: {self.frame_skip_count}")

    def paintEvent(self, event):
        """Optimized paint event with proper alpha handling"""
        painter = QPainter(self)
        
        # CRITICAL: Always clear with fully transparent background first
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Reset to normal composition for drawing the current frame
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Draw the current movie frame if we have one
        if self.current_movie and self.current_movie.state() == QMovie.MovieState.Running:
            current_pixmap = self.current_movie.currentPixmap()
            if not current_pixmap.isNull():
                # During initialization, be more lenient about missing frames
                if not self.initialization_complete and current_pixmap.size().isEmpty():
                    self.frame_skip_count += 1
                    painter.end()
                    return
                
                # Optimize: Only scale if necessary, and cache the size
                if not hasattr(self, '_cached_size') or self._cached_size != self.size():
                    self._cached_size = self.size()
                    self._needs_scaling = (current_pixmap.size() != self.size())
                
                if self._needs_scaling:
                    # Use faster scaling for better performance
                    scaled_pixmap = current_pixmap.scaled(
                        self.size(), 
                        Qt.AspectRatioMode.IgnoreAspectRatio,  # Faster than KeepAspectRatio
                        Qt.TransformationMode.FastTransformation  # Faster than SmoothTransformation
                    )
                    painter.drawPixmap(0, 0, scaled_pixmap)
                else:
                    # No scaling needed
                    painter.drawPixmap(0, 0, current_pixmap)
        elif not self.initialization_complete:
            # During init, if no movie is ready, draw a simple placeholder
            painter.setPen(Qt.GlobalColor.white)
            painter.drawEllipse(self.rect().center(), 2, 2)
        
        painter.end()

    def initUI(self):
        # Different window flags for macOS
        if platform.system() == "Darwin":
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                | Qt.WindowType.WindowDoesNotAcceptFocus
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                | Qt.WindowType.WindowTransparentForInput
                | Qt.WindowType.SubWindow
                | Qt.WindowType.WindowDoesNotAcceptFocus
            )
        
        # Essential for transparency but we'll handle alpha ourselves
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        # Re-enable mouse transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Constants
        self.THEME = "orange_cat"
        self.SPRITE_SIZE = 64
        self.TRIGGER_DISTANCE = 64
        self.CATCH_DISTANCE = 24
        self.OFFSET_X = -20
        self.OFFSET_Y = -20
        self.NEKO_SPEED = 24
        self.DIG_TIMEOUT = 50

        # State variables
        self.state = self.CHASING
        self.sleep_counter = 0
        self.idle_timer = 0
        self.current_frame = 0
        self.last_update = 0
        self.idle_action_timer = 0
        self.current_idle_action = 'sit'
        self.idle_action_counter = 0
        self.dig_timer = 0
        self.dig_direction = None

        # Load animations
        if not self.loadAnimations():
            print("Failed to load animations. Exiting.")
            return
            
        # Setup tray icon
        self.setupTrayIcon()
        
        # Don't set initial movie via setMovie() - let state machine handle it
        self.resize(self.SPRITE_SIZE, self.SPRITE_SIZE)
        
        # No background styling needed - we handle it in paintEvent
        
        # Timer for movement and state updates - optimized interval
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_state)
        self.timer.start(60)  # Reduced from 90ms to 60ms for smoother motion

        # Show window
        self.show()
        self.raise_()
        
        # Move to center for testing
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() // 2, screen.height() // 2)
        
        print("Setup complete!")

    def setNekoMovie(self, movie):
        """Optimized method to handle movie changes with proper alpha clearing"""
        if movie is None or movie == self.current_movie:
            return  # Skip if same movie
        
        # During initialization, be more careful about movie transitions
        if not self.initialization_complete:
            # Ensure the new movie is fully loaded before switching
            if movie.state() == QMovie.MovieState.NotRunning:
                movie.jumpToFrame(0)
                movie.start()
                # Give it a moment to load the first frame
                if movie.currentPixmap().isNull():
                    return  # Skip this transition, try again next update
            
        # Stop current movie if any
        if self.current_movie:
            self.current_movie.stop()
            try:
                self.current_movie.frameChanged.disconnect()
            except:
                pass  # Ignore if already disconnected
        
        # Set new current movie
        self.current_movie = movie
        
        # Connect frame changed signal to trigger repaints (but throttle updates)
        if self.current_movie:
            self.current_movie.frameChanged.connect(self.on_frame_changed)
            self.current_movie.jumpToFrame(0)
            if self.current_movie.state() != QMovie.MovieState.Running:
                self.current_movie.start()
        
        # Force immediate repaint only when changing movies
        self.update()

    def on_frame_changed(self):
        """Throttled frame update to improve performance"""
        # Only update if widget is visible and not already updating
        if self.isVisible() and not hasattr(self, '_updating'):
            self._updating = True
            self.update()
            # During initialization, use longer delays to prevent spam
            delay = 20 if not self.initialization_complete else 10
            QTimer.singleShot(delay, lambda: setattr(self, '_updating', False))

    def loadAnimations(self):
        self.animations = {}

        # Get the base path for resources
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.dirname(__file__))

        print(f"Looking for animations in: {base_path}")
        gif_folder = os.path.join(base_path, "theme_"+self.THEME)
        print(f"GIF folder path: {gif_folder}")

        # Load animations and pre-cache them
        for i in range(1, 33):
            gif_name = f"{i}.GIF"
            path = os.path.join(gif_folder, gif_name)

            if os.path.exists(path):
                try:
                    movie = QMovie(path)
                    movie.setScaledSize(QSize(self.SPRITE_SIZE, self.SPRITE_SIZE))
                    
                    # Optimize movie settings for better performance
                    movie.setCacheMode(QMovie.CacheMode.CacheAll)  # Cache frames for better performance
                    movie.setSpeed(100)  # Normal speed
                    
                    # Pre-load the first frame to prevent initialization delays
                    movie.jumpToFrame(0)
                    movie.start()
                    movie.stop()  # Stop after loading first frame
                    
                    self.animations[i - 1] = movie
                    print(f"Loaded animation {i}")
                except Exception as e:
                    print(f"Error loading animation {i}: {e}")
            else:
                print(f"Missing animation file: {path}")

        print(f"Total animations loaded: {len(self.animations)} out of 32")
        return len(self.animations) > 0

    def setupTrayIcon(self):
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Try multiple icon sources (restored from original)
        icon_loaded = False
        
        # First try icon files
        if not icon_loaded:
            if getattr(sys, 'frozen', False):
                # If running as exe/app bundle, use bundled path
                if platform.system() == "Darwin":
                    icon_path = os.path.join(sys._MEIPASS, "oneko.icns")
                else:
                    icon_path = os.path.join(sys._MEIPASS, "oneko.ico")
            else:
                # If running from script
                if platform.system() == "Darwin":
                    icon_path = "oneko.icns"
                else:
                    icon_path = "oneko.ico"

            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
                icon_loaded = True
                print(f"Using icon file: {icon_path}")

        # Then try to use one of the cat GIF frames as an icon
        if not icon_loaded:
            if hasattr(self, 'animations') and self.animations:
                try:
                    # Use the first animation frame as icon
                    first_animation = list(self.animations.values())[0]
                    if first_animation:
                        # Get current frame from the movie
                        first_animation.jumpToFrame(0)
                        pixmap = first_animation.currentPixmap()
                        if not pixmap.isNull():
                            icon = QIcon(pixmap)
                            self.tray_icon.setIcon(icon)
                            icon_loaded = True
                            print("Using cat animation frame as tray icon")
                except Exception as e:
                    print(f"Failed to use animation as icon: {e}")
        
        # Final fallback to system icon
        if not icon_loaded:
            if platform.system() == "Darwin":
                # Try different system icons for macOS
                system_icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
                self.tray_icon.setIcon(system_icon)
                print("Using system computer icon")
            else:
                self.tray_icon.setIcon(QIcon.fromTheme("applications-system"))
                print("Using system applications icon")

        # Also set the application icon (for dock/taskbar)
        if icon_loaded and hasattr(self, 'tray_icon'):
            app = QApplication.instance()
            app.setWindowIcon(self.tray_icon.icon())
            print("Set application icon for dock")
        
        # Create the tray menu
        self.tray_menu = QMenu()

        # Add toggle visibility action
        self.toggle_action = self.tray_menu.addAction("Hide Kitty")
        self.toggle_action.triggered.connect(self.toggleVisibility)

        # Add separator
        self.tray_menu.addSeparator()

        # Add autostart toggle (platform-specific text)
        if platform.system() == "Darwin":
            autostart_text = "Start with macOS"
        else:
            autostart_text = "Start with Windows"
        
        self.autostart_action = self.tray_menu.addAction(autostart_text)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self.is_autostart_enabled())
        self.autostart_action.triggered.connect(self.toggle_autostart)

        # Add separator
        self.tray_menu.addSeparator()

        # Add quit action
        quit_action = self.tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)

        # Set the menu for the tray icon
        self.tray_icon.setContextMenu(self.tray_menu)

        # Add tooltip
        self.tray_icon.setToolTip("Oneko")

        # Show the tray icon
        self.tray_icon.show()

    def toggleVisibility(self):
        if self.isVisible():
            self.hide()
            self.toggle_action.setText("Show Kitty")
        else:
            self.show()
            self.toggle_action.setText("Hide Kitty")

    # Add the missing autostart methods from original code
    def get_launch_agent_path(self):
        """Get the path for macOS LaunchAgent plist file"""
        home = Path.home()
        return home / "Library" / "LaunchAgents" / "com.oneko.plist"

    def get_startup_path(self):
        """Get the startup path for Windows"""
        return Path(os.path.expandvars('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\oneko.bat'))

    def is_autostart_enabled(self):
        """Check if autostart is enabled (cross-platform)"""
        if platform.system() == "Darwin":
            return self.get_launch_agent_path().exists()
        else:
            return self.get_startup_path().exists()

    def toggle_autostart(self):
        """Toggle autostart functionality (cross-platform)"""
        if platform.system() == "Darwin":
            self.toggle_autostart_mac()
        else:
            self.toggle_autostart_windows()

    def toggle_autostart_mac(self):
        """Handle autostart for macOS using LaunchAgent"""
        launch_agent_path = self.get_launch_agent_path()
        
        if self.autostart_action.isChecked():
            try:
                # Create LaunchAgents directory if it doesn't exist
                launch_agent_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Get the path to the current executable/script
                if getattr(sys, 'frozen', False):
                    program_path = sys.executable
                else:
                    program_path = os.path.abspath(sys.argv[0])
                
                # Create the plist content
                plist_content = {
                    'Label': 'com.oneko',
                    'ProgramArguments': [program_path],
                    'RunAtLoad': True,
                    'KeepAlive': False,
                    'StandardOutPath': '/tmp/oneko.log',
                    'StandardErrorPath': '/tmp/oneko.log'
                }
                
                # Write the plist file
                with open(launch_agent_path, 'wb') as f:
                    plistlib.dump(plist_content, f)
                
                # Load the launch agent
                subprocess.run(['launchctl', 'load', str(launch_agent_path)], 
                             capture_output=True, text=True)
                
                self.tray_icon.showMessage("Oneko", "Will start with macOS")
            except Exception as e:
                self.autostart_action.setChecked(False)
                self.tray_icon.showMessage("Oneko", f"Failed to enable autostart: {str(e)}")
        else:
            try:
                # Unload the launch agent
                if launch_agent_path.exists():
                    subprocess.run(['launchctl', 'unload', str(launch_agent_path)], 
                                 capture_output=True, text=True)
                    launch_agent_path.unlink()
                
                self.tray_icon.showMessage("Oneko", "Won't start with macOS")
            except Exception as e:
                self.autostart_action.setChecked(True)
                self.tray_icon.showMessage("Oneko", f"Failed to disable autostart: {str(e)}")

    def toggle_autostart_windows(self):
        """Handle autostart for Windows (original functionality)"""
        startup_path = self.get_startup_path()
        if self.autostart_action.isChecked():
            try:
                # If we're running from exe, use sys.executable
                # Otherwise use the script path
                exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
                with open(startup_path, 'w') as f:
                    f.write(f'start "" "{exe_path}"')
                self.tray_icon.showMessage("Oneko", "Will start with Windows")
            except Exception as e:
                self.autostart_action.setChecked(False)
                self.tray_icon.showMessage("Oneko", "Failed to enable autostart")
        else:
            try:
                if startup_path.exists():
                    startup_path.unlink()
                self.tray_icon.showMessage("Oneko", "Won't start with Windows")
            except Exception as e:
                self.autostart_action.setChecked(True)
                self.tray_icon.showMessage("Oneko", "Failed to disable autostart")

    def get_virtual_desktop_geometry(self):
        app = QApplication.instance()
        screens = app.screens()
        
        if not screens:
            return QApplication.primaryScreen().geometry()
        
        min_x = min(screen.geometry().x() for screen in screens)
        min_y = min(screen.geometry().y() for screen in screens)
        max_x = max(screen.geometry().x() + screen.geometry().width() for screen in screens)
        max_y = max(screen.geometry().y() + screen.geometry().height() for screen in screens)
        
        from PyQt6.QtCore import QRect
        return QRect(min_x, min_y, max_x - min_x, max_y - min_y)

    def is_cursor_on_screen(self):
        cursor_pos = QCursor.pos()
        app = QApplication.instance()
        screens = app.screens()
        
        for screen in screens:
            if screen.geometry().contains(cursor_pos):
                return True
        return False

    def get_screen_edge(self):
        cursor_pos = QCursor.pos()
        virtual_desktop = self.get_virtual_desktop_geometry()

        dist_top = abs(cursor_pos.y() - virtual_desktop.top())
        dist_bottom = abs(cursor_pos.y() - virtual_desktop.bottom())
        dist_left = abs(cursor_pos.x() - virtual_desktop.left())
        dist_right = abs(cursor_pos.x() - virtual_desktop.right())

        min_dist = min(dist_top, dist_bottom, dist_left, dist_right)
        
        if min_dist == dist_top:
            return "up", (16, 17)
        elif min_dist == dist_bottom:
            return "down", (20, 21)
        elif min_dist == dist_left:
            return "left", (22, 23)
        else:
            return "right", (18, 19)

    def update_state(self):
        cursor_pos = QCursor.pos()
        cat_pos = self.pos() + QPoint(self.SPRITE_SIZE // 2, self.SPRITE_SIZE // 2)

        dx = cursor_pos.x() + self.OFFSET_X - cat_pos.x()
        dy = cursor_pos.y() + self.OFFSET_Y - cat_pos.y()
        distance = math.sqrt(dx * dx + dy * dy)

        if not self.is_cursor_on_screen():
            if self.state != self.DIGGING:
                self.state = self.DIGGING
                self.dig_timer = 0
                self.dig_direction, _ = self.get_screen_edge()
            self.handle_digging()
            return

        if distance < self.CATCH_DISTANCE:
            if self.state != self.IDLE:
                self.state = self.IDLE
                self.idle_timer = 0
                self.current_idle_action = 'sit'
                self.idle_action_counter = 0
                if 24 in self.animations:
                    self.setNekoMovie(self.animations[24])
            self.handle_idle_animations()
            return

        if (self.state == self.IDLE or self.state == self.DIGGING) and distance > self.TRIGGER_DISTANCE:
            self.state = self.SURPRISED
            if 31 in self.animations:
                self.setNekoMovie(self.animations[31])
            self.last_update = 5
            return

        if self.state == self.SURPRISED:
            self.last_update -= 1
            if self.last_update <= 0:
                self.state = self.CHASING

        if self.state == self.CHASING:
            if distance > 0:
                angle = math.atan2(dy, dx)
                move_x = round((dx / distance) * self.NEKO_SPEED)
                move_y = round((dy / distance) * self.NEKO_SPEED)

                new_pos = self.pos() + QPoint(move_x, move_y)
                self.move(new_pos)

                degrees = math.degrees(angle)
                self.current_frame = (self.current_frame + 1) % 2
                self.set_direction_animation(degrees)

    def handle_digging(self):
        self.dig_timer += 1
        _, frames = self.get_screen_edge()

        frame_idx = frames[self.dig_timer % 2]
        if frame_idx in self.animations:
            self.setNekoMovie(self.animations[frame_idx])

        if self.dig_timer >= self.DIG_TIMEOUT:
            self.state = self.IDLE
            self.idle_timer = 301
            self.current_idle_action = 'sleep'
            self.idle_action_counter = 0

    def handle_idle_animations(self):
        self.idle_timer += 1

        if self.idle_timer % 100 == 0:
            if self.current_idle_action == 'sit':
                if random.random() < 0.15:
                    self.current_idle_action = 'wash'
                    self.idle_action_counter = 0
                elif self.idle_timer > 300 and random.random() < (0.5 if self.state == self.DIGGING else 0.1):
                    self.current_idle_action = 'sleep'
                    self.idle_action_counter = 0
            elif self.current_idle_action == 'wash':
                if self.idle_action_counter > 30:
                    self.current_idle_action = 'sit'
                    self.idle_action_counter = 0

        if self.current_idle_action == 'sit':
            if 24 in self.animations:
                self.setNekoMovie(self.animations[24])
        elif self.current_idle_action == 'wash':
            self.idle_action_counter += 1
            frame_idx = 24 + (self.idle_timer // 3 % 2)
            if frame_idx in self.animations:
                self.setNekoMovie(self.animations[frame_idx])
        elif self.current_idle_action == 'sleep':
            self.idle_action_counter += 1
            if self.idle_action_counter < 20:
                if 26 in self.animations:
                    self.setNekoMovie(self.animations[26])
            else:
                frame_idx = 28 + (self.idle_timer // 5 % 2)
                if frame_idx in self.animations:
                    self.setNekoMovie(self.animations[frame_idx])

    def set_direction_animation(self, degrees):
        frame_idx = None
        
        if -22.5 <= degrees <= 22.5:  # Right
            frame_idx = 4 + self.current_frame
        elif 22.5 < degrees <= 67.5:  # Down-Right
            frame_idx = 6 + self.current_frame
        elif 67.5 < degrees <= 112.5:  # Down
            frame_idx = 8 + self.current_frame
        elif 112.5 < degrees <= 157.5:  # Down-Left
            frame_idx = 10 + self.current_frame
        elif degrees > 157.5 or degrees <= -157.5:  # Left
            frame_idx = 12 + self.current_frame
        elif -157.5 < degrees <= -112.5:  # Up-Left
            frame_idx = 14 + self.current_frame
        elif -112.5 < degrees <= -67.5:  # Up
            frame_idx = 0 + self.current_frame
        elif -67.5 < degrees <= -22.5:  # Up-Right
            frame_idx = 2 + self.current_frame
            
        if frame_idx is not None and frame_idx in self.animations:
            self.setNekoMovie(self.animations[frame_idx])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = OnekoWindow()
    sys.exit(app.exec())