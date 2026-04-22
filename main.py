import json
import math
import os
import random
import sys
import tkinter as tk
from collections import deque
from tkinter import messagebox, ttk

import pystray
from PIL import Image, ImageDraw, ImageSequence, ImageTk

FPS = 30
DUCK_SCALE = 0.6
BANNER_W = 260
BANNER_H = 60
GIF_NAME = "a9378435ab8cf241898a33b66964051ffb3c9a0f.gif"
TRANSPARENT_NAME = "duck_transparent.png"
CONFIG_NAME = "config.json"
INSTALLER_LANGUAGE_NAME = "installer_language.json"
ICON_PNG_NAME = "app_icon.png"
ICON_ICO_NAME = "app_icon.ico"
BACKGROUND_TOLERANCE = 18

DEFAULT_CONFIG = {
    "interval_minutes": 10,
    "travel_duration_ms": 12000,
    "message": "ENDEREZA LA ESPALDA, PUÑETA",
    "language": "es",
    "start_with_windows": False,
    "minimize_to_tray": True,
}

LANGUAGE_NAMES = {
    "es": "Español",
    "en": "English",
}

LANGUAGE_CODES_BY_NAME = {name: code for code, name in LANGUAGE_NAMES.items()}
LANGUAGE_ALIASES = {
    "es": "es",
    "spanish": "es",
    "espanol": "es",
    "español": "es",
    "en": "en",
    "english": "en",
}

TRANSLATIONS = {}


def normalize_language(language):
    if language is None:
        return DEFAULT_CONFIG["language"]
    return LANGUAGE_ALIASES.get(str(language).strip().lower(), DEFAULT_CONFIG["language"])


def tr(language, key):
    language = normalize_language(language)
    fallback = TRANSLATIONS.get(DEFAULT_CONFIG["language"], {})
    return TRANSLATIONS.get(language, fallback).get(key, fallback.get(key, key))


def startup_launch_requested():
    return "--startup" in sys.argv


def command_line_language():
    args = sys.argv[1:]
    for index, arg in enumerate(args):
        if arg.startswith("--language="):
            return normalize_language(arg.split("=", 1)[1])
        if arg.startswith("--lang="):
            return normalize_language(arg.split("=", 1)[1])
        if arg in ("--language", "--lang") and index + 1 < len(args):
            return normalize_language(args[index + 1])
    return None


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def asset_path(name):
    path = os.path.join(base_dir(), name)
    if os.path.exists(path):
        return path

    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        bundled_path = os.path.join(bundle_dir, name)
        if os.path.exists(bundled_path):
            return bundled_path

    return path


def load_translations():
    translations = {}
    for language in LANGUAGE_NAMES:
        path = asset_path(os.path.join("locales", f"{language}.json"))
        try:
            with open(path, "r", encoding="utf-8") as fh:
                translations[language] = json.load(fh)
        except (OSError, json.JSONDecodeError):
            translations[language] = {}

    fallback = translations.get(DEFAULT_CONFIG["language"], {})
    for language, values in translations.items():
        translations[language] = {**fallback, **values}
    return translations


TRANSLATIONS = load_translations()


def config_path():
    return asset_path(CONFIG_NAME)


def installer_language_path():
    return asset_path(INSTALLER_LANGUAGE_NAME)


def load_installer_language():
    path = installer_language_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return normalize_language(data.get("language"))


def startup_dir():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise OSError(tr(DEFAULT_CONFIG["language"], "startup_appdata_error"))
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def startup_script_path():
    return os.path.join(startup_dir(), "PatoRecordatorio.cmd")


def installer_startup_shortcut_path():
    return os.path.join(startup_dir(), "Pato Recordatorio.lnk")


def startup_script_contents():
    if getattr(sys, "frozen", False):
        target = os.path.abspath(sys.executable)
        return f'@echo off\r\nstart "" "{target}" --startup\r\n'

    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    script = os.path.abspath(__file__)
    return f'@echo off\r\nstart "" "{pythonw}" "{script}" --startup\r\n'


def set_start_with_windows(enabled):
    path = startup_script_path()
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(startup_script_contents())
        return

    for startup_path in (path, installer_startup_shortcut_path()):
        if os.path.exists(startup_path):
            os.remove(startup_path)


