# Change Log
All notable changes to this project will be documented in this file.
## [0.3.0] - 2025-09-01
- All docs and screenshots have been updated or edited.
- eye_sight.py - Refactor: to use clipboard function in latent_tools.py & removing redundant code.
- eye_sight.py - Refactor: for the sake of consistency switched to using sys.platform instead of platform.system().
- File_tree.py - Removed: unused context menu code
- info_view.py - Fixed: issue when no metadata found, file name being elided with ...
- info_view.py - Removed: copy_to_clipboard() function.
- info_view.py - Refactor: to use latent_tools clipboard function.
- latent_tools.py - Added: new sampler names added to SamplerNames strEnum so they are Human readable not just a string of characters
- latent_tools.py - Refactor: Reordered functions and classes from the mess that they were.
- latent_tools.py - Removed: ttip_color() only used in one place for thumbnail_view.py converted to TOOLTIPCOLOR_QSS
- latent_tools.py - Fixed: clipboard_copy()
- latent_tools.py - Added Style Class. All things style related. QSS and Static methods
- latent_tools.py - Added Style.TOOLTIPCOLOR_QSS - changes the tooltip color for the thumbnail ToolTips
- latent_tools.py - Added Style.set_table_styling() same as set_table_styling() before just moved to Style class
- metadatatable.py - Refactor: how sampler names in metadata are handled. use strEnum instead of dict.
- metadatatable.py - Removed: SAMPLERS_NAMES dict and replaced with StrEnum from latent_tools.py
- metadatatable.py - Moved: method set_table_styling() to latent_tools Style Class as static method.
- metadatatable.py - Moved: rearranged some of the methods and functions so they were in a more logical order.
- thumbnail_view.py - Added: show_thumbnail_context_menu() Context menu for file delete, rename, copy path to clipboard and show in OS specific file manager
- thumbnail_view.py - Added: move_thumbnail_to_trash() - does exactly what it says. platform independent.
- thumbnail_view.py - Added: rename_thumbnail_file() - uses OS native file dialog box for rename and sanitizes bad names.
- thumbnail_view.py - Added: filename_to_clipboard() - copies FQFN to system clipboard.
- thumbnail_view.py - Added: open_file_manager() - Open an OS specific file manager and if possible highlights selected file.
- thumbnail_view.py - Fixed: show_selected() to account for deleting and renaming files and the associated thumbnails.
- thumbnail_view.py - Fixed: update_progress() changed progressbar text to reflect what its really doing.
- thumbnail_view.py - Fixed: sort_image_files() now sorts as it should and changed from file Creation Date to Last modified date.
- thumbnail_view.py - Refactor: improved some of error messages to add more meaningful info.
- thumbnail_view.py - Refactor: add_thumbnail() to add context menu to thumbnails and moved tooltip stylesheet to latent_tools.py

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
