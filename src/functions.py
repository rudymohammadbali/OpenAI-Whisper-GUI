import json
import os
import webbrowser
from pathlib import Path
from threading import Thread

import customtkinter as ctk
import pynvml
import whisper
from PIL import Image
from pydub import AudioSegment
from whisper.utils import get_writer

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
DOWNLOAD_DIR = Path().home() / "Downloads"
APP_VERSION = "Version 1.0.0"
ICONS = {
    "settings": ctk.CTkImage(light_image=Image.open(f"{CURRENT_PATH}\\icons\\settings.png"),
                             dark_image=Image.open(f"{CURRENT_PATH}\\icons\\settings.png"), size=(25, 25)),
    "folder": ctk.CTkImage(light_image=Image.open(f"{CURRENT_PATH}\\icons\\folder.png"),
                           dark_image=Image.open(f"{CURRENT_PATH}\\icons\\folder.png"), size=(18, 18))
}

LANGUAGE_VALUES = [
    "Auto",
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
    "title": ("Inter", 22, "normal"),
    "subtitle": ("Inter", 18, "normal"),
    "btn": ("Inter", 14, "normal"),
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

OPTION = {
    "width": 160,
    "height": 28,
    "corner_radius": 3,
    "font": FONTS["small"]
}

BUTTONS = {
    "height": 30,
    "corner_radius": 3,
    "font": FONTS["btn"]
}


def change_theme(new_theme):
    ctk.set_appearance_mode(new_theme)


def help_page() -> None:
    webbrowser.open("https://github.com/rudymohammadbali")


def check_gpu() -> dict:
    pynvml.nvmlInit()
    device_count = pynvml.nvmlDeviceGetCount()
    cuda = device_count > 0

    if cuda:
        device = pynvml.nvmlDeviceGetHandleByIndex(0)
        total_mem = pynvml.nvmlDeviceGetMemoryInfo(device).total
        total_mem_gb = round(total_mem / (1024 ** 3))
    else:
        total_mem_gb = 0

    model_req = {
        10: ["large", "large-v1", "large-v2", "large-v3"],
        5: ["medium", "medium.en"],
        2: ["small", "small.en"],
        1: ["tiny", "base", "tiny.en", "base.en"]
    }

    models_list = [model for req, models in model_req.items() if total_mem_gb >= req for model in models]

    pynvml.nvmlShutdown()

    return {"models": models_list, "cuda": cuda}


def merge_dicts(d1, d2) -> dict:
    for k, v in d1.items():
        if k in d2 and isinstance(v, dict) and isinstance(d2[k], dict):
            d2[k] = merge_dicts(v, d2[k])
    return {**d1, **d2}


def save_config(settings: dict, filename: str) -> bool:
    try:
        existing_settings = load_config(filename)
        merged_settings = merge_dicts(existing_settings, settings)

        with open(filename, 'w') as f:
            json.dump(merged_settings, f, indent=4)

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def load_config(filename: str) -> dict:
    try:
        if not os.path.isfile(filename):
            return {}

        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return {}


def reset_config(filename: str):
    if os.path.exists(filename):
        os.remove(filename)

    gpu_info = check_gpu()
    default_settings = {
        "download_path": str(DOWNLOAD_DIR),
        "models": gpu_info["models"],
        "cuda": gpu_info["cuda"],
        "theme": "system",
        "model": "base",
        "language": "auto",
        "task": "transcribe",
        "device": "cpu"
    }

    save_config(default_settings, filename)


def transcriber_task(options: dict = None, callback: any = None) -> None:
    transcriber = WhisperTranscriber(audio_file=options["audio"], model_size=options["model"],
                                     device=options["device"], language=options["language"], task=options["task"])
    get_result = transcriber.transcribe()
    callback(get_result)


def subtitles_writer(options: dict = None, callback: any = None) -> None:
    file_path = options["output_dir"]
    result = options["result"]
    audio_file = options["audio_file"]

    selected_extension = os.path.splitext(file_path)
    file_extension = selected_extension[1]
    dir_name, get_file_name = os.path.split(file_path)

    default_options = {
        'max_line_width': None,
        'max_line_count': None,
        'highlight_words': False
    }

    if file_extension == ".srt":
        writer = get_writer("srt", dir_name)
        writer(result, audio_file,
               default_options)
    elif file_extension == ".txt":
        txt_writer = get_writer("txt", dir_name)
        txt_writer(result, audio_file, default_options)
    elif file_extension == ".vtt":
        vtt_writer = get_writer("vtt", dir_name)
        vtt_writer(result, audio_file, default_options)
    elif file_extension == ".tsv":
        tsv_writer = get_writer("tsv", dir_name)
        tsv_writer(result, audio_file, default_options)
    elif file_extension == ".json":
        json_writer = get_writer("json", dir_name)
        json_writer(result, audio_file, default_options)
    elif file_extension == ".all":
        all_writer = get_writer("all", dir_name)
        all_writer(result, audio_file, default_options)

    callback(f"File exported as: {file_path}")


def subtitle_to_video(options: dict, callback: any) -> None:
    result = options["result"]
    audio = options["audio"]
    output = options["output"]
    lang = options["lang"]
    device = options["device"]
    if result and audio:
        file_name = os.path.basename(output)
        dir_name = os.path.dirname(output)
        file_extension = os.path.splitext(output)

        temp_file_name = "temp_srt.srt"
        writer = get_writer("srt", ".")
        writer(result, temp_file_name, {"highlight_words": True, "max_line_count": 50, "max_line_width": 3})

        if file_extension[1] == ".mkv":
            os.system(
                "ffmpeg -i {} -i {} -map 0 -map 1 -c copy -disposition:s:0 default -metadata:s:s:0 language={} {} -y".format(
                    '"' + audio + '"',
                    temp_file_name,
                    lang,
                    os.path.join('"' + dir_name, file_name + '"'),
                )
            )
        else:
            if device == "cuda":
                os.system(
                    "ffmpeg -i {} -c:v h264_nvenc -vf subtitles={} {} -y".format(
                        '"' + audio + '"',
                        temp_file_name,
                        os.path.join('"' + dir_name, file_name + '"'),
                    )
                )
            else:
                os.system(
                    "ffmpeg -i {} -vf subtitles={} {} -y".format(
                        '"' + audio + '"',
                        temp_file_name,
                        os.path.join('"' + dir_name, file_name + '"'),
                    )
                )

        os.remove(os.path.join(".", temp_file_name))

        callback(output)


def start_transcriber(options: dict = None, callback: any = None) -> None:
    Thread(target=transcriber_task, args=(options, callback), daemon=True).start()


def start_writer(options: dict = None, callback: any = None) -> None:
    Thread(target=subtitles_writer, args=(options, callback), daemon=True).start()


def start_subtitle(options: dict = None, callback: any = None) -> None:
    Thread(target=subtitle_to_video, args=(options, callback), daemon=True).start()


class WhisperTranscriber:
    def __init__(self, audio_file: str = None, model_size: str = "base", download_root: str = None,
                 language: str = "auto", task: str = "transcribe",
                 prompt: dict = None, device: str = None):

        if not audio_file:
            raise ValueError("[!] Audio file not provided!")
        else:
            is_valid = self.validate_file(audio_file)
            if not is_valid:
                raise ValueError("Error, file is not valid")

        self.available_models = whisper.available_models()

        self.audio_file = audio_file
        self.model_size = model_size if model_size in self.available_models else "base"
        self.download_root = download_root if download_root and os.path.isdir(download_root) else None
        self.language = self.detect_language() if language == 'auto' else language
        self.task = "transcribe" if task == 'translate' and self.language in ['en', 'english'] else task
        self.prompt = self.get_valid_prompts(prompt)
        self.device = device if device in ["gpu", "cpu"] else None

        if self.language in ['en', 'english'] and self.model_size not in ["large", "large-v1", "large-v2", "large-3"]:
            self.model_size += '.en'
            print("[!] Using english only model.")

        self.load_model = whisper.load_model(self.model_size, device=self.device, download_root=self.download_root)

        self.result = None

    def transcribe(self) -> dict:
        result = self.load_model.transcribe(self.audio_file, language=self.language, task=self.task, **self.prompt)
        self.result = result
        return result

    def detect_language(self) -> str:
        model = whisper.load_model("tiny")
        audio = whisper.load_audio(self.audio_file)
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        _, probs = model.detect_language(mel)
        return f"{max(probs, key=probs.get)}"

    def subtitles_writer(self, output_dir: str = None, output_format: str = "txt", options: dict = None) -> None:
        if not os.path.isdir(output_dir):
            raise NotADirectoryError(f"({output_dir}) is not a valid directory")

        extensions = ["txt", "srt", "vtt", "tsv", "json"]
        if output_format not in extensions:
            raise ValueError(f"[!] ({output_format}) is not a valid output format!")

        default_options = {
            'max_line_width': None,
            'max_line_count': None,
            'highlight_words': False
        }

        options = options if options else default_options

        writer = get_writer(output_format, output_dir)
        writer(self.result, self.audio_file, options)

    @staticmethod
    def get_valid_prompts(prompts) -> dict:
        if prompts is None:
            return {}
        transcribe_params = {
            "verbose": bool,
            "temperature": float,
            "compression_ratio_threshold": float,
            "logprob_threshold": float,
            "no_speech_threshold": float,
            "condition_on_previous_text": bool,
            "initial_prompt": str,
            "word_timestamps": bool,
            "prepend_punctuations": str,
            "append_punctuations": str
        }

        valid_prompts = {}

        for prompt_name, value in prompts.items():
            if prompt_name in transcribe_params and isinstance(value, transcribe_params[prompt_name]):
                valid_prompts[prompt_name] = value

        return valid_prompts

    @staticmethod
    def validate_file(file_path: str) -> bool:
        if not os.path.isfile(file_path):
            return False

        try:
            AudioSegment.from_file(file_path)
            return True
        except Exception as e:
            print(e)
            return False
