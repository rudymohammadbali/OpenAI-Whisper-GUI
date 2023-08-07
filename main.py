import os
import webbrowser
from concurrent.futures import ThreadPoolExecutor

import pynvml
import torch
import whisper
from whisper.utils import get_writer

import customtkinter as ctk
from customtkinter import filedialog as fd

from PIL import Image


app_version = "Version 1.1"
app_logo = "./icons/logo.ico"


def load_image(path, size):
    return ctk.CTkImage(Image.open(path), size=size)


image_info = {
    "clear_icon": {"path": "./icons/delete.png", "size": (20, 20)},
    "github_icon": {"path": "./icons/github.png", "size": (20, 20)},
    "warning_icon": {"path": "./icons/warning.png", "size": (50, 50)},
    "close_icon": {"path": "./icons/close-white.png", "size": (20, 20)},
    "exit_icon": {"path": "./icons/exit.png", "size": (20, 20)},
    "background": {"path": "./icons/background.jpg", "size": (500, 250)},
}


icons = {
    name: load_image(info["path"], info["size"]) for name, info in image_info.items()
}

clear_icon = icons["clear_icon"]
github_icon = icons["github_icon"]
warning_icon = icons["warning_icon"]
close_icon = icons["close_icon"]
exit_icon = icons["exit_icon"]
background = icons["background"]


custom_button = {
    "bg_color": "transparent",
    "fg_color": "#a52a2a",
    "text_color": "#ffffff",
    "hover_color": "#8d0d26",
    "text_color_disabled": "#a8a8a8",
    "corner_radius": 2,
}

custom_optionmenu = {
    "bg_color": "transparent",
    "fg_color": "#a52a2a",
    "text_color": "#ffffff",
    "text_color_disabled": "#a8a8a8",
    "button_color": "#8d0d26",
    "button_hover_color": "#800000",
    "dropdown_fg_color": "#a52a2a",
    "dropdown_hover_color": "#8d0d26",
    "dropdown_text_color": "#ffffff",
    "corner_radius": 2,
}


