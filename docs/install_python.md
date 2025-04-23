
# Python3 intallation

In order to use LatentEye you need to have python3.12 or later on your system. The instructions for Linux, macOS, and Windows are below

## MacOS:
   If you don't know if python is installed use Spotlight (cmd-space) and enter `python3`. Spotlight will show what it finds and likely the version number along with it. If you don't have python 3.12 or later installed I would recommend th use following.

   1. install [Homebrew](https://brew.sh) if you don't already have it.
   1. Install the latest version of Python3 using Brew:
      ```sh
      $ brew install python@3
      ```
      if you want install a specific version of python using Homebrew use `brew install python@[version]` where [version] is the specific version you want. eg. `brew install python@3.12` or `brew install python@3.13`

   if you want to take the road less taveled without a brew, Python install instructions be found on Python.org at [Using Python on macOS](https://docs.python.org/3/using/mac.html). Select a version 3.12 or later.

## Linux
   For all Linux distros, to determine what version of python you have installed use:
   ```
   $ which python3
   $ python3 --version
   ```
   how you install python depends on which distro you are using. first find out what you have.<br/>
   if neither of those work either python is not installed or not on your `PATH`.

### apt based
yes, that means Debian, Mint, Ubuntu, and several others.
   ```
   $ sudo apt-get update
   $ sudo apt-get install python3
   ```

   on some versions of Ubuntu, use the <a href="https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa">“deadsnakes” PPA</a> to install Python.
   ```
   $ sudo apt install software-properties-common               # you need this for the next step
   $ sudo add-apt-repository ppa:deadsnakes/ppa
   $ sudo apt-get update
   $ sudo apt-get install python3
   ```

### RPM based
Like Red Hat distros, CentOS (R.I.P.), Rocky and Alma. it uses either yum or dnf package managers so one of these should work:
```
$ sudo dnf install python3 -y
$ sudo yum install python3 -y
```

### Pacman based
wacca..wacca...wacca...Arch, Manjaro, wacca..wacca...others?
```
sudo pacman -Sy python
```
### Others
for all others see [https://docs.python.org/3/using/unix.html](https://docs.python.org/3/using/unix.html)

## Microsoft Windows
   1. Download Python from the [Windows Download](https://www.python.org/downloads/windows/) page. Version 3.12 or later.
   1. Run the installer. Make sure to _check_ the box to have Python added to your `PATH` if the installer offers such an option (it's normally off by default).

   This is covered in detail on Python.org at [Using Python on Windows](https://docs.python.org/3/using/windows.html) page. Select a version 3.12 or later.

## Getting bit by the snake?
If you don't understand what to do or are having difficulty, maybe a different perspective will help: The hitchhikers guide to Python pages.
- [Installing Python 3 on Linux](https://docs.python-guide.org/starting/install3/linux/)
- [Installing Python 3 on Mac OS](https://docs.python-guide.org/starting/install3/osx/)
- [Installing Python 3 on Windows](https://docs.python-guide.org/starting/install3/win/)
