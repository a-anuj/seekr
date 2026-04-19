<div align="center">

<img src="assets/logo.png" alt="Seekr Logo" width="120"/>

# Seekr

**AI-powered natural language file search for Linux**

[![Fedora COPR](https://img.shields.io/badge/Fedora%20COPR-a--anuj%2Fsekr-blue?logo=fedora&logoColor=white)](https://copr.fedoraproject.org/coprs/a-anuj/seekr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GTK4](https://img.shields.io/badge/GTK-4.0-brightgreen?logo=gnome)](https://gtk.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![AI: Groq](https://img.shields.io/badge/AI-Groq-orange)](https://groq.com)

</div>

---

## What is Seekr?

Seekr is an **AI-powered file search tool** for Linux that understands natural language. Instead of wrestling with `find` or `locate` commands, just type what you're looking for — the way you'd say it out loud.

> _"python files from yesterday"_  
> _"report pdf in downloads"_  
> _"that parser file I edited in GigArmor"_

Seekr parses your intent using a **hybrid rule-based + AI pipeline** (powered by [Groq](https://groq.com)), queries a local **SQLite FTS5 index** for near-instant results, and opens the file's location in your file manager with one click.

It ships with both a sleek **GTK4/Adwaita GUI** (GNOME-native) and a **CLI** for power users.

---

## Features

| Feature | Description |
|---|---|
| **AI Query Parsing** | Understands natural language via Groq LLM; extracts filename keywords, folder hints, and structured filters |
| **Fast Indexed Search** | SQLite FTS5 full-text search index — no slow `find` traversals on every query |
| **Smart Sync Indexer** | Background indexer that adds new files, updates changed ones, and prunes deleted ones — without a full rebuild |
| **Filter Support** | Filter by **file extension**, **time range** (today, yesterday, last week, custom), **folder name**, and **file size** |
| **Size-Based Search** | Find the largest/smallest files or filter by size thresholds — e.g. _"largest files in downloads"_, _"files over 10MB"_ |

| **Secure API Key Storage** | Groq API key stored using the system keyring (no plaintext secrets on disk) |
| **GNOME-Native GTK4 UI** | Built with Adwaita for a native GNOME look and feel |
| **One-Click Open** | Double-click a result to reveal the file in your file manager (via DBus `ShowItems`) |

---

## Installation

### Recommended: Fedora COPR (DNF)

The easiest and recommended way to install Seekr on Fedora/RHEL-based systems.

```bash
# Enable the COPR repository
sudo dnf copr enable a-anuj/seekr

# Install Seekr
sudo dnf install seekr
```

> **Supported:** Fedora 39+, RHEL 9+, and compatible derivatives.

---

## Quick Start

### GUI (GTK4 / GNOME)

Search for **Seekr** in your application menu, or run:

```bash
seekr
```

On first launch, Seekr will prompt you to enter your **Groq API Key**. This enables the AI query understanding features.

1. Get a free API key at [console.groq.com](https://console.groq.com)
2. Paste it in the setup screen (keys start with `gsk_`)
3. Click **Save & Continue** — your key is stored securely in the system keyring

Seekr will then start indexing your files in the background.



## How It Works

Seekr uses a **three-stage pipeline** for every query:

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│  Stage 1: Rule-Based Parser     │  ← Extracts extension, time keywords (fast, zero-cost)
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Stage 2: AI Name & Folder      │  ← Groq LLM extracts filename keyword & folder hint
│          Extractor              │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Stage 3: Confidence Router     │  ← Scores filter set; calls full AI parser if weak
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  SQLite FTS5 Index Search       │  ← Near-instant full-text search on local DB
└─────────────────────────────────┘
    │
    ▼
  Results (sorted by most recent)
```

### Indexer

At startup, a **background thread** runs the smart indexer:

- Scans `~/Projects`, `~/Desktop`, `~/Downloads`, `~/Documents`, `~/Music`, `~/Videos`, `~/Pictures`
- Skips `.git`, `node_modules`, `__pycache__`, `.venv`, `.cache`, etc.
- Uses **mtime comparison** and **inotify** to instantly keep files in sync
- Stores **file size** for size-based filtering and sorting
- Removes entries for files that were deleted from disk
- Stores metadata in `~/.local/share/seekr/seekr.db` (SQLite FTS5)

---

## Project Structure

```
seekr-1.0/
├── app/
│   ├── ai/
│   │   ├── name_extractor.py     # AI: extracts filename keyword from query
│   │   ├── folder_extractor.py   # AI: extracts folder hint from query
│   │   ├── parser_ai.py          # AI: full structured JSON filter extraction (fallback)
│   │   └── utils.py              # Converts AI JSON output → internal filter dict
│   ├── app_entry/
│   │   ├── main_gtk.py           # GTK4/Adwaita GUI (primary UI)
│   │   └── main.py               # PyQt6 GUI (legacy/alternate UI)
│   ├── cli/
│   │   └── main.py               # CLI entry point (`seekr` command)
│   ├── core/
│   │   ├── parser.py             # Rule-based query parser (extension, time)
│   │   ├── router.py             # Hybrid routing: rule-based → AI → fallback
│   │   ├── search.py             # Direct filesystem search (fallback, no DB)
│   │   ├── indexer.py            # Smart background file indexer
│   │   └── filters.py            # Filter helper utilities
│   └── storage/
│       ├── db.py                 # SQLite FTS5 DB init & search
│       └── check_db.py           # Dev utility: preview indexed DB contents
├── assets/
│   └── logo.png                  # Application icon
└── install.sh                    # Manual install script (non-COPR)
```

---

## Query Examples

| Query | What Seekr Understands |
|---|---|
| `"report"` | Files with "report" in the name |
| `"python files today"` | `.py` files modified today |
| `"tar file yesterday"` | `.tar` files from yesterday |
| `"pdf in downloads"` | `.pdf` files inside the Downloads folder |
| `"parser file in GigArmor"` | File named "parser" inside a "GigArmor" folder |
| `"python files last week"` | `.py` files from last week (AI parses date range) |
| `"pictures"` | All files inside `~/Pictures`, sorted by most recent |
| `"largest files in pictures"` | Files from `~/Pictures` sorted by size (largest first) |
| `"files over 10MB"` | Any indexed file larger than 10 MB |
| `"smallest python files"` | `.py` files sorted by size (smallest first) |

---

## System Requirements

- **OS:** Linux (Fedora 39+ recommended; Debian/Ubuntu supported via manual install)
- **Python:** 3.10+
- **Desktop:** GNOME with GTK 4.0 + Adwaita (for GUI; CLI works anywhere)
- **Dependencies:** `python3-gobject`, `gtk4`, `libadwaita`, `keyring`, `groq`, `python-dotenv`
- **Optional:** `locate` / `plocate` (used by the CLI fast-search fallback)



## Configuration

### Groq API Key

Seekr uses [Groq](https://groq.com) for its AI query understanding. A free-tier account is sufficient.

- **GUI:** Enter your key on the first-launch setup screen. It is stored securely via the system keyring.
- **CLI / Manual:** Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_key_here
```

> ⚠️ **Never commit your `.env` file.** It is already in `.gitignore`.



## Manual Installation (Non-COPR)

If you prefer to install from source:

```bash
git clone https://github.com/a-anuj/seekr.git
cd seekr-1.0
chmod +x install.sh
./install.sh
```

The script will:
1. Check and install GTK system dependencies (`python3-gobject`, `gtk4`)
2. Install Python dependencies via `pip`
3. Create a `.desktop` entry so Seekr appears in your app menu



## Contributing

Contributions are welcome! Feel free to open issues or pull requests for:

- Additional AI model backends (Ollama local, OpenAI, Gemini)
- Packaging for other distros (Arch AUR, Debian PPA)



## License

This project is licensed under the **MIT License**.
