# OpenAI Whisper GUI
Modern GUI application that transcribes and translate audio files using OpenAI Whisper.


## Preview
![preview](https://github.com/iamironman0/OpenAI-Whisper-GUI/assets/63475761/bb5fcac3-6d87-4617-9f3c-dcdbf0963574)

https://github.com/iamironman0/OpenAI-Whisper-GUI/assets/63475761/a6a65286-4450-4493-aef1-a2c3f658c96d

## Setup

### Requirements
* Python version 3.9 or newer
* Torch with Cuda
* ffmpeg
* customtkinter 

> For more information please visit OpenAI Wishper github: https://github.com/openai/whisper

1. Install the required dependencies by running the following command:

```
pip install customtkinter Pillow torch openai-whisper torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
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
