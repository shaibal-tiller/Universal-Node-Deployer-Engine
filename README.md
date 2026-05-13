<div align="center">
  <h1 style="color: #89b4fa;">🚀 Universal App Deployer</h1>
  <p><b>A dynamic, user-friendly graphical tool that makes running, building, and globally sharing modern web apps universally accessible to everyone.</b></p>
  
  <br>
  
  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](#)
  [![Platform](https://img.shields.io/badge/Platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#)
  [![Status](https://img.shields.io/badge/Status-Active-success.svg)](#)
</div>

---

## 👨‍💻 Author Information
* **Author:** Sharif Shaibal, Software Engineer
* **Email:** [shaibalsharif@gmail.com](mailto:shaibalsharif@gmail.com)
* **LinkedIn:** [shaibal-sharif](https://www.linkedin.com/in/shaibal-sharif/)
* **Portfolio:** [shaibal-portfolio.vercel.app](https://shaibal-portfolio.vercel.app/)
* **Project Repository:** [Universal-Node-Deployer-Engine](https://github.com/shaibal-tiller/Universal-Node-Deployer-Engine)
* **Other Repositories:** [github.com/shaibal-tiller](https://github.com/shaibal-tiller)

---

## 🌩️ Core Features

<details open>
<summary><b>1. Dynamic Environment Configuration</b></summary>
Works out of the box! It verifies system requirements autonomously and seamlessly downloads Node.js, Python dependencies, and necessary packages without jumping through hoops.
</details>

<details open>
<summary><b>2. Smart Project Analysis</b></summary>
The engine auto-detects specifics directly from `package.json` (such as Vite, Next.js, Nuxt, React configurations). It visualizes internal `README.md` files instantly right in the app.
</details>

<details open>
<summary><b>3. Automated Build & Serve Engine</b></summary>
Eliminates terminal drudgery! It intelligently triggers `npm install`, identifies whether to run a production build (`npm run build`), and maps the optimal `npm run dev / start` sequence while dynamically hunting for free system ports. 
</details>

<details open>
<summary><b>4. Global SSH Proxy Tunneling</b></summary>
Instantly transition from local loopbacks to the World Wide Web! Creates a secure, remote-accessible link using **localhost.run** reverse SSH tunnels—*no port forwarding, firewalls, or cloud logins required.*
</details>

<details open>
<summary><b>5. Real-Time Resource Monitoring</b></summary>
A live dashboard natively hooked into `psutil` continually monitors your machine's **CPU**, **RAM**, and **Disk Usage**, while spawning isolated live terminals for your web server logs!
</details>

---

## 📥 Downloads & Installation

Choose the version appropriate for your system.

### <span style="color:#0078D7">🪟 Windows Setup</span>
**Option A: Portable Standalone (`.exe`)**
*If you have compiled the app using the guide, you can just click the EXE.*
1. Download `Universal Deployer.exe` from the Releases tab.
2. Double-click the file to launch the Deployer instantly!

**Option B: Running from Source**
1. Download the repository folder.
2. Double-click on `start-deployer.bat`. *It will auto-configure Python environments if you are missing them.*

---

### <span style="color:#A2AAAD">🍎 macOS Setup</span>
**Option A: Native Drag & Drop (`.dmg`) - *Recommended***
1. Download the `UniversalDeployer.dmg` file from the Releases tab.
2. Double click to open the image.
3. Drag the **Universal Deployer** icon into your **Applications** folder shortcut.
4. Open the app from your Launchpad!

**Option B: Running from Source**
1. Download the repository folder.
2. Open your `Terminal` and navigate to the folder.
3. Run the following command to give execution rights:
   ```bash
   chmod +x start-deployer.sh
   ```
4. Execute the launcher:
   ```bash
   ./start-deployer.sh
   ```

---

## 🛠️ Developer Guide (Compiling the App)

Want to build the `.exe` or `.dmg` yourself? 

Please refer to the dedicated [**App Packaging Guide (App-Packaging-Guide.md)**](./App-Packaging-Guide.md) file included in this repository for full graphical, bolded instructions on native compilations using PyInstaller and py2app!