class CheckMemory:
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.check_cuda = torch.cuda.is_available()

    def check_memory(self):
        if self.check_cuda:
            gpu_memory = self._get_gpu_memory()
            free_memory_gb = int(gpu_memory.free / (1024**3))
            unsupported_models = self._check_memory_requirements(free_memory_gb)
            return unsupported_models if unsupported_models else None
        else:
            return False

    def _get_gpu_memory(self):
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_id)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        return info

    def _check_memory_requirements(self, free_memory_gb):
        memory_requirements = {
            10: "Large",
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


class Notification(ctk.CTkFrame):
    def __init__(self, master, text="", cl_btn=True, ex_btn=False, progress_bar=False):
        super().__init__(
            master,
            width=400,
            height=200,
            border_width=2,
            border_color="#a52a2a",
            corner_radius=5,
        )
        self.pack_propagate(0)

        self.master = master

        warning = ctk.CTkLabel(self, text="", image=warning_icon)
        warning.pack(padx=10, pady=10, side="top")

        message = ctk.CTkLabel(self, text=text)
        message.pack(padx=10, pady=10, fill="both", expand=True)

        if cl_btn:
            close_btn = ctk.CTkButton(
                self,
                text="Close",
                image=close_icon,
                command=self.hide_message,
                width=100,
                bg_color="transparent",
                fg_color="#a52a2a",
                text_color="#ffffff",
                hover_color="#8d0d26",
                text_color_disabled="#a8a8a8",
                corner_radius=2,
            )
            close_btn.pack(padx=10, pady=10, side="right")

        if ex_btn:
            exit_btn = ctk.CTkButton(
                self,
                text="Exit",
                image=exit_icon,
                command=self.master.destroy,
                width=100,
                bg_color="transparent",
                fg_color="#a52a2a",
                text_color="#ffffff",
                hover_color="#8d0d26",
                text_color_disabled="#a8a8a8",
                corner_radius=2,
            )
            exit_btn.pack(padx=10, pady=10, side="right")

        if progress_bar:
            progress_bar = ctk.CTkProgressBar(
                self,
                mode="indeterminate",
                fg_color="#dc143c",
                height=10,
                corner_radius=3,
                progress_color="#f8eff8",
                width=300,
            )
            progress_bar.set(0)
            progress_bar.pack(padx=10, pady=10, side="bottom")
            progress_bar.start()

    def show_message(self):
        self.place(relx=0.5, rely=0.5, anchor="center")

    def hide_message(self):
        self.place_forget()


class WhisperGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Whisper GUI - ASR")
        self.iconbitmap(app_logo)
        self.geometry("1000x500")
        self.minsize(1000, 500)

        self._center_window(1000, 500)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=1, column=0, sticky="ns", padx=10, pady=(0, 10))

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=(0, 10))

        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )

        self.file_path = None
        self.result = None
        self.thread_pool = ThreadPoolExecutor(max_workers=5)

        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def create_widgets(self):
        self._top_frame()
        self._left_frame()
        self._right_frame()
        self._bottom_frame()

    # Frames
    def _top_frame(self):
        title = ctk.CTkLabel(
            self.top_frame, text="Audio Transciber & Translater", font=("", 20, "bold")
        )
        title.pack(side="left", padx=10, pady=15)

        values = ["System", "Dark", "Light"]
        theme_option = ctk.CTkOptionMenu(
            self.top_frame,
            values=values,
            command=self._change_theme,
            **custom_optionmenu,
        )
        theme_option.set("System")
        theme_option.pack(side="right", padx=10, pady=15)

        theme_label = ctk.CTkLabel(self.top_frame, text="Theme", font=("", 12, "bold"))
        theme_label.pack(side="right", padx=10, pady=15)

    def _left_frame(self):
        checker = CheckMemory()
        result = checker.check_memory()
        models = ["Tiny", "Base", "Small", "Medium", "Large"]
        models_value = []

        if result == False:
            notification = Notification(
                master=self,
                text="No Nvidia GPU with CUDA is available.",
                ex_btn=True,
                cl_btn=False,
            )
            self.after(2000, notification.show_message)

        if result:
            unmet_models = [
                model for model in models if any(model in message for message in result)
            ]

            met_models = [model for model in models if model not in unmet_models]
            models_value = met_models

            notification = Notification(
                master=self,
                text=f"GPU Memory requirements not met for the following models: \n{unmet_models}",
            )
            self.after(2000, notification.show_message)

        if result is None:
            models_value = models

        self.left_frame.grid_rowconfigure(5, weight=1)

        title = ctk.CTkLabel(self.left_frame, text="Settings", font=("", 18))
        title.grid(row=0, column=0, padx=10, pady=10)

        model_label = ctk.CTkLabel(self.left_frame, text="Model Size")
        model_label.grid(row=1, column=0, padx=10, pady=10)

        self.model_option = ctk.CTkOptionMenu(
            self.left_frame,
            values=models_value,
            **custom_optionmenu,
        )
        if models_value:
            self.model_option.set(models_value[0])
        else:
            self.model_option.set("")
        self.model_option.grid(row=1, column=1, padx=10, pady=10)

        language_label = ctk.CTkLabel(self.left_frame, text="Language")
        language_label.grid(row=2, column=0, padx=10, pady=10)

        language_values = [
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
            "Sundanese",
        ]
        self.language_option = ctk.CTkOptionMenu(
            self.left_frame,
            values=language_values,
            **custom_optionmenu,
        )
        self.language_option.set("Auto Detection")
        self.language_option.grid(row=2, column=1, padx=10, pady=10)

        task_label = ctk.CTkLabel(self.left_frame, text="Task")
        task_label.grid(row=3, column=0, padx=10, pady=10)

        task_values = ["Transcribe", "Translate"]
        self.task_option = ctk.CTkOptionMenu(
            self.left_frame,
            values=task_values,
            **custom_optionmenu,
        )
        self.task_option.set("Transcribe")
        self.task_option.grid(row=3, column=1, padx=10, pady=10)

        device_label = ctk.CTkLabel(self.left_frame, text="Device")
        device_label.grid(row=4, column=0, padx=10, pady=10)

        device_value = ["CPU", "GPU"]
        self.device_option = ctk.CTkOptionMenu(
            self.left_frame,
            values=device_value,
            **custom_optionmenu,
        )
        self.device_option.set("GPU")
        self.device_option.grid(row=4, column=1, padx=10, pady=10)

        self.upload_button = ctk.CTkButton(
            self.left_frame,
            text="Upload Audio/Video",
            command=self.select_file,
            border_spacing=5,
            **custom_button,
        )
        self.upload_button.grid(
            row=5, column=0, padx=10, pady=10, rowspan=5, columnspan=2
        )

    def _right_frame(self):
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure((0, 1), weight=1)

        self.textbox = ctk.CTkTextbox(self.right_frame, wrap="word")
        self.textbox.insert("0.0", "Configure settings and than click start button!")
        self.textbox.configure(state="disabled")
        self.textbox.grid(
            row=0, column=0, columnspan=6, padx=10, pady=10, sticky="nsew"
        )

        self.show_time_checkbox = ctk.CTkCheckBox(
            self.right_frame,
            text="Show Time",
            onvalue="on",
            offvalue="off",
            corner_radius=2,
            fg_color="#a52a2a",
            hover_color="#8d0d26",
        )

        self.show_time_checkbox.grid(row=1, column=1, padx=10, pady=10)

        self.start_button = ctk.CTkButton(
            self.right_frame,
            text="Start",
            command=self.start_task,
            **custom_button,
        )
        self.start_button.grid(row=1, column=2, padx=10, pady=10)

        self.subtitle_button = ctk.CTkButton(
            self.right_frame,
            text="Add Subtitle to Video",
            command=self.start_subtask,
            **custom_button,
        )
        self.subtitle_button.grid(row=1, column=3, padx=10, pady=10)

        self.save_button = ctk.CTkButton(
            self.right_frame,
            text="Save",
            command=self.save_text,
            **custom_button,
        )
        self.save_button.grid(row=1, column=4, padx=10, pady=10)

        self.clear_button = ctk.CTkButton(
            self.right_frame,
            text="",
            command=self.clear_output,
            image=clear_icon,
            compound="right",
            width=50,
            border_spacing=2,
            **custom_button,
        )
        self.clear_button.grid(row=1, column=5, padx=10, pady=10)

    def _bottom_frame(self):
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        version_label = ctk.CTkLabel(self.bottom_frame, text=app_version, font=("", 12))
        version_label.grid(row=0, column=0, padx=10, pady=10)

        github_button = ctk.CTkButton(
            self.bottom_frame,
            text="Github",
            command=self.open_github,
            image=github_icon,
            compound="right",
            width=100,
            border_spacing=4,
            **custom_button,
        )
        github_button.grid(row=0, column=2, padx=10, pady=10)

    # Functions
    def start_task(self):
        if self.return_data():
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
        notification = Notification(
            master=self,
            text="Task has started. Please wait!",
            cl_btn=False,
            progress_bar=True,
        )
        notification.show_message()
        self.start_button.configure(state="disabled")

        fp16 = True

        if device == "cpu":
            fp16 = False

        load_model = whisper.load_model(model, device=device)
        load_audio = whisper.load_audio(file_path)
        load_audio = whisper.pad_or_trim(load_audio)
        audio = file_path

        if language == "auto detection":
            mel = whisper.log_mel_spectrogram(load_audio).to(load_model.device)

            _, probs = load_model.detect_language(mel)
            lang = max(probs, key=probs.get)
            self.lang = lang

            result = load_model.transcribe(
                audio,
                language=lang,
                task=task,
                fp16=fp16,
            )

            if show_time == "on":
                for segment in result["segments"]:
                    segment = "[%s --> %s]%s" % (
                        round(segment["start"], 2),
                        round(segment["end"], 2),
                        segment["text"],
                    )
                    self.textbox.configure(state="normal")
                    self.textbox.delete("0.0", "end")
                    self.textbox.insert("end", segment + "\n")
                    self.textbox.configure(state="disabled")
            else:
                text = result["text"].strip().capitalize()
                self.textbox.configure(state="normal")
                self.textbox.delete("0.0", "end")
                self.textbox.insert("end", text)
                self.textbox.configure(state="disabled")

        else:
            result = load_model.transcribe(
                audio,
                language=language,
                task=task,
                fp16=fp16,
            )
            if show_time == "on":
                for segment in result["segments"]:
                    segment = "[%s --> %s]%s" % (
                        round(segment["start"], 2),
                        round(segment["end"], 2),
                        segment["text"],
                    )
                    self.textbox.configure(state="normal")
                    self.textbox.delete("0.0", "end")
                    self.textbox.insert("end", segment + "\n")
                    self.textbox.configure(state="disabled")
            else:
                text = result["text"].strip().capitalize()
                self.textbox.configure(state="normal")
                self.textbox.delete("0.0", "end")
                self.textbox.insert("end", text)
                self.textbox.configure(state="disabled")

        self.result = result

        self.start_button.configure(state="normal")
        notification.hide_message()
        notification = Notification(master=self, text="Task complete!")
        notification.show_message()
        self.after(5000, notification.hide_message)

    def start_subtask(self):
        if self.result is not None and self.file_path is not None:
            ogfile_name = os.path.basename(self.file_path)
            sep = "."
            ogfile_name = ogfile_name.split(sep, 1)[0]
            file_path = fd.asksaveasfilename(
                parent=self,
                initialfile=ogfile_name + "-sub",
                defaultextension=".srt",
                title="Export subtitle",
                filetypes=[("MPEG-4", "*.mp4"), ("MKV", "*.mkv"), ("All", "*.*")],
            )

            file_name = os.path.basename(file_path)
            dir_name = os.path.dirname(file_path)
            file_extension = os.path.splitext(file_path)

            tempfile_name = "tempsrt.srt"
            writer = get_writer("srt", ".")
            writer(self.result, tempfile_name)

            if file_extension[1] == ".mkv":
                os.system(
                    "ffmpeg -i {} -i {} -map 0 -map 1 -c copy -disposition:s:0 default -metadata:s:s:0 language={} {} -y".format(
                        '"' + self.file_path + '"',
                        tempfile_name,
                        self.lang,
                        os.path.join('"' + dir_name, file_name + '"'),
                    )
                )
            else:
                if self.device == "cuda":
                    os.system(
                        "ffmpeg -i {} -c:v h264_nvenc -vf subtitles={} {} -y".format(
                            '"' + self.file_path + '"',
                            tempfile_name,
                            os.path.join('"' + dir_name, file_name + '"'),
                        )
                    )
                else:
                    os.system(
                        "ffmpeg -i {} -vf subtitles={} {} -y".format(
                            '"' + self.file_path + '"',
                            tempfile_name,
                            os.path.join('"' + dir_name, file_name + '"'),
                        )
                    )

            os.remove(os.path.join(".", tempfile_name))
        else:
            self.show_notification_5(text="No file is transcribed/selected.")

    def return_data(self):
        if self.file_path:
            model = self.model_option.get().lower()
            language = self.language_option.get().lower()
            task = self.task_option.get().lower()
            device = self.device_option.get().lower()
            show_time = self.show_time_checkbox.get()

            if language == "english" and model != "large":
                model += ".en"

            if language == "english":
                task = "transcribe"

            if device == "gpu":
                device = "cuda"
                self.device = "cuda"

            return self.file_path, model, language, task, device, show_time

        self.show_notification_5(text="Please upload an audio file to begin the task!")
        return None

    def open_github(self):
        webbrowser.open("https://github.com/iamironman0")

    def clear_output(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.configure(state="disabled")

    def save_text(self):
        if self.result is not None and self.file_path is not None:
            ogfile_name = os.path.basename(self.file_path)
            sep = "."
            ogfile_name = ogfile_name.split(sep, 1)[0]

            file_path = fd.asksaveasfilename(
                parent=self,
                initialfile=ogfile_name,
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

            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_path)
            dir_name = os.path.dirname(file_path)

            if file_path and (file_extension[1] == ".srt"):
                writer = get_writer("srt", dir_name)
                writer(self.result, file_name)
                self.save_notification()
            elif file_path and (file_extension[1] == ".txt"):
                txt_writer = get_writer("txt", dir_name)
                txt_writer(self.result, file_name)
                self.save_notification()
            elif file_path and (file_extension[1] == ".vtt"):
                vtt_writer = get_writer("vtt", dir_name)
                vtt_writer(self.result, file_name)
                self.save_notification()
            elif file_path and (file_extension[1] == ".tsv"):
                tsv_writer = get_writer("tsv", dir_name)
                tsv_writer(self.result, file_name)
                self.save_notification()
            elif file_path and (file_extension[1] == ".json"):
                json_writer = get_writer("json", dir_name)
                json_writer(self.result, file_name)
                self.save_notification()
            elif file_path and (file_extension[1] == ".all"):
                all_writer = get_writer("all", dir_name)
                all_writer(self.result, file_name)
                self.save_notification()
        else:
            self.show_notification_5(text="No file is transcribed/selected.")

    def show_notification_5(self, text):
        notification = Notification(master=self, text=text)
        notification.show_message()
        self.after(5000, notification.destroy)

    def save_notification(self):
        notification = Notification(master=self, text="Saving Successfully!")
        notification.show_message()
        self.after(5000, notification.destroy)

    def select_file(self):
        file_path = fd.askopenfilename(
            parent=self,
            title="Select Audio/Video File",
            filetypes=(
                (
                    ("All files", "*.*"),
                    ("Videofile", "*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.flv"),
                    ("Audiofile", "*.mp3 *.wav *.flac *.aac *.ogg *.wma *.m4a"),
                )
            ),
        )
        if file_path:
            file_name = os.path.basename(file_path)
            self.show_notification_5(text=f"Selected file name: {file_name}")
            self.file_path = file_path
        else:
            self.file_path = None
            self.show_notification_5(text="No file is selected.")

    def _center_window(self, window_width, window_height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    def _change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme)

    def _on_close(self):
        self.thread_pool.shutdown(wait=False)
        self.destroy()


if __name__ == "__main__":
    app = WhisperGui()
    app.mainloop()
