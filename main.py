import os
import sys

import customtkinter as ctk
from customtkinter import filedialog as fd

from src.functions import APP_VERSION, ICONS, LANGUAGE_VALUES, FONTS, DROPDOWN, OPTION, BUTTONS, help_page, \
    reset_config, load_config, save_config, start_transcriber, start_writer, change_theme, start_subtitle
from src.widgets import CTkScrollableDropdownFrame, CTkMessagebox, CTkLoader, SettingsInterface

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = f"{CURRENT_PATH}\\src\\config.json"


class WhisperGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._on_startup()
        self._init_window()
        self._init_widgets()

        self.result = None
        self.file_path = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_startup(self):
        if not os.path.exists(CONFIG_FILE):
            reset_config(CONFIG_FILE)

        self.config = load_config(CONFIG_FILE)

        self.model = self.config["model"]
        self.language = self.config["language"]
        self.task = self.config["task"]
        self.device = self.config["device"]
        self.models_value = self.config["models"]
        device_value = self.config["cuda"]
        self.theme_value = self.config["theme"]

        if device_value:
            self.device_value = ["GPU", "CPU"]
        else:
            self.device_value = ["CPU"]

            self.after(5000, lambda: CTkMessagebox(
                master=self,
                title="INFO",
                message="CUDA not found",
                corner_radius=8
            ))

    def _init_window(self) -> None:
        self.title("OpenAI Whisper GUI")
        self.iconbitmap(f"{CURRENT_PATH}\\src\\icons\\logo.ico")
        self.geometry("1000x500")

        self.center_window(1000, 500)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        change_theme(self.theme_value)

    def _init_widgets(self) -> None:
        self._init_frames()
        self._top_widgets()
        self._left_widgets()
        self._right_widgets()
        self._bottom_widgets()

    def _init_frames(self) -> None:
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=1, column=0, sticky="ns", padx=2, pady=2)
        self.left_frame.grid_rowconfigure(5, weight=1)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(2, weight=1)

        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        self.bottom_frame.grid_columnconfigure(0, weight=1)

    def _top_widgets(self) -> None:
        title = ctk.CTkLabel(self.top_frame, text="Whisper GUI: Audio Transcription toolkit", font=FONTS["title"])
        title.grid(row=0, column=0, padx=10, pady=20, sticky="w")

        settings_btn = ctk.CTkButton(self.top_frame, text="", image=ICONS["settings"], width=50, height=20,
                                     command=self.show_settings)
        settings_btn.grid(row=0, column=1, padx=10, pady=20, sticky="e")

    def _left_widgets(self) -> None:
        title = ctk.CTkLabel(self.left_frame, text="Options", font=FONTS["subtitle"])
        title.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        model_label = ctk.CTkLabel(self.left_frame, text="Model Size", anchor="w", font=FONTS["small"])
        model_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.model_option = ctk.CTkOptionMenu(self.left_frame, **OPTION)
        self.model_option.grid(row=1, column=1, padx=20, pady=10, sticky="e")
        self.model_dropdown = CTkScrollableDropdownFrame(self.model_option, values=self.models_value, **DROPDOWN)
        self.model_option.set(self.model)

        language_label = ctk.CTkLabel(self.left_frame, text="Language", anchor="w", font=FONTS["small"])
        language_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.language_option = ctk.CTkOptionMenu(self.left_frame, **OPTION)
        self.language_dropdown = CTkScrollableDropdownFrame(self.language_option, values=LANGUAGE_VALUES, **DROPDOWN)
        self.language_option.grid(row=2, column=1, padx=20, pady=10, sticky="e")
        self.language_option.set(self.language)

        task_label = ctk.CTkLabel(self.left_frame, text="Task", anchor="w", font=FONTS["small"])
        task_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        task_values = ["Transcribe", "Translate"]
        self.task_option = ctk.CTkOptionMenu(self.left_frame, **OPTION)
        self.task_option.grid(row=3, column=1, padx=20, pady=10, sticky="e")
        self.task_dropdown = CTkScrollableDropdownFrame(self.task_option, values=task_values, **DROPDOWN, height=65)
        self.task_option.set(self.task)

        device_label = ctk.CTkLabel(self.left_frame, text="Device", anchor="w", font=FONTS["small"])
        device_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.device_option = ctk.CTkOptionMenu(self.left_frame, **OPTION)
        self.device_option.grid(row=4, column=1, padx=20, pady=10, sticky="e")
        self.device_dropdown = CTkScrollableDropdownFrame(self.device_option, values=self.device_value, **DROPDOWN,
                                                          height=65)
        self.device_option.set(self.device)

        self.upload_btn = ctk.CTkButton(self.left_frame, text="Choose File", command=self._select_file_callback,
                                        **BUTTONS)
        self.upload_btn.grid(row=5, column=0, padx=20, pady=20, sticky="sew", columnspan=2)

    def _right_widgets(self) -> None:
        self.textbox = ctk.CTkTextbox(self.right_frame, wrap="word", corner_radius=5, border_width=1, border_spacing=8,
                                      font=FONTS["normal"])
        self.textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", columnspan=3)

        self.start_btn = ctk.CTkButton(self.right_frame, text="Start", **BUTTONS, command=self.start_callback)
        self.start_btn.grid(row=1, column=0, padx=(10, 5), pady=(10, 20), sticky="e")
        self.start_btn.configure(state="disabled")

        self.subtitle_btn = ctk.CTkButton(self.right_frame, text="Add Subtitles", **BUTTONS,
                                          command=self.subtitle_callback)
        self.subtitle_btn.grid(row=1, column=1, padx=5, pady=(10, 20))
        self.subtitle_btn.configure(state="disabled")

        self.save_btn = ctk.CTkButton(self.right_frame, text="Save", **BUTTONS, command=self.save_callback)
        self.save_btn.grid(row=1, column=2, padx=(5, 10), pady=(10, 20), sticky="e")
        self.save_btn.configure(state="disabled")

    def _bottom_widgets(self) -> None:
        version_label = ctk.CTkLabel(self.bottom_frame, text=APP_VERSION, font=FONTS["small"])
        version_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        help_btn = ctk.CTkButton(self.bottom_frame, text="Get help", command=help_page, width=100, height=28,
                                 corner_radius=3, fg_color="transparent", border_width=1, hover=False,
                                 text_color=("black", "white"))
        help_btn.grid(row=0, column=1, padx=20, pady=10, sticky="e")

    def show_settings(self) -> None:
        SettingsInterface(self).grid(row=0, column=0, sticky="nsew", rowspan=3, columnspan=3, padx=250, pady=20)

    def subtitle_notification(self, msg: str) -> None:
        self.enable_controller()
        self.loader.stop_loader()
        CTkMessagebox(self, title="SUCCESS", message=f"Subtitles added to the video: {msg}",
                      corner_radius=8, icon="check")

    def show_results(self, result: dict) -> None:
        self.enable_controller()
        self.textbox.insert("0.0", result["text"].strip())
        self.result = result
        self.loader.stop_loader()

    def save_notification(self, msg: str) -> None:
        self.enable_controller()
        self.loader.stop_loader()
        CTkMessagebox(self, title="SUCCESS", message=msg,
                      corner_radius=8, icon="check")

    def save_callback(self) -> None:
        og_file_name = os.path.basename(self.file_path)
        sep = "."
        og_file_name = og_file_name.split(sep, 1)[0]
        file_path = fd.asksaveasfilename(
            parent=self,
            initialfile=og_file_name,
            defaultextension=".txt",
            title="Export subtitle as",
            filetypes=[
                ("SubRip Subtitle file", "*.srt"),
                ("text file", "*.txt"),
                ("Web Video Text Tracks", "*.vtt"),
                ("Tab-separated values", "*.tsv"),
                ("JSON", "*.json"),
                ("Save all extensions", "*.all"),
            ],
        )

        if file_path:
            self.disable_controller()
            self.loader = CTkLoader(self)
            options = {"output_dir": file_path, "result": self.result,
                       "audio_file": self.file_path}

            start_writer(options, self.save_notification)

    def subtitle_callback(self):
        og_file_name = os.path.basename(self.file_path)
        sep = "."
        og_file_name = og_file_name.split(sep, 1)[0]
        file_path = fd.asksaveasfilename(
            parent=self,
            initialfile=og_file_name + "-sub",
            defaultextension=".srt",
            title="Export subtitle",
            filetypes=[("MPEG-4", "*.mp4"), ("MKV", "*.mkv"), ("All", "*.*")],
        )
        if file_path:
            self.disable_controller()
            self.loader = CTkLoader(self)
            start_subtitle({"result": self.result, "audio": self.file_path, "output": file_path, "lang": self.language,
                            "device": self.device}, self.subtitle_notification)

    def start_callback(self) -> None:
        self.disable_controller()
        self.loader = CTkLoader(self)

        options = {"audio": self.file_path, "model": self.model_option.get().lower(),
                   "language": self.language_option.get().lower(), "task": self.task_option.get().lower(),
                   "device": self.device_option.get().lower()}

        start_transcriber(options, self.show_results)

    def _select_file_callback(self) -> None:
        file_path = fd.askopenfilename(
            parent=self,
            title="Select Audio/Video File",
            filetypes=(
                (
                    ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.flv"),
                    ("Audiofile", "*.mp3 *.wav *.flac *.aac *.ogg *.wma *.m4a"),
                )
            ),
        )
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_path = file_path
            self.start_btn.configure(state="normal")
            CTkMessagebox(self, title="INFO", message=f"Selected file name: {file_name}",
                          corner_radius=8)
        else:
            self.file_path = None
            self.start_btn.configure(state="disabled")
            CTkMessagebox(self, title="WARNING", message="No file is selected.",
                          corner_radius=8, icon="warning")

    def enable_controller(self) -> None:
        self.model_dropdown.configure(state="normal")
        self.language_dropdown.configure(state="normal")
        self.task_dropdown.configure(state="normal")
        self.device_dropdown.configure(state="normal")

        self.start_btn.configure(state="normal")
        self.subtitle_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.upload_btn.configure(state="normal")
        self.model_option.configure(state="normal")
        self.language_option.configure(state="normal")
        self.task_option.configure(state="normal")
        self.device_option.configure(state="normal")

    def disable_controller(self) -> None:
        self.model_dropdown.configure(state="disabled")
        self.language_dropdown.configure(state="disabled")
        self.task_dropdown.configure(state="disabled")
        self.device_dropdown.configure(state="disabled")

        self.start_btn.configure(state="disabled")
        self.subtitle_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self.upload_btn.configure(state="disabled")
        self.model_option.configure(state="disabled")
        self.language_option.configure(state="disabled")
        self.task_option.configure(state="disabled")
        self.device_option.configure(state="disabled")

    def center_window(self, window_width, window_height) -> None:
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

    def on_close(self) -> None:
        options = {
            "model": self.model_option.get(),
            "language": self.language_option.get(),
            "task": self.task_option.get(),
            "device": self.device_option.get(),
        }
        save_config(options, CONFIG_FILE)

        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = WhisperGui()
    app.mainloop()
