# 🧱 Minecraft Server Control Panel

A simple web-based control panel built with **Flask (Python)** that allows you to manage a Minecraft Java Edition server on an Ubuntu machine or VPS.

---

## ✨ Features

- 🌐 Start, Stop, and Restart your Minecraft server via a web interface
- ⚙️ Powered by Flask (Python) and `screen` for server control
- 💻 Easy to run on Linux (Ubuntu/Debian)
- 🧠 Beginner-friendly project structure

---

## 📁 Project Structure

minecraft-server-panel/
├── app.py # Flask application
├── templates/
│ └── index.html # Web UI
├── static/
│ └── style.css # Styling for the web interface
├── minecraft_server/
│ └── server.jar # Minecraft server JAR (not uploaded to GitHub)



---

## 🚀 Getting Started

### 1️⃣ Install Requirements

Install Python and Flask:

```bash
sudo apt update
sudo apt install python3-pip -y
pip3 install flask

2️⃣ Set Up Minecraft Server
Download the server.jar from minecraft.net

Place it inside the minecraft_server/ folder

Make sure to accept the EULA:

bash
echo "eula=true" > minecraft_server/eula.txt

python3 app.py

http://localhost:5000

| Action  | URL        |
| ------- | ---------- |
| Start   | `/start`   |
| Stop    | `/stop`    |
| Restart | `/restart` |


🛡️ Security Note
This version is for local or LAN usage only.

For production:

Add authentication

Run behind Nginx with Gunicorn

Use HTTPS (SSL)

🐧 Run as a Service (Optional)
Create a systemd service to run it at boot.

ini
Copy
Edit
[Unit]
Description=Minecraft Flask Panel
After=network.target

[Service]
User=your-username
WorkingDirectory=/home/your-username/minecraft-server-panel
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
🔒 .gitignore
Make sure you don't upload server.jar to GitHub.

Your .gitignore should include:

bash
Copy
Edit
minecraft_server/server.jar
__pycache__/
*.pyc
.env
📜 License
This project is licensed under the MIT License.

👨‍💻 Author
Adarsh Mishra
🔗 LinkedIn
🎮 YouTube: Hyper-A

Built with ❤️ for learning and Minecraft server admins.

yaml
Copy
Edit

---

## ✅ What to Do Next

1. Save this as a file named `README.md` in your project folder.
2. Run:

```bash
git add README.md
git commit -m "Add project README"
git push origin main
