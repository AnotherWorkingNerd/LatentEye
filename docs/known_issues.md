# known problems and issues

if you have a png, jpeg image that doesn't display the image or metadata properly, please include it, if you can, in the bug report along with details of what was expected. It's hard to fix if I don't know what it should be.

These are the known problems. please do not file a bug for any of these issues.
- This was tested on MacOS and is reasonable snappy. When I tried it on Ubuntu it really slow when it came to file IO. My initial indicates that this is a known problem with Qt and therefore PyQt. I am researching this to see of there is an way to alieveiate this. what I've found is in [Ubuntu Notes](./Ubuntu_notes.md). Apr 2025 note: With the steps mentioned in the Ubuntu Notes I'm not sure if this is still a problem.
- EyeSight: zoom and  fit to window do not work. This work is in progress.
- MainWindow: sorting does not work. This work is in progress.
- Some menu options may not work as expected. This work is in progress.
- Linux: metadata font is too large.
- Linux: not all the directories should be shown, especially system level dirs.
- Linux: Volume/drive selection needs work better.
