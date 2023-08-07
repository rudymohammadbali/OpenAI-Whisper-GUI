# OpenAI Whisper GUI
Modern GUI application that transcribes and translate audio files using OpenAI Whisper.


## Preview
![Screenshot 2023-08-07 104238](https://github.com/iamironman0/OpenAI-Whisper-GUI/assets/63475761/ed4e92a3-f7d4-40d5-8e67-6e849a8190ab)


## Setup

### Requirements
* Python version 3.9 or newer
* Torch with Cuda
* ffmpeg
* customtkinter 

> For more information please visit OpenAI Wishper github: https://github.com/openai/whisper

1. Install the required dependencies by running the following command:

```
pip install customtkinter Pillow pynvml torch openai-whisper torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
```

2. Install fffmpeg:
```
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

3. Run the application by executing the following command:

```
python main.py 
```
