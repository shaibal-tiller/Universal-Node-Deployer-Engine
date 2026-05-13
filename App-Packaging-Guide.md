<div align="center">
  <h1>📦 App Packaging Guide</h1>
  <p><b>Transforming Python Scripts into Native Executables</b></p>
</div>

---

If you want to distribute the **Universal App Deployer** as an independent, native, clickable app with a custom icon—completely eliminating the need for terminal windows—you must compile the source Python script.

Here is the **step-by-step descriptive guide** on how to compile it for major operating systems.

---

## <span style="color:#0078D7">🪟 1. Building for Windows (.exe)</span>

To package the tool into a clean Windows executable, we use `PyInstaller`.

### 🔹 Prerequisites
Make sure Python is installed. Open PowerShell or CMD and run:
```bash
pip install pyinstaller
```

### 🔹 Compilation Step
Navigate to the `Universal-App-Deployer` directory and execute the following command:
```bash
pyinstaller --noconfirm --onedir --windowed --add-data "README.md;." --icon "assets/icon.ico" --name "Universal Deployer" Universal-App-Deployer.py
```
> **💡 Pro Tip:** The `--windowed` flag ensures no ugly command prompt pops up in the background!

### 🔹 The Result
A new folder named **`dist`** will be generated. Inside `dist/Universal Deployer/`, you will find your standalone **`Universal Deployer.exe`**. You can now create a desktop shortcut or zip this folder to share it!

---

## <span style="color:#A2AAAD">🍎 2. Building for macOS (.app & .dmg)</span>

Mac requires two phases if you want it to be truly professional: 
1. Converting the script to a `.app`.
2. Packaging the `.app` into a drag-and-drop `.dmg` disk image.

### 🔹 Phase A: Compiling the `.app` file
We use `py2app` to bundle everything for macOS.

1. Install the compiler:
```bash
pip3 install py2app
```
2. Generate the setup file:
```bash
py2applet --make-setup Universal-App-Deployer.py
```
3. Build the application (the `-A` alias creates a portable build linked to your libs, but for full distribution, remove the `-A`):
```bash
python3 setup.py py2app
```
*Your native `.app` bundle is now ready inside the `dist/` directory!*

### 🔹 Phase B: Creating the DMG Drag-and-Drop Installer
To create a clean "Drag to Applications" installer window just like commercial apps, install the `create-dmg` tool.

1. Install `create-dmg` via Homebrew:
```bash
brew install create-dmg
```
2. Generate the `.dmg` file using your newly built `.app`:
```bash
create-dmg \
  --volname "Universal Deployer Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "Universal Deployer.app" 150 190 \
  --hide-extension "Universal Deployer.app" \
  --app-drop-link 450 190 \
  "UniversalDeployer.dmg" \
  "dist/Universal Deployer.app"
```
### 🎉 Done!
You now have a clean **`UniversalDeployer.dmg`**. When users open it, they will see an intuitive UI instructing them to drag the app into their macOS `Applications` folder!
