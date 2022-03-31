# fdpm

F-Droid Package Manager
Install apps from f-droid through command line

## Requirements
- adb
- python

## Setup
- On android:
  - [Enable adb from developer options](https://developer.android.com/studio/command-line/adb#Enabling)
  - [Optional but recommended] To connect adb on phone itself
      - Install [termux](https://f-droid.org/en/packages/com.termux/) 
      - Install [adb binaries](https://github.com/ShiSheng233/Termux-ADB)
      - Follow steps for Wireless connection [here](https://github.com/mzlogin/awesome-adb/blob/master/README.en.md#wireless-connection-need-to-use-the-usb-cable) (Needs USB one time)
      - After disconnecting usb, use termux to connect adb.
- On desktop:
  - Download and extract [platform tools](https://developer.android.com/studio/releases/platform-tools#downloads)
  - Add `adb` to your `PATH` (You should be able to access it from any directory)
  - Follow connection steps for [wireless](https://github.com/mzlogin/awesome-adb/blob/master/README.en.md#wireless-connection-need-to-use-the-usb-cable) 
  or [usb](https://github.com/mzlogin/awesome-adb/blob/master/README.en.md#wireless-connection-need-to-use-the-usb-cable)
- Install [dummy installer apk](https://gitlab.com/kshib/fdpm/-/blob/main/fdroid-cli.apk)
  ([Source code](https://gitlab.com/kshib/fdpm-installer)) - Needed to track installed apps by fdpm

## Installation
```
pip install fdpm
```

## Usage
````
# Search apps
fdpm -s launcher

# Install apps
fdpm -i org.videolan.vlc ch.deletescape.lawnchair.plah

# Uninstall apps
fdpm -n org.videolan.vlc ch.deletescape.lawnchair.plah

# Update installed apps
fdpm -u

# Use dialog interface to avoid using package names (Not supported on windows)
fdpm -d

# Repo names:
fdpm -a

# Subscribe to repo
fdpm -a Bitwarden

# Unsubscribe from repo
fdpm -r Bitwarden

````

Screenshots:
![dialog_demo](https://z.zz.fo/9DeTS.jpg "Dialog demo")

## Tested on
- Android 11
- 5.16.14-1-MANJARO

## License
GNU AFFERO GENERAL PUBLIC LICENSE

