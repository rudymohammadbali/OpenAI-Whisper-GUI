import os
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor

import customtkinter as ctk
import pynvml
import torch
import whisper
from PIL import Image
from customtkinter import filedialog as fd
from whisper.utils import get_writer

from assets.ctkdropdown import CTkScrollableDropdownFrame
from assets.ctkmessagebox import CTkMessagebox

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

APP_LOGO = f"{CURRENT_PATH}\\assets\\icons\\logo.ico"
APP_VERSION = "Version 20231217"
ICONS = {
    "theme": ctk.CTkImage(light_image=Image.open(f"{CURRENT_PATH}\\assets\\icons\\theme_black.png"),
                          dark_image=Image.open(f"{CURRENT_PATH}\\assets\\icons\\theme_white.png"), size=(25, 25)),
    "github": ctk.CTkImage(light_image=Image.open(f"{CURRENT_PATH}\\assets\\icons\\github.png"),
                           dark_image=Image.open(f"{CURRENT_PATH}\\assets\\icons\\github.png"), size=(25, 25))
}

LANGUAGE_VALUES = [
    "Auto Detection",
    "English",
    "Chinese",
    "German",
    "Spanish",
    "Russian",
    "Korean",
    "French",
    "Japanese",
    "Portuguese",
    "Turkish",
    "Polish",
    "Catalan",
    "Dutch",
    "Arabic",
    "Swedish",
    "Italian",
    "Indonesian",
    "Hindi",
    "Finnish",
    "Vietnamese",
    "Hebrew",
    "Ukrainian",
    "Greek",
    "Malay",
    "Czech",
    "Romanian",
    "Danish",
    "Hungarian",
    "Tamil",
    "Norwegian",
    "Thai",
    "Urdu",
    "Croatian",
    "Bulgarian",
    "Lithuanian",
    "Latin",
    "Maori",
    "Malayalam",
    "Welsh",
    "Slovak",
    "Telugu",
    "Persian",
    "Latvian",
    "Bengali",
    "Serbian",
    "Azerbaijani",
    "Slovenian",
    "Kannada",
    "Estonian",
    "Macedonian",
    "Breton",
    "Basque",
    "Icelandic",
    "Armenian",
    "Nepali",
    "Mongolian",
    "Bosnian",
    "Kazakh",
    "Albanian",
    "Swahili",
    "Galician",
    "Marathi",
    "Punjabi",
    "Sinhala",
    "Khmer",
    "Shona",
    "Yoruba",
    "Somali",
    "Afrikaans",
    "Occitan",
    "Georgian",
    "Belarusian",
    "Tajik",
    "Sindhi",
    "Gujarati",
    "Amharic",
    "Yiddish",
    "Lao",
    "Uzbek",
    "Faroese",
    "Haitian creole",
    "Pashto",
    "Turkmen",
    "Nynorsk",
    "Maltese",
    "Sanskrit",
    "Luxembourgish",
    "Myanmar",
    "Tibetan",
    "Tagalog",
    "Malagasy",
    "Assamese",
    "Tatar",
    "Hawaiian",
    "Lingala",
    "Hausa",
    "Bashkir",
    "Javanese",
    "Sundanese"
]

FONTS = {
    "title_bold": ("Inter", 24, "bold"),
    "title": ("Inter", 22, "normal"),
    "subtitle_bold": ("Inter", 18, "bold"),
    "btn": ("Inter", 15, "normal"),
    "normal": ("Inter", 14, "normal"),
    "small": ("Inter", 12, "normal"),
}

DROPDOWN = {
    "font": FONTS["small"],
    "corner_radius": 2,
    "alpha": 1.0,
    "frame_corner_radius": 5,
    "x": 0,
    "justify": "center"
}


class CheckRequirements:
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.check_cuda = torch.cuda.is_available()

    def check_memory(self):
        if self.check_cuda:
            gpu_memory = self.get_gpu_memory()
            free_memory_gb = int(gpu_memory.free / (1024 ** 3))
            unsupported_models = self.check_memory_requirements(free_memory_gb)
            return unsupported_models if unsupported_models else None
        else:
            return False

    def get_gpu_memory(self):
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_id)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        return info

    @staticmethod
    def check_memory_requirements(free_memory_gb):
        memory_requirements = {
            10: ["Large", "Large-v1", "Large-v2", "Large-v3"],
            5: "Medium",
            2: "Small",
            1: ["Base", "Tiny"],
        }
        unsupported_models = []

        for requirement, models in memory_requirements.items():
            if free_memory_gb < requirement:
                if isinstance(models, list):
                    unsupported_models.extend(models)
                else:
                    unsupported_models.append(models)
        return unsupported_models


def open_github():
    webbrowser.open("https://github.com/rudymohammadbali")


def change_theme(new_theme):
    ctk.set_appearance_mode(new_theme)


class WhisperGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OpenAI Whisper GUI")
        self.iconbitmap(APP_LOGO)
        self.geometry("1000x500")
        self.minsize(1000, 500)

        self.center_window(1000, 500)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=1, column=0, sticky="ns", padx=10, pady=(0, 10))

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=(0, 10))

        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.file_path = None
        self.result = None
        self.device = None
        self.lang = None
        self.save_btn = None
        self.subtitle_btn = None
        self.start_btn = None
        self.timestamps_checkbox = None
        self.textbox = None
        self.upload_btn = None
        self.device_option = None
        self.task_option = None
        self.language_option = None
        self.model_option = None
        self.theme_option = None
        self.device_dropdown = None
        self.task_dropdown = None
        self.language_dropdown = None
        self.model_dropdown = None
        self.theme_dropdown = None
        self.thread_pool = ThreadPoolExecutor(max_workers=5)

        check_requirements = CheckRequirements()
        result = check_requirements.check_memory()
        models = ["Tiny", "Base", "Small", "Medium", "Large", "Large-v1", "Large-v2", "Large-v3"]
        self.models_value = []

        if result:
            unmet_models = [
                model for model in models if any(model in message for message in result)
            ]

            met_models = [model for model in models if model not in unmet_models]
            self.models_value = met_models

            self.device_value = ["GPU", "CPU"]

            self.after(5000, lambda: CTkMessagebox(
                master=self,
                title="INFO",
                message=f"GPU Memory requirements not met for the following models: \n{unmet_models}",
                corner_radius=8
            ))
        else:
            self.after(5000, lambda: CTkMessagebox(
                master=self,
                title="INFO",
                message="CUDA not found",
                corner_radius=8
            ))
            self.device_value = ["CPU"]
            self.models_value = models

        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        self.top_widgets()
        self.left_widgets()
        self.right_widgets()
        self.bottom_widgets()

    def top_widgets(self):
        self.top_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self.top_frame, text="Audio Transcriber and Translator", font=FONTS["title_bold"])
        title.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        theme_label = ctk.CTkLabel(self.top_frame, text="", image=ICONS["theme"])
        theme_label.grid(row=0, column=1, padx=10, pady=20, sticky="e")

        values = ["System", "Dark", "Light"]
        self.theme_option = ctk.CTkOptionMenu(self.top_frame)
        self.theme_option.grid(row=0, column=2, padx=(10, 20), pady=20, sticky="e")
        self.theme_dropdown = CTkScrollableDropdownFrame(self.theme_option, values=values, command=change_theme,
                                                         **DROPDOWN)
        self.theme_option.set("System")

    def left_widgets(self):
        title = ctk.CTkLabel(self.left_frame, text="Settings", font=FONTS["subtitle_bold"])
        title.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        model_label = ctk.CTkLabel(self.left_frame, text="Model Size", anchor="w", font=FONTS["normal"])
        model_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.model_option = ctk.CTkOptionMenu(self.left_frame)
        self.model_option.grid(row=1, column=1, padx=20, pady=10, sticky="e")
        self.model_dropdown = CTkScrollableDropdownFrame(self.model_option, values=self.models_value, **DROPDOWN)
        self.model_option.set(self.models_value[0])

        language_label = ctk.CTkLabel(self.left_frame, text="Language", anchor="w", font=FONTS["normal"])
        language_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.language_option = ctk.CTkOptionMenu(self.left_frame)
        self.language_dropdown = CTkScrollableDropdownFrame(self.language_option, values=LANGUAGE_VALUES, **DROPDOWN)
        self.language_option.grid(row=2, column=1, padx=20, pady=10, sticky="e")
        self.language_option.set("Auto Detection")

        task_label = ctk.CTkLabel(self.left_frame, text="Task", anchor="w", font=FONTS["normal"])
        task_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        task_values = ["Transcribe", "Translate"]
        self.task_option = ctk.CTkOptionMenu(self.left_frame)
        self.task_option.grid(row=3, column=1, padx=20, pady=10, sticky="e")
        self.task_dropdown = CTkScrollableDropdownFrame(self.task_option, values=task_values, **DROPDOWN)
        self.task_option.set("Transcribe")

        device_label = ctk.CTkLabel(self.left_frame, text="Device", anchor="w", font=FONTS["normal"])
        device_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.device_option = ctk.CTkOptionMenu(self.left_frame)
        self.device_option.grid(row=4, column=1, padx=20, pady=10, sticky="e")
        self.device_dropdown = CTkScrollableDropdownFrame(self.device_option, values=self.device_value, **DROPDOWN)
        self.device_option.set(self.device_value[0])

        self.upload_btn = ctk.CTkButton(self.left_frame, text="Choose File", command=self.select_file,
                                        font=FONTS["btn"], height=30)
        self.upload_btn.grid(row=5, column=0, padx=20, pady=20, sticky="sew", columnspan=2)

    def right_widgets(self):
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(self.right_frame, wrap="word")
        self.textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", columnspan=5)

        self.timestamps_checkbox = ctk.CTkCheckBox(self.right_frame, text="Show timestamps", onvalue=True,
                                                   offvalue=False, font=FONTS["normal"])

        self.timestamps_checkbox.grid(row=1, column=0, padx=20, pady=20, sticky="w")

        self.start_btn = ctk.CTkButton(self.right_frame, text="Start", command=self.start_task, font=FONTS["btn"])
        self.start_btn.grid(row=1, column=2, padx=10, pady=20)

        self.subtitle_btn = ctk.CTkButton(self.right_frame, text="Add Subtitles", command=self.start_subtask,
                                          font=FONTS["btn"])
        self.subtitle_btn.grid(row=1, column=3, padx=10, pady=20)

        self.save_btn = ctk.CTkButton(self.right_frame, text="Save", command=self.save_text, font=FONTS["btn"])
        self.save_btn.grid(row=1, column=4, padx=10, pady=20)

    def bottom_widgets(self):
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        version_label = ctk.CTkLabel(self.bottom_frame, text=APP_VERSION, font=FONTS["small"])
        version_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        github_btn = ctk.CTkButton(self.bottom_frame, text="Github", command=open_github, image=ICONS["github"],
                                   compound="left", font=FONTS["btn"])
        github_btn.grid(row=0, column=1, padx=20, pady=10, sticky="e")

    def start_task(self):
        if self.return_data():
            CTkMessagebox(self, title="Transcribing...", message="Please wait while transcribe process to finished.",
                          corner_radius=8)
            file_path, model, language, task, device, show_time = self.return_data()
            self.thread_pool.submit(
                self.run_transcribe,
                file_path,
                model,
                language,
                task,
                device,
                show_time,
            )

    def run_transcribe(self, file_path, model, language, task, device, show_time):
        try:
            self.disable_controller()
            fp16 = False

            if device == "cuda":
                fp16 = True

            load_model = whisper.load_model(model, device=device)

            if language == "auto detection":
                load_audio = whisper.load_audio(file_path)
                load_audio = whisper.pad_or_trim(load_audio)
                mel = whisper.log_mel_spectrogram(load_audio).to(load_model.device)

                _, probs = load_model.detect_language(mel)
                lang = max(probs, key=probs.get)
                self.lang = lang
                self.device = device

                result = load_model.transcribe(
                    file_path,
                    language=lang,
                    task=task,
                    fp16=fp16,
                )

            else:
                result = load_model.transcribe(file_path, language=language, task=task, fp16=fp16)

            if show_time:
                self.textbox.delete("0.0", "end")
                for segment in result["segments"]:
                    segment = "[%s --> %s]%s" % (
                        round(segment["start"], 2),
                        round(segment["end"], 2),
                        segment["text"],
                    )
                    self.textbox.insert("end", segment + "\n")

            else:
                text = result["text"].strip().capitalize()
                self.textbox.delete("0.0", "end")
                self.textbox.insert("end", text)

            self.result = result

            self.enable_controller()
        except:
            self.enable_controller()

    def start_subtask(self):
        if self.result and self.file_path:
            CTkMessagebox(self, title="INFO", message="Please wait while adding subtitles to the video.",
                          corner_radius=8)
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

            file_name = os.path.basename(file_path)
            dir_name = os.path.dirname(file_path)
            file_extension = os.path.splitext(file_path)

            temp_file_name = "temp_srt.srt"
            writer = get_writer("srt", ".")
            writer(self.result, temp_file_name, {"highlight_words": True, "max_line_count": 50, "max_line_width": 3})

            if file_extension[1] == ".mkv":
                os.system(
                    "ffmpeg -i {} -i {} -map 0 -map 1 -c copy -disposition:s:0 default -metadata:s:s:0 language={} {} -y".format(
                        '"' + self.file_path + '"',
                        temp_file_name,
                        self.lang,
                        os.path.join('"' + dir_name, file_name + '"'),
                    )
                )
            else:
                if self.device == "cuda":
                    os.system(
                        "ffmpeg -i {} -c:v h264_nvenc -vf subtitles={} {} -y".format(
                            '"' + self.file_path + '"',
                            temp_file_name,
                            os.path.join('"' + dir_name, file_name + '"'),
                        )
                    )
                else:
                    os.system(
                        "ffmpeg -i {} -vf subtitles={} {} -y".format(
                            '"' + self.file_path + '"',
                            temp_file_name,
                            os.path.join('"' + dir_name, file_name + '"'),
                        )
                    )

            os.remove(os.path.join(".", temp_file_name))
        else:
            CTkMessagebox(self, title="WARNING", message="No file is transcribed/selected.",
                          corner_radius=8, icon="warning")

    def return_data(self):
        if self.file_path:
            model = self.model_option.get().lower()
            language = self.language_option.get().lower()
            task = self.task_option.get().lower()
            device = self.device_option.get().lower()
            show_time = self.timestamps_checkbox.get()

            if language == "english" and model != "large":
                model += ".en"

            if language == "english":
                task = "transcribe"

            if device == "gpu":
                device = "cuda"

            return self.file_path, model, language, task, device, show_time

    def save_text(self):
        if self.result and self.file_path:
            og_file_name = os.path.basename(self.file_path)
            sep = "."
            og_file_name = og_file_name.split(sep, 1)[0]

            file_path = fd.asksaveasfilename(
                parent=self,
                initialfile=og_file_name,
                defaultextension=".txt",
                title="Export subtitle",
                filetypes=[
                    ("SubRip Subtitle file", "*.srt"),
                    ("text file", "*.txt"),
                    ("Web Video Text Tracks", "*.vtt"),
                    ("Tab-separated values", "*.tsv"),
                    ("JSON", "*.json"),
                    ("Save all extensions", "*.all"),
                ],
            )

            selected_extension = os.path.splitext(file_path)
            file_extension = selected_extension[1]

            if file_path:
                dir_name, get_file_name = os.path.split(file_path)

                if file_extension == ".srt":
                    writer = get_writer("srt", dir_name)
                    writer(self.result, self.file_path,
                           {"highlight_words": True, "max_line_count": 50, "max_line_width": 3})
                elif file_extension == ".txt":
                    txt_writer = get_writer("txt", dir_name)
                    txt_writer(self.result, self.file_path, {"highlight_words": True, "max_line_count": 50,
                                                             "max_line_width": 3})
                elif file_extension == ".vtt":
                    vtt_writer = get_writer("vtt", dir_name)
                    vtt_writer(self.result, self.file_path, {"highlight_words": True, "max_line_count": 50,
                                                             "max_line_width": 3})
                elif file_extension == ".tsv":
                    tsv_writer = get_writer("tsv", dir_name)
                    tsv_writer(self.result, self.file_path, {"highlight_words": True, "max_line_count": 50,
                                                             "max_line_width": 3})
                elif file_extension == ".json":
                    json_writer = get_writer("json", dir_name)
                    json_writer(self.result, self.file_path, {"highlight_words": True, "max_line_count": 50,
                                                              "max_line_width": 3})
                elif file_extension == ".all":
                    all_writer = get_writer("all", dir_name)
                    all_writer(self.result, self.file_path, {"highlight_words": True, "max_line_count": 50,
                                                             "max_line_width": 3})

        else:
            CTkMessagebox(self, title="WARNING", message="No file is transcribed/selected.",
                          corner_radius=8, icon="warning")

    def select_file(self):
        file_path = fd.askopenfilename(
            parent=self,
            title="Select Audio/Video File",
            filetypes=(
                (
                    ("All files", "*.*"),
                    ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.flv"),
                    ("Audiofile", "*.mp3 *.wav *.flac *.aac *.ogg *.wma *.m4a"),
                )
            ),
        )
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_path = file_path
            CTkMessagebox(self, title="INFO", message=f"Selected file name: {file_name}",
                          corner_radius=8)
        else:
            self.file_path = None
            CTkMessagebox(self, title="WARNING", message="No file is selected.",
                          corner_radius=8, icon="warning")

    def enable_controller(self):
        self.theme_dropdown.configure(state="normal")
        self.model_dropdown.configure(state="normal")
        self.language_dropdown.configure(state="normal")
        self.task_dropdown.configure(state="normal")
        self.device_dropdown.configure(state="normal")

        self.theme_option.configure(state="normal")
        self.start_btn.configure(state="normal")
        self.subtitle_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.timestamps_checkbox.configure(state="normal")
        self.upload_btn.configure(state="normal")
        self.model_option.configure(state="normal")
        self.language_option.configure(state="normal")
        self.task_option.configure(state="normal")
        self.device_option.configure(state="normal")

    def disable_controller(self):
        self.theme_dropdown.configure(state="disabled")
        self.model_dropdown.configure(state="disabled")
        self.language_dropdown.configure(state="disabled")
        self.task_dropdown.configure(state="disabled")
        self.device_dropdown.configure(state="disabled")

        self.theme_option.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        self.subtitle_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self.timestamps_checkbox.configure(state="disabled")
        self.upload_btn.configure(state="disabled")
        self.model_option.configure(state="disabled")
        self.language_option.configure(state="disabled")
        self.task_option.configure(state="disabled")
        self.device_option.configure(state="disabled")

    def center_window(self, window_width, window_height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

    def on_close(self):
        self.thread_pool.shutdown(wait=False)
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = WhisperGui()
    app.mainloop()
