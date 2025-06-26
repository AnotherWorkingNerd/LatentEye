# Change Log
All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-06-01
This is a big update with many improvements affecting all parts of LatentEye.

Summary:
- Significantly improved thumbnail generation speed and added progress bar
- Added: refresh button to MainWindow toolbar
- Improved: changes, corrections, and clarifications to markdown files.
- Changed: reordered import lines across all .py files to improve consistency
- Fixed: toolbar buttons in EyeSight. All of them do what they should

Details below:

Changes to main_window.py:
- **Added:** sortMethodChanged signal.
- **Added:** connect to sort method in thumbnail_view.py.
- **Added:** refresh thumbnails button. Due to the way the thumbnails are displayed, a simple auto-refresh is not possible, afaik.
- **Refactored** on_sort_changed to trigger sort method in thumbnail_view.py based on selected sort. Name sort is now the the sort at app start. default is an unsorted sort.
- **Removed:** sort_thumbnails() method removed.

Changes to thumbnail_view.py
- **Added:** threading and signals.
- **Added:** class ThumbnailWorkerSignals
- **Added:** class ThumbnailWorker with run method using signals.
- **Added:** progress bar to Thumbnail generation progress.
- **Added:** add_thumbnail method to do all the stuff thats not thread-safe. much of the code that was in load_thumbnails(). See the code for further docs.
- **Added:** update_progress() - updates progress bar.
- **Refactored** heavily modified load_thumbnails. Now only triggers ThumbnailWorker thread and progress bar. moved image file reading and to threaded run method.
- **Added:** sort_image_files. This is now the primary entrance into thumbnail_view from main_window. it generates the list of image files in the specified directory then sorts them based on the chosen sort method then calls load_thumbnails.

Changes to eye_sight.py
- **Added:** QVBoxLayout layout.
- **FIXED:** zoom, reset zoom and fit to window.
- **FIXED:** mouseWheel scroll and zoom. depending on platform hold down option or alt key to zoom with mouse wheel.
- **FIXED:** toolbar actions now do what they should.
- **Rewrote:** several part but the biggest rewrite was to actions, functions and methods related to image zoom. Not perfect but works.

Changes to latent_tools.py
- **Added:** Style class - to have a single resource for all the QSS strings used. Imho, otherwise they clutter up the code.
- **Changed:** ttip_color() changed the default background color

## [0.1.0] - 2025-04-23
### Initial release.
- **Added:** well, everything.
  - Thumbnail generation for browsing PNG, jpeg and webp images that may or may not have been the result of Generative AI.
  - Display full metadata associated with images from ComfyUI and Stable Diffusion related tools
  - EyeSight for full size viewing of selected image.
  - Copy the metadata info to the system clipboard.
  - Easy to use GUI with resizable elements and windows.
