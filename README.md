# purplegolf
It's like regular golf, except purple.

## Getting Started

This project uses a Python virtual environment (`venv`). The `venv/` folder is
git-ignored, so each developer creates their own locally before developing.

Requires **Python 3.12**.

### 1. Create the virtual environment

```powershell
# PowerShell (Windows)
python -m venv venv
```

```bash
# Git Bash (Windows)
python -m venv venv
```

```bash
# macOS / Linux
python3 -m venv venv
```

### 2. Activate it

Activate the venv at the start of every development session:

```powershell
# PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# Git Bash (Windows)
source venv/Scripts/activate
```

```bash
# macOS / Linux
source venv/bin/activate
```

Once active, your shell prompt is prefixed with `(venv)`. To leave it, run
`deactivate`.

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

> _Note: there are no dependencies yet. Once a `requirements.txt` exists, run the
> command above (with the venv active) to install them._

You're now ready to develop.
