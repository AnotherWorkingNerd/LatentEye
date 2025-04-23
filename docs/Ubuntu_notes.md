# Troubleshooting

Since this is an early release and I'm the lone developer with access limited to MacOS, Ubuntu, and Windows 11. I'm looking for better solutions but I have a life outside of LatentEye so I'll do the best I can when I can. It's not you are paying for the software. :-)

## Ubuntu notes

While this is mainly for Ubuntu it may so apply to other distro's as well but as of April 2025 I've only tested on Ubuntu 24.04 LTS.

PyQt / Qt seem to be really slow on Ubuntu and possibly other Linux Distros. I searched for a possible cause or solution using mutiple methods. One of the comments I read about this issues said almost exactly "Thats Just The Way It Is" much as as I hate to say it unless someone knows a solution. That all I know. If anyone reading this knows a solution I'd love to hear it.

<!-- this had mutiple problems and then didn't really have any effect.
 installing appmenu-registrar did not help and I can not find the package vala-panel-appmenu-common
Need to incorporate:
  possible solution: `apt install appmenu-registrar vala-panel-appmenu-common`
-->

## PROBLEM - Could not load xcb
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

## WHat the problem is
This error message means that your PyQt6 or Qt application is failing to start because the `xcb` platform plugin is either missing dependencies or not loading properly. Specifically:

1. **Missing `xcb-cursor0` or `libxcb-cursor0`**:
   - From Qt 6.5.0 onward, `xcb-cursor0` (or `libxcb-cursor0` depending on your system) is required for the `xcb` plugin.
   - Without it, the `xcb` plugin cannot initialize, causing Qt to fail.

2. **The `xcb` plugin was found but could not be loaded**:
   - This suggests that `xcb` is installed but has missing dependencies or is incompatible.

3. **No Qt platform plugin could be initialized**:
   - Qt needs a platform plugin (`xcb`, `wayland`, `eglfs`, etc.) to run on Linux. Since `xcb` isn't loading, it tries others but fails.

4. **Your available platform plugins are listed**:
   - `xcb` is among them, but it won’t work until dependencies are fixed.

### **How to Fix**
#### **On Debian / Ubuntu**
Try installing the missing xcb package and associted libraries:
```bash
sudo apt install libxcb-cursor0 libxcb-xinerama0 libxcb1 libx11-xcb1 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0
```

#### **On Fedora**
```bash
sudo dnf install xcb-util-cursor
```

#### **On Arch Linux**
```bash
sudo pacman -S xcb-util-cursor
```

#### **On OpenSUSE**
```bash
sudo zypper install xcb-util-cursor
```

After installing the missing libraries, try running your application again.

If the issue persists, check whether `QT_QPA_PLATFORM` is set correctly:
```bash
echo $QT_QPA_PLATFORM
```
It should return `xcb` (or be empty). If it's something else, try forcing it:
```bash
export QT_QPA_PLATFORM=xcb
./your_qt_app
```
# Postscript

There may be some issues with Qt and QTK one of the suggestions was:
Set the following environment variable to enhance compatibility:
`QT_QPA_PLATFORM=xcb`
This adjustment ensures a smoother integration of QT applications with the chosen themes. After installation, you should observe improved theming consistency across your system.

As with most things [YMMV](https://en.wiktionary.org/wiki/YMMV). Try these step at your own risk. I am not responsible for any of your issues, problems, or data loss.

*note:* using the method mentioned above for Ubuntu 24.04 really improved the performance on my system. It now performs quite well. [Shrug] ahh... the wonders of multi-platform development.

# Disclaimer
USE AT YOUR OWN RISK. What works for me, may not for you. I am not responsible for any data loss, OS failures, or any other data or computer system issues if you use the steps above.

**Sources**:
- [https://askubuntu.com/questions/1185372/why-does-forcing-qt-applications-to-use-gtk-theme-makes-those-apps-startup-slowl](https://askubuntu.com/questions/1185372/why-does-forcing-qt-applications-to-use-gtk-theme-makes-those-apps-startup-slowl)
- [https://askubuntu.com/questions/1506715/qt-applications-not-adhering-to-gtk-theme-after-upgrading-to-ubuntu-23-10](https://askubuntu.com/questions/1506715/qt-applications-not-adhering-to-gtk-theme-after-upgrading-to-ubuntu-23-10)
- [https://stackoverflow.com/questions/79536848/qtreeview-makes-extra-calls-to-qfilesystemmodel](https://stackoverflow.com/questions/79536848/qtreeview-makes-extra-calls-to-qfilesystemmodel)
- [https://forum.qt.io/topic/145196/could-not-load-the-qt-platform-plugin-xcb-in-even-though-it-was-found/9](https://forum.qt.io/topic/145196/could-not-load-the-qt-platform-plugin-xcb-in-even-though-it-was-found/9)
- [https://stackoverflow.com/questions/77725761/from-6-5-0-xcb-cursor0-or-libxcb-cursor0-is-needed-to-load-the-qt-xcb-platform#77726234](https://stackoverflow.com/questions/77725761/from-6-5-0-xcb-cursor0-or-libxcb-cursor0-is-needed-to-load-the-qt-xcb-platform#77726234)
