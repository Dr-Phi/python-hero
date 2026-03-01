# 🎸 Python Hero

A musical game inspired by Clone Hero, built with Python and Pygame.

## ✨ Features

- 🎵 Select any `.mp3` from your `assets/` folder
- 🎼 Record your own song chart in real time
- 💾 Save multiple chart versions per song
- 📂 Load existing charts

## project structure

python-hero/
├── assets/ (Put your .mp3 and .txt charts here)
├── save_data/ (Your .json profiles will appear here)
└── src/
└── python_hero/
├── `**init**.py`
├── main.py
├── app.py
├── config.py
├── data_manager.py
├── gameplay.py
├── render.py
└── screens.py

---

## 🎮 Controls

### Global

- `ESC` — Quit
- `BACKSPACE` — Go back (menus)

### Splash Screen

- `SPACE` — Continue

### Song Selection

- `UP / DOWN` — Navigate songs
- `ENTER` — Select song

### Chart Menu

- `R` — Record new chart
- `L / ENTER` — Load selected chart
- `D` — Delete selected chart
- `BACKSPACE` — Return to song list

### Recording Mode

- `Y U I O P` — Record notes
- `S` — Save chart

### Play Mode

- `Y U I O P` — Hit notes
- `Score +1` per correct hit

---

## 🚀 Installation

### 1️⃣ Clone the repo

git clone https://github.com/YOUR_USERNAME/python-hero.git

cd python-hero

### 2️⃣ Create virtual environment

python -m venv .venv
.venv\Scripts\activate # Windows

### 3️⃣ Install dependencies

pip install -r requirements.txt

---

## ▶️ Run the Game

From project root:

python -m src.python_hero.main

Or create a `run.py` launcher if preferred.

---

## 🎵 Adding Songs

Place your `.mp3` files inside:

assets/

Charts will be saved automatically in the same folder.

## 📦 Dependencies

- Python 3.10+
- pygame
