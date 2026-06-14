# LoL Color Pentagon

LoL Color Pentagon is a dynamic Python-based desktop application designed to generate and visualize attribute pentagons for League of Legends champions. It allows users to browse through all 172 champions and view their core attributes represented visually around a "color pentagon".

## Features
- **Visual Overlays:** Automatically overlays a champion's Role, Class, Legacy Class, Resource, Range Type, Release Date, and Store Price onto a mathematical pentagon.
- **Customizable Backgrounds:** Includes options for standard dark backgrounds, pure green (Chroma Key/Green Screen for OBS), magenta, black, and white.
- **Thumbnails & Galleries:** View up to 5 individual images per champion or dynamically generate a composite rendering that combines the champion's splash art with their data pentagon.
- **Portable & Open Source:** The source code resolves all file paths dynamically. The repository includes all necessary raw data (markdown files and PNG symbols).

## How to use
You can either run the pre-built executable or run the project from source.

### Option 1: Executable
1. Go to the **Releases** section on the right side of the GitHub repository page.
2. Download the latest `ColorPentagon.exe`.
3. Run it! (No installation required)

### Option 2: From Source
1. Download the repository or `lol-color-pentagon-source.zip`.
2. Ensure you have Python installed.
3. Install the required libraries: `pip install pillow`
4. Run the script: `python color_pentagon.py`

## Building the Executable
If you make changes to the source code and want to build a new `.exe`, run:
```bash
python build_exe.py
```
This will automatically package all folders (`champs`, `empty_pentagon`, `symbols`) into a standalone executable in the `dist` folder using PyInstaller.

## License
The underlying source code of this project is licensed under the MIT License. See the `LICENSE` file for details.

## Legal Disclaimer
This is a fan-made project and is **not** affiliated with, endorsed, sponsored, or specifically approved by Riot Games. All rights, copyrights, and intellectual property regarding League of Legends, its champions, and assets belong entirely to Riot Games. 

Because this project utilizes Riot Games' intellectual property, **commercial use of this application or its assets is strictly prohibited**. This project was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project.
