from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os
import json  # <-- added for saving users

app = Flask(__name__)
app.secret_key = "aerosegment_secret"

# -----------------------------
# Dataset Configuration
# -----------------------------
DATASETS = {
    "beed-by-pass": "datasets/beed-by-pass.csv",
    "paithan-gate": "datasets/paithan-gate.csv",
    "hudco": "datasets/hudco.csv",
    "cidco": "datasets/cidco.csv",
    "chikalthana": "datasets/chikalthana.csv"
}

# Price recommendations per area
PRICE_RANGES = {
    "beed-by-pass": "₹10,000 - ₹12,000",
    "paithan-gate": "₹14,000 - ₹18,000",
    "hudco": "₹20,000 - ₹25,000",
    "cidco": "₹25,000 - ₹30,000",
    "chikalthana": "₹30,000 - ₹35,000"
}

# -----------------------------
# User system with JSON persistence
# -----------------------------
USERS_FILE = "users.json"

# Load users from file (if it exists)
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        try:
            USERS = json.load(f)
        except json.JSONDecodeError:
            USERS = {}
else:
    USERS = {}

def save_users():
    """Save current USERS dict to users.json"""
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!")
            return redirect(url_for("login"))

    return render_template("auth.html")

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    if username in USERS:
        flash("Username already exists!")
    else:
        USERS[username] = password
        save_users()  # <-- added this to persist user data
        flash("Account created successfully! Please log in.")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# -----------------------------
# Dashboard Route
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        username=session["username"],
        datasets=DATASETS,
        prices=PRICE_RANGES
    )

# -----------------------------
# Plot Generation
# -----------------------------
@app.route("/api/plots/<plot_type>/<dataset>")
def generate_plot(plot_type, dataset):
    if dataset not in DATASETS:
        return "Dataset not found", 404

    dataset_path = DATASETS[dataset]
    if not os.path.exists(dataset_path):
        return f"File not found: {dataset_path}", 404

    df = pd.read_csv(dataset_path)

    plt.figure(figsize=(6, 4))
    img = io.BytesIO()

    try:
        if plot_type == "age":
            sns.histplot(df["Age"], bins=10, kde=True, color="teal")
            plt.title("Customer Age Distribution")

        elif plot_type == "gender":
            sns.countplot(x="Gender", data=df, palette="coolwarm")
            plt.title("Gender Distribution")

        elif plot_type == "income":
            sns.histplot(df["Annual Income (Lakhs)"], bins=10, color="orange")
            plt.title("Annual Income Distribution (Lakhs)")

        elif plot_type == "spending":
            sns.histplot(df["Spending Score (1-100)"], bins=10, color="green")
            plt.title("Spending Score Distribution")

        elif plot_type == "correlation":
            sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="coolwarm")
            plt.title("Correlation Matrix")

        elif plot_type == "clusters":
            sns.scatterplot(
                x="Age",
                y="Spending Score (1-100)",
                data=df,
                hue="Gender",
                palette="Set2"
            )
            plt.title("Customer Segmentation (Age vs Spending Score)")

        else:
            return "Invalid plot type", 400

        plt.tight_layout()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close()
        return send_file(img, mimetype="image/png")

    except Exception as e:
        print("Error generating plot:", e)
        return f"Error: {e}", 500

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
