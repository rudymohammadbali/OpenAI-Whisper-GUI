import os
import subprocess
import sys
import time

if not sys.platform.startswith("win"):
    print("This app only support Windows system!")
    sys.exit()

else:
    try:
        import pkg_resources
    except ImportError:
        subprocess.call('python -m pip install setuptools', shell=True)
        import pkg_resources

    DIR_PATH = os.path.dirname(os.path.realpath(__file__))

    # Checking the required folders
    folders = ["assets"]
    missing_folder = []
    for i in folders:
        if not os.path.exists(i):
            missing_folder.append(i)
    if missing_folder:
        print("These folder(s) not available: " + str(missing_folder))
        print("Download them from the repository properly")
        sys.exit()
    else:
        print("All folders available!")

    # Checking required modules
    required = {"Pillow==10.1.0", "customtkinter==5.2.1", "packaging==23.2", "openai-whisper==20231117", "pynvml==11.5.0"}
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed
    missing_set = [*missing, ]
    pytorch_win = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
    pytorch_linux = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
    pytorch_mac = "torch torchvision torchaudio"

    # Download the modules if not installed
    if missing:
        try:
            print("Installing modules...")
            for x in range(len(missing_set)):
                y = missing_set[x]
                subprocess.call('python -m pip install ' + y, shell=True)
        except:
            print("Unable to download! \nThis are the required ones: " + str(
                required) + "\nUse 'pip install module_name' to download the modules one by one.")
            time.sleep(3)
            sys.exit()

        try:
            print("Installing Pytorch...")
            if sys.platform.startswith("win"):
                subprocess.call('python -m pip install ' + pytorch_win, shell=True)
            elif sys.platform.startswith("linux"):
                subprocess.call('python3 -m pip install ' + pytorch_linux, shell=True)
            elif sys.platform.startswith("darwin"):
                subprocess.call('python3 -m pip install ' + pytorch_mac, shell=True)
        except:
            print("Unable to download! \nThis are the required ones: " + str(
                required) + "\nUse 'pip/pip3 install module_name' to download the modules one by one.")
            sys.exit()

    else:
        print("All required modules installed!")

    # Everything done!
    print("Setup Complete!")
    time.sleep(5)
    sys.exit()
