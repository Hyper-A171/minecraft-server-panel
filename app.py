from flask import Flask, render_template, request, redirect, url_for, session, flash
import subprocess, smtplib, random, string, os, sqlite3, bcrypt, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'A9d$8xP#kL*2mZ!q0hF@v7T'

# -----------------------------
# Helpers
# -----------------------------
def get_db_connection():
    db_path = "/var/www/minecraft_webpanel/users.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(user_id, to_email, username, purpose="Verification"):
    code = generate_verification_code()

    conn = sqlite3.connect("/home/hyper/minecraft_webpanel/users.db")
    conn.execute(
        "INSERT INTO email_verifications (user_id, code, purpose) VALUES (?, ?, ?)",
        (user_id, code, purpose)
    )
    conn.commit()
    conn.close()

    subject = f"{purpose} Code"
    body = f"""Hello {username},

Your {purpose.lower()} code is:

{code}

Please enter this code in the web panel to complete the process.

If you didn't request this, you can ignore this email.
"""

    msg = MIMEMultipart()
    msg["From"] = "mr.hypera@gmail.com"
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "mr.hypera@gmail.com"
    smtp_password = "vvdv txpa alxv dvmv"

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())
        server.quit()
        print(f"Verification email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def run_command(command):
    try:
        output = subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        return output
    except subprocess.CalledProcessError as e:
        return e.output

def get_all_servers():
    import subprocess
    servers = []
    username = session.get("username")
    if not username:
        return servers

    base_dir = f"/home/hyper/minecraft_server/minecraft_{username}/"
    java_dir = os.path.join(base_dir, "Java_Server")
    bedrock_dir = os.path.join(base_dir, "Bedrock_Server")

    for edition, edition_dir in [("Java", java_dir), ("Bedrock", bedrock_dir)]:
        if not os.path.exists(edition_dir):
            continue

        for entry in os.listdir(edition_dir):
            server_path = os.path.join(edition_dir, entry)
            if os.path.isdir(server_path):
                server_name = entry
                service_name = f"{username}_{server_name}"
                properties_path = os.path.join(server_path, "server.properties")
                port = "Unknown"

                if os.path.exists(properties_path):
                    with open(properties_path) as f:
                        for line in f:
                            if line.startswith("server-port"):
                                port = line.strip().split("=")[1]
                                break

                status = subprocess.getoutput(f"systemctl is-active {service_name}").strip()
                servers.append({
                    "name": server_name,
                    "service": service_name,
                    "port": port,
                    "status": status,
                    "edition": edition
                })

    return servers


# -----------------------------
# Public Routes
# -----------------------------
@app.route("/")
def public_home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

# -----------------------------
# Login / Registration
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):

            session["logged_in"] = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome, {user['username']}!")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        hashed = generate_password_hash(password)  # Werkzeug only

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hashed)
            )
            conn.commit()
            flash("User created successfully.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("home.html")

# -----------------------------
# Dashboard
# -----------------------------
@app.route("/panel")
def home():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    return render_template("panel.html")

@app.route("/det", methods=["POST"])
def det():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    entered_password = request.form["confirm_password"].strip()

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        conn.close()
        flash("User not found.")
        return redirect(url_for("profile"))

    stored_hash = user["password_hash"]
    if isinstance(stored_hash, bytes):
        valid = bcrypt.checkpw(entered_password.encode("utf-8"), stored_hash)
    else:
        valid = check_password_hash(stored_hash, entered_password)

    if not valid:
        conn.close()
        flash("Incorrect password. Account was not deleted.")
        return redirect(url_for("profile"))

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    session.clear()
    flash("Your account has been permanently deleted.")
    return redirect(url_for("public_home"))


@app.route("/create_server", methods=["GET", "POST"])
def create_server():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        username = session.get("username")
        server_name = request.form["server_name"].strip()
        port = request.form["port"].strip()
        gamemode = request.form.get("gamemode", "survival").strip().lower()
        edition = request.form.get("edition", "java").strip().lower()

        if not server_name or not port:
            flash("Server name and port are required.")
            return redirect(url_for("create_server"))

        # Validate gamemode
        valid_gamemodes = ["survival", "creative", "adventure", "spectator"]
        if gamemode not in valid_gamemodes:
            gamemode = "survival"

        # Validate edition
        valid_editions = ["java", "bedrock"]
        if edition not in valid_editions:
            edition = "java"

        folder_path = f"/home/hyper/minecraft_server/minecraft_{username}/Java_Server/{server_name}"
        os.makedirs(folder_path, exist_ok=True)

        # Java Edition
        if edition == "java":
            jar_path = "/home/hyper/server.jar"
            os.system(f"cp {jar_path} '{folder_path}/server.jar'")

            with open(os.path.join(folder_path, "eula.txt"), "w") as f:
                f.write("eula=true\n")

            with open(os.path.join(folder_path, "server.properties"), "w") as f:
                f.write(f"server-port={port}\n")
                f.write(f"motd={server_name}\n")
                f.write("online-mode=false\n")
                f.write(f"gamemode={gamemode}\n")

            exec_start = "/usr/bin/java -Xmx1024M -Xms1024M -jar server.jar nogui"

        # Bedrock Edition
        else:
            bedrock_server_path = "/home/hyper/minecraft_server/minecraft_{username}/Bedrock_Server/{server_name}"
            os.system(f"cp -r /home/hyper/bedrock-server/* '{folder_path}/'")

            with open(os.path.join(folder_path, "server.properties"), "w") as f:
                f.write(f"server-port={port}\n")
                f.write(f"server-name={server_name}\n")
                f.write(f"gamemode={gamemode}\n")
                f.write("online-mode=false\n")

            exec_start = f"{folder_path}/bedrock_server"

        # Create systemd service
        service_content = f"""
[Unit]
Description=Minecraft {edition.capitalize()} server {server_name}
After=network.target

[Service]
WorkingDirectory={folder_path}
ExecStart={exec_start}
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

        service_path = f"/etc/systemd/system/{username}_{server_name}.service"
        with open(service_path, "w") as f:
            f.write(service_content)

        os.system("systemctl daemon-reload")
        os.system(f"ufw allow {port}")
        os.system(f"systemctl enable {username}_{server_name}")
        os.system(f"systemctl start {username}_{server_name}")

        flash(f"{edition.capitalize()} server '{server_name}' created and started successfully.")
        return redirect(url_for("manage_servers"))

    return render_template("create_server.html")


@app.route("/verify_email", methods=["GET", "POST"])
def verify_email():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        flash("User not found.")
        return redirect(url_for("profile"))

    if request.method == "GET":
        send_verification_email(user["id"], user["email"], user["username"])
        flash("Verification code sent to your email.")

    if request.method == "POST":
        entered_code = request.form["code"].strip()
        expected_code = conn.execute(
            "SELECT code FROM email_verifications WHERE user_id = ? ORDER BY rowid DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        if expected_code and entered_code == expected_code["code"]:
            conn.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))
            conn.commit()
            flash("✅ Email verified successfully.")
            return redirect(url_for("profile"))
        else:
            flash("❌ Invalid verification code. Please try again.")

    conn.close()
    return render_template("verify.html", email=user["email"])

from flask import (
    render_template, request, redirect, url_for, flash, session
)
from werkzeug.security import check_password_hash, generate_password_hash

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if request.method == "POST":
        # Update email
        if "update_email" in request.form:
            new_email = request.form["email"].strip()
            conn.execute(
                "UPDATE users SET email = ?, email_verified = 0 WHERE id = ?",
                (new_email, user_id)
            )
            conn.commit()
            flash("Email updated. You may now verify it.")

        # Change password with old password verification
        elif "update_password" in request.form:
            old_password = request.form["old_password"].strip()
            new_password = request.form["new_password"].strip()

            # Check old password
            if not check_password_hash(user["password_hash"], old_password):
                flash("Old password is incorrect.")
            else:
                hashed = generate_password_hash(new_password)
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hashed, user_id)
                )
                conn.commit()
                flash("Password updated.")

        # Send email verification
        elif "send_verification" in request.form:
            if not user["email"]:
                flash("Please set an email first.")
            else:
                # You must define this function elsewhere
                send_verification_email(user["id"], user["email"], user["username"])
                flash("Verification code sent to your email.")

        # Refresh user data
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    conn.close()
    return render_template("profile.html", user=user)


@app.route("/manage_servers")
def manage_servers():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    servers = get_all_servers()
    return render_template("manage_servers.html", servers=servers)

@app.route("/action/<service>/<action>")
def action(service, action):
    if "logged_in" not in session:
        return redirect(url_for("login"))
    if action not in ["start", "stop", "restart"]:
        flash("Invalid action")
        return redirect(url_for("manage_servers"))
    run_command(f"systemctl {action} {service}")
    time.sleep(1)
    flash(f"{action.capitalize()} command sent to {service}.")
    return redirect(url_for("manage_servers"))

@app.route("/remove/<service>")
def remove_server(service):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    username = session.get("username")

    # Stop and disable the service
    run_command(f"systemctl stop {service}")
    run_command(f"systemctl disable {service}")

    # Remove the systemd service file
    service_path = f"/etc/systemd/system/{service}.service"
    if os.path.exists(service_path):
        os.remove(service_path)

    # Reload systemd
    run_command("systemctl daemon-reload")

    # Figure out which edition folder contains the server
    server_name = service.replace(f"{username}_", "")
    base_dir = f"/home/hyper/minecraft_server/minecraft_{username}/"
    removed = False

    for edition_folder in ["Java_Server", "Bedrock_Server"]:
        folder_path = os.path.join(base_dir, edition_folder, server_name)
        if os.path.exists(folder_path):
            run_command(f"rm -rf '{folder_path}'")
            removed = True
            break

    if removed:
        flash(f"Server '{server_name}' has been removed.")
    else:
        flash(f"Server '{server_name}' folder not found. Systemd service was removed.")

    return redirect(url_for("manage_servers"))

# -----------------------------
# Run the app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
