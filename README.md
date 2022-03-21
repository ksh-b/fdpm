# fdroid-cli

Install apps from f-droid through command line

## Requirements
- adb
- git
- python

## Setup
- On android:
  - [Enable developer options](https://developer.android.com/studio/command-line/adb#Enabling)
  - [Optional] To connect adb on phone itself:
    - Install a terminal like [termux](https://f-droid.org/en/packages/com.termux/) 
    - Install [adb binaries](https://github.com/ShiSheng233/Termux-ADB)
    - Go to `Developer options` -> `Wireless debugging` -> Note the `IP address & Port`
    - Open termux and enter `adb connect ip.add.re.ss:port` (Enter IP address & Port noted in previous step)
    - Install [dummy installer apk](https://gitlab.com/kshib/fdroid-cli/-/blob/main/fdroid-cli.apk)
- On desktop:
  - Download and extract [platform tools](https://developer.android.com/studio/releases/platform-tools#downloads)
  - Add `adb` to your `PATH` (You should be able to access it from any directory)
  - If wireless adb is possible on your android, enter `adb connect ip.add.re.ss:port` (same way as in android steps)
  - If wireless is not possible, connect usb
  
## Installation
```
git clone https://gitlab.com/kshib/fdroid-cli
cd fdroid-cli
pip install -r requirements.txt
```

## Usage
````
# Search apps
python fdpm.py -s launcher

# Install apps
python fdpm.py -i org.videolan.vlc ch.deletescape.lawnchair.plah

# Uninstall apps
python fdpm.py -n org.videolan.vlc ch.deletescape.lawnchair.plah

# Update installed apps
python fdpm.py -u

# Use dialog interface to avoid using package names (Not supported on windows)
python fdpm.py -d
````

## Tested on
- Android 11
- 5.16.14-1-MANJARO

## License
GNU AFFERO GENERAL PUBLIC LICENSE