def is_start_with_windows_enabled():
    try:
        return os.path.exists(startup_script_path()) or os.path.exists(installer_startup_shortcut_path())
    except OSError:
        return False


def load_config():
    config = DEFAULT_CONFIG.copy()
    path = config_path()
    config_exists = os.path.exists(path)
    if config_exists:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            config.update(data)

    config["interval_minutes"] = max(1, int(config.get("interval_minutes", DEFAULT_CONFIG["interval_minutes"])))
    config["travel_duration_ms"] = max(1000, int(config.get("travel_duration_ms", DEFAULT_CONFIG["travel_duration_ms"])))
    config["message"] = str(config.get("message", DEFAULT_CONFIG["message"])).strip() or DEFAULT_CONFIG["message"]
    installer_language = None if config_exists else load_installer_language()
    config["language"] = normalize_language(
        command_line_language() or installer_language or config.get("language", DEFAULT_CONFIG["language"])
    )
    config["start_with_windows"] = bool(config.get("start_with_windows", DEFAULT_CONFIG["start_with_windows"]))
    config["minimize_to_tray"] = bool(config.get("minimize_to_tray", DEFAULT_CONFIG["minimize_to_tray"]))
    return config


def save_config(config):
    with open(config_path(), "w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)


def icon_png_path():
    return asset_path(ICON_PNG_NAME)


def icon_ico_path():
    return asset_path(ICON_ICO_NAME)


def ensure_app_icon():
    png_path = icon_png_path()
    ico_path = icon_ico_path()

    if os.path.exists(png_path) and os.path.exists(ico_path):
        return png_path, ico_path

    source_path = asset_path(TRANSPARENT_NAME)
    if not os.path.exists(source_path):
        source_path = asset_path(GIF_NAME)

    try:
        image = Image.open(source_path)
        if getattr(image, "is_animated", False):
            image.seek(0)
        duck = image.convert("RGBA")
    except OSError:
        duck = Image.new("RGBA", (128, 128), (0, 0, 0, 0))

    icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    badge = Image.new("RGBA", (256, 256), (0, 0, 0, 0))

    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((24, 30, 238, 244), fill=(0, 0, 0, 55))

    badge_draw = ImageDraw.Draw(badge)
    badge_draw.ellipse((18, 18, 234, 234), fill=(255, 228, 122, 255), outline=(45, 33, 13, 255), width=8)
    badge_draw.ellipse((40, 38, 214, 120), fill=(255, 246, 196, 90))

    duck.thumbnail((150, 150), Image.Resampling.NEAREST)
    duck_x = (256 - duck.width) // 2 - 4
    duck_y = (256 - duck.height) // 2 + 14

    icon.alpha_composite(shadow)
    icon.alpha_composite(badge)
    icon.alpha_composite(duck, (duck_x, duck_y))

    icon.save(png_path)
    icon.save(ico_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    return png_path, ico_path


class DuckReminder:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.pet = None
        self.canvas = None
        self.spawn_job = None
        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()

        self.duck_frames_right = []
        self.duck_frames_left = []
        self.duck_width = 0
        self.duck_height = 0
        self.duck_frame_count = 0
        self.pet_width = 520
        self.pet_height = 180
        self.duck_x = 40
        self.duck_y = BANNER_H + 16

        self.load_duck_frames()

    @property
    def message(self):
        return self.config["message"]

    @property
    def interval_ms(self):
        return self.config["interval_minutes"] * 60 * 1000

    @property
    def travel_duration_ms(self):
        return self.config["travel_duration_ms"]

    def update_config(self, config):
        self.config = config
        self.cancel_next_spawn()
        self.schedule_next_spawn()

    def schedule_next_spawn(self, delay_ms=None):
        self.cancel_next_spawn()
        delay = self.interval_ms if delay_ms is None else max(0, int(delay_ms))
        self.spawn_job = self.root.after(delay, self.spawn_duck)

    def cancel_next_spawn(self):
        if self.spawn_job is not None:
            self.root.after_cancel(self.spawn_job)
            self.spawn_job = None

    def remove_solid_background(self, image):
        rgba = image.convert("RGBA")
        pixels = rgba.load()
        bg = rgba.getpixel((0, 0))
        width, height = rgba.size
        queue = deque()
        visited = set()

        def is_bg(pixel):
            return (
                abs(pixel[0] - bg[0]) <= BACKGROUND_TOLERANCE
                and abs(pixel[1] - bg[1]) <= BACKGROUND_TOLERANCE
                and abs(pixel[2] - bg[2]) <= BACKGROUND_TOLERANCE
            )

        for x in range(width):
            queue.append((x, 0))
            queue.append((x, height - 1))
        for y in range(height):
            queue.append((0, y))
            queue.append((width - 1, y))

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if not (0 <= x < width and 0 <= y < height):
                continue

            pixel = pixels[x, y]
            if not is_bg(pixel):
                continue

            pixels[x, y] = (pixel[0], pixel[1], pixel[2], 0)
            queue.append((x + 1, y))
            queue.append((x - 1, y))
            queue.append((x, y + 1))
            queue.append((x, y - 1))

        return rgba

    def load_duck_frames(self):
        gif_path = asset_path(GIF_NAME)
        output_path = asset_path(TRANSPARENT_NAME)

        try:
            image = Image.open(gif_path)
        except OSError:
            return

        frames = []
        durations = []
        for frame in ImageSequence.Iterator(image):
            transparent = self.remove_solid_background(frame)
            if DUCK_SCALE != 1.0:
                new_size = (
                    max(1, int(round(transparent.width * DUCK_SCALE))),
                    max(1, int(round(transparent.height * DUCK_SCALE))),
                )
                transparent = transparent.resize(new_size, Image.Resampling.NEAREST)
            frames.append(transparent.copy())
            durations.append(frame.info.get("duration", image.info.get("duration", 100)))

        if not frames:
            return

        crop_box = None
        for frame in frames:
            bbox = frame.getbbox()
            if bbox is None:
                continue
            if crop_box is None:
                crop_box = list(bbox)
            else:
                crop_box[0] = min(crop_box[0], bbox[0])
                crop_box[1] = min(crop_box[1], bbox[1])
                crop_box[2] = max(crop_box[2], bbox[2])
                crop_box[3] = max(crop_box[3], bbox[3])

        if crop_box is not None:
            frames = [frame.crop(tuple(crop_box)) for frame in frames]

        try:
            save_kwargs = {}
            if len(frames) > 1:
                save_kwargs = {
                    "save_all": True,
                    "append_images": frames[1:],
                    "duration": durations,
                    "loop": image.info.get("loop", 0),
                    "disposal": 2,
                }
            frames[0].save(output_path, **save_kwargs)
        except OSError:
            pass

        self.duck_frames_left = [ImageTk.PhotoImage(frame) for frame in frames]
        self.duck_frames_right = [
            ImageTk.PhotoImage(frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT))
            for frame in frames
        ]
        self.duck_frame_count = len(self.duck_frames_right)
        self.duck_width = self.duck_frames_right[0].width()
        self.duck_height = self.duck_frames_right[0].height()
        self.pet_width = max(BANNER_W + 80, self.duck_width + 80)
        self.pet_height = self.duck_height + BANNER_H + 40
        self.duck_x = max(24, (self.pet_width - self.duck_width) // 2)
        self.duck_y = BANNER_H + 16

    def spawn_duck_now(self):
        self.cancel_next_spawn()
        self.spawn_duck()

    def spawn_duck(self):
        self.spawn_job = None
        if self.pet is not None:
            return

        self.pet = tk.Toplevel(self.root)
        self.pet.overrideredirect(True)
        self.pet.attributes("-topmost", True)

        transparent_color = "magenta"
        self.pet.config(bg=transparent_color)
        try:
            self.pet.wm_attributes("-transparentcolor", transparent_color)
        except tk.TclError:
            pass

        width = self.pet_width
        height = self.pet_height
        self.direction = random.choice([1, -1])

        y = random.randint(80, max(80, self.screen_h - height - 40))
        if self.direction == 1:
            self.start_x = -width
            self.end_x = self.screen_w
        else:
            self.start_x = self.screen_w
            self.end_x = -width

        self.current_x = self.start_x
        self.base_y = y
        self.total_frames = max(1, int((self.travel_duration_ms / 1000) * FPS))
        self.frame = 0

        self.pet.geometry(f"{width}x{height}+{int(self.current_x)}+{int(self.base_y)}")

        self.canvas = tk.Canvas(
            self.pet,
            width=width,
            height=height,
            bg=transparent_color,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()
        self.animate()

    def animate(self):
        if self.pet is None:
            return

        self.canvas.delete("all")
        progress = self.frame / self.total_frames
        self.current_x = self.start_x + (self.end_x - self.start_x) * progress
        bob = math.sin(self.frame * 0.45) * 3

        self.pet.geometry(
            f"{self.pet_width}x{self.pet_height}+{int(self.current_x)}+{int(self.base_y + bob)}"
        )

        if self.direction == 1:
            self.draw_scene_left_to_right()
        else:
            self.draw_scene_right_to_left()

        self.frame += 1
        if self.frame <= self.total_frames:
            self.pet.after(int(1000 / FPS), self.animate)
        else:
            self.destroy_pet()
            self.schedule_next_spawn()

    def destroy_pet(self):
        if self.pet is not None:
            self.pet.destroy()
            self.pet = None
            self.canvas = None

    def draw_sprite(self, x, y, facing_right=True):
        if self.duck_frame_count:
            frames = self.duck_frames_right if facing_right else self.duck_frames_left
            frame = frames[self.frame % self.duck_frame_count]
            self.canvas.create_image(x, y, image=frame, anchor="nw")

    def draw_banner(self, duck_x, duck_y, facing_right=True):
        body_center_x = duck_x + (self.duck_width * 0.5 if self.duck_width else 51)
        banner_x0 = body_center_x - BANNER_W / 2
        banner_y0 = duck_y - BANNER_H - 8
        skew = 8 if facing_right else -8

        pole_bottom = duck_y + 56
        pole_top = banner_y0 + BANNER_H - 4
        self.canvas.create_line(body_center_x, pole_top, body_center_x, pole_bottom, width=4, fill="#5c3b1e")
        self.canvas.create_polygon(
            banner_x0,
            banner_y0,
            banner_x0 + BANNER_W,
            banner_y0 + skew,
            banner_x0 + BANNER_W,
            banner_y0 + BANNER_H + skew,
            banner_x0,
            banner_y0 + BANNER_H,
            fill="#fff7b2",
            outline="black",
            width=3,
        )
        self.canvas.create_text(
            banner_x0 + BANNER_W / 2,
            banner_y0 + BANNER_H / 2 + skew * 0.25,
            text=self.message,
            font=("Arial", 14, "bold"),
            fill="black",
            width=BANNER_W - 24,
            justify="center",
        )

    def draw_scene_left_to_right(self):
        self.draw_banner(self.duck_x, self.duck_y, facing_right=True)
        self.draw_sprite(self.duck_x, self.duck_y, facing_right=True)

    def draw_scene_right_to_left(self):
        self.draw_banner(self.duck_x, self.duck_y, facing_right=False)
        self.draw_sprite(self.duck_x, self.duck_y, facing_right=False)


class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self.root.geometry("440x410")
        self.root.resizable(False, False)
        self.tray_icon = None
        self.window_icon = None
        self.main_frame = None
        self.launched_from_startup = startup_launch_requested()
        self.startup_taskbar_minimize_pending = False
        if self.launched_from_startup:
            self.root.withdraw()

        self.config = load_config()
        self.config["start_with_windows"] = self.config["start_with_windows"] or is_start_with_windows_enabled()
        if self.config["start_with_windows"]:
            set_start_with_windows(True)
        if command_line_language() is not None or (not os.path.exists(config_path()) and load_installer_language() is not None):
            try:
                save_config(self.config)
            except OSError:
                pass
        self.icon_png, self.icon_ico = ensure_app_icon()
        self.reminder = DuckReminder(root, self.config)

        self.interval_var = tk.StringVar(value=str(self.config["interval_minutes"]))
        self.duration_var = tk.StringVar(value=str(self.config["travel_duration_ms"] // 1000))
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES[self.config["language"]])
        self.startup_var = tk.BooleanVar(value=self.config["start_with_windows"])
        self.minimize_to_tray_var = tk.BooleanVar(value=self.config["minimize_to_tray"])
        self.status_var = tk.StringVar(value=self.text("status_ready"))

        self.root.title(self.text("app_title"))
        self.build_ui()
        self.apply_window_icon()
        self.setup_tray_icon()
        self.reminder.schedule_next_spawn(delay_ms=3000)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Unmap>", self.on_minimize)
        if self.launched_from_startup:
            self.root.after(0, self.start_hidden_from_startup)

    def text(self, key):
        return tr(self.config.get("language", DEFAULT_CONFIG["language"]), key)

    def selected_language(self):
        return normalize_language(LANGUAGE_CODES_BY_NAME.get(self.language_var.get(), self.config["language"]))

    def current_message_text(self):
        if hasattr(self, "message_entry"):
            return self.message_entry.get("1.0", "end").strip()
        return self.config["message"]

    def apply_language_change(self, language, persist=True):
        language = normalize_language(language)
        if language == self.config["language"]:
            return

        current_message = self.current_message_text() or self.config["message"]
        self.config = {**self.config, "language": language, "message": current_message}
        self.reminder.update_config(self.config)
        self.status_var.set(self.text("status_ready"))
        self.root.title(self.text("app_title"))
        self.build_ui()
        self.refresh_tray_icon()
        if persist:
            save_config(self.config)

    def on_language_selected(self, event=None):
        try:
            self.apply_language_change(self.selected_language())
        except OSError as exc:
            messagebox.showerror(tr(self.selected_language(), "save_error_title"), str(exc))

    def build_ui(self):
        if self.main_frame is not None:
            self.main_frame.destroy()

        main = ttk.Frame(self.root, padding=16)
        self.main_frame = main
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text=self.text("settings_title"), font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text=self.text("settings_subtitle"),
            wraplength=395,
        )
        subtitle.pack(anchor="w", pady=(6, 16))

        form = ttk.Frame(main)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text=self.text("interval_label")).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Spinbox(form, from_=1, to=240, textvariable=self.interval_var, width=10).grid(
            row=0, column=1, sticky="w", pady=6
        )

        ttk.Label(form, text=self.text("duration_label")).grid(row=1, column=0, sticky="w", pady=6)
        ttk.Spinbox(form, from_=1, to=120, textvariable=self.duration_var, width=10).grid(
            row=1, column=1, sticky="w", pady=6
        )

        ttk.Label(form, text=self.text("language_label")).grid(row=2, column=0, sticky="w", pady=6)
        language_combo = ttk.Combobox(
            form,
            textvariable=self.language_var,
            values=list(LANGUAGE_CODES_BY_NAME.keys()),
            state="readonly",
            width=12,
        )
        language_combo.grid(row=2, column=1, sticky="w", pady=6)
        language_combo.bind("<<ComboboxSelected>>", self.on_language_selected)

        ttk.Label(form, text=self.text("message_label")).grid(row=3, column=0, sticky="nw", pady=6)
        self.message_entry = tk.Text(main, height=4, width=40, font=("Segoe UI", 11))
        self.message_entry.pack(fill="x", pady=(4, 12))
        self.message_entry.insert("1.0", self.config["message"])

        options = ttk.Frame(main)
        options.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(options, text=self.text("start_with_windows"), variable=self.startup_var).pack(anchor="w")
        ttk.Checkbutton(
            options,
            text=self.text("minimize_to_tray"),
            variable=self.minimize_to_tray_var,
        ).pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(4, 12))
        ttk.Button(buttons, text=self.text("save_changes"), command=self.save_settings).pack(side="left")
        ttk.Button(buttons, text=self.text("preview_now"), command=self.preview_now).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text=self.text("restore"), command=self.restore_defaults).pack(side="left", padx=(8, 0))

        info = ttk.Label(
            main,
            text=self.text("build_info"),
            wraplength=395,
            foreground="#555555",
        )
        info.pack(anchor="w", pady=(6, 10))

        status = ttk.Label(main, textvariable=self.status_var, wraplength=395, foreground="#1f5f3b")
        status.pack(anchor="w")

    def read_form_config(self):
        language = self.selected_language()
        try:
            interval_minutes = max(1, int(self.interval_var.get().strip()))
            travel_duration_ms = max(1000, int(float(self.duration_var.get().strip()) * 1000))
        except ValueError:
            raise ValueError(tr(language, "number_error")) from None
        message = self.message_entry.get("1.0", "end").strip()
        if not message:
            raise ValueError(tr(language, "empty_message_error"))
        return {
            "interval_minutes": interval_minutes,
            "travel_duration_ms": travel_duration_ms,
            "message": message,
            "language": language,
            "start_with_windows": self.startup_var.get(),
            "minimize_to_tray": self.minimize_to_tray_var.get(),
        }

    def save_settings(self):
        try:
            new_config = self.read_form_config()
            set_start_with_windows(new_config["start_with_windows"])
            save_config(new_config)
        except ValueError as exc:
            messagebox.showerror(tr(self.selected_language(), "invalid_config_title"), str(exc))
            return
        except OSError as exc:
            messagebox.showerror(tr(self.selected_language(), "save_error_title"), str(exc))
            return

        language_changed = new_config["language"] != self.config["language"]
        self.config = new_config
        self.reminder.update_config(new_config)
        self.status_var.set(self.text("status_saved"))
        if language_changed:
            self.root.title(self.text("app_title"))
            self.build_ui()
            self.refresh_tray_icon()

    def preview_now(self):
        try:
            new_config = self.read_form_config()
        except ValueError as exc:
            messagebox.showerror(tr(self.selected_language(), "invalid_config_title"), str(exc))
            return

        language_changed = new_config["language"] != self.config["language"]
        self.config = new_config
        self.reminder.update_config(new_config)
        self.reminder.spawn_duck_now()
        self.status_var.set(self.text("status_preview"))
        if language_changed:
            self.root.title(self.text("app_title"))
            self.build_ui()
            self.refresh_tray_icon()

    def restore_defaults(self):
        self.interval_var.set(str(DEFAULT_CONFIG["interval_minutes"]))
        self.duration_var.set(str(DEFAULT_CONFIG["travel_duration_ms"] // 1000))
        language = self.selected_language()
        self.message_entry.delete("1.0", "end")
        self.message_entry.insert("1.0", tr(language, "default_message"))
        self.startup_var.set(is_start_with_windows_enabled())
        self.minimize_to_tray_var.set(DEFAULT_CONFIG["minimize_to_tray"])
        self.status_var.set(tr(language, "status_restored"))

    def setup_tray_icon(self):
        tray_image = self.create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem(self.text("tray_show"), self.tray_show_window, default=True),
            pystray.MenuItem(self.text("tray_spawn_now"), self.tray_spawn_now),
            pystray.MenuItem(self.text("tray_quit"), self.tray_quit),
        )
        self.tray_icon = pystray.Icon("pato_recordatorio", tray_image, self.text("app_title"), menu)
        self.tray_icon.run_detached()

    def refresh_tray_icon(self):
        if self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None
        self.setup_tray_icon()

    def create_tray_image(self):
        image = Image.open(self.icon_png).convert("RGBA")
        return image.resize((64, 64), Image.Resampling.LANCZOS)

    def apply_window_icon(self):
        try:
            self.window_icon = ImageTk.PhotoImage(Image.open(self.icon_png))
            self.root.iconphoto(True, self.window_icon)
            if os.path.exists(self.icon_ico):
                self.root.iconbitmap(self.icon_ico)
        except Exception:
            self.window_icon = None

    def tray_show_window(self, icon=None, item=None):
        self.root.after(0, self.show_window)

    def tray_spawn_now(self, icon=None, item=None):
        self.root.after(0, self.preview_now)

    def tray_quit(self, icon=None, item=None):
        self.root.after(0, self.force_exit)

    def show_window(self):
        self.startup_taskbar_minimize_pending = False
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def start_hidden_from_startup(self):
        self.startup_taskbar_minimize_pending = True
        self.status_var.set(self.text("status_startup_minimized"))
        self.root.withdraw()
        self.root.after(500, self.finish_startup_minimize)

    def finish_startup_minimize(self):
        self.startup_taskbar_minimize_pending = False

    def hide_to_tray(self):
        self.root.withdraw()
        self.status_var.set(self.text("status_tray"))

    def on_minimize(self, event):
        if self.startup_taskbar_minimize_pending:
            return
        if self.root.state() == "iconic" and self.minimize_to_tray_var.get():
            self.root.after(0, self.hide_to_tray)

    def on_close(self):
        if self.minimize_to_tray_var.get():
            self.hide_to_tray()
            return
        self.force_exit()

    def force_exit(self):
        self.reminder.cancel_next_spawn()
        self.reminder.destroy_pet()
        if self.tray_icon is not None:
            self.tray_icon.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    SettingsWindow(root)
    root.mainloop()
