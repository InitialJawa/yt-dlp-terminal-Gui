import os, sys, json, subprocess, shutil
from pathlib import Path

try:
    import msvcrt
except ImportError:
    msvcrt = None

os.system("")

R = "\033[0m"; B = "\033[94m"; G = "\033[92m"; Y = "\033[93m"
C = "\033[96m"; M = "\033[95m"; RED = "\033[91m"; BOLD = "\033[1m"
CLS = "\033[2J\033[H"

YTDLP = shutil.which("yt-dlp") or "yt-dlp"
HOME = Path.home()
QUICK_DIRS = {
    "1": ("Downloads", HOME / "Downloads"),
    "2": ("Videos", HOME / "Videos"),
    "3": ("Desktop", HOME / "Desktop"),
    "4": ("Music", HOME / "Music"),
    "5": ("Documents", HOME / "Documents"),
    "6": ("Current Folder", Path.cwd()),
}

def clear():
    print(CLS, end="")

def banner():
    clear()
    print(f" {M}{BOLD}╔══════════════════════════════════════╗{R}")
    print(f" {M}{BOLD}║     {C}yt-dlp Terminal Downloader{R}     {M}{BOLD}║{R}")
    print(f" {M}{BOLD}╚══════════════════════════════════════╝{R}")
    print()

def get_key():
    if msvcrt:
        k = msvcrt.getch()
        if k == b'\xe0':
            k2 = msvcrt.getch()
            if k2 == b'H': return 'UP'
            if k2 == b'P': return 'DOWN'
            return None
        try:
            return k.decode()
        except:
            return None
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            k = sys.stdin.read(1)
            if k == '\x1b':
                k2 = sys.stdin.read(2)
                if k2 == '[A': return 'UP'
                if k2 == '[B': return 'DOWN'
                return None
            return k
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def select_menu(items, title):
    idx = 0
    shortcuts = {}
    for i, (label, _) in enumerate(items):
        for ch in ["1","2","3","4","5","6","7","8","9","0","m","b","s","c","p","a","v","d","f","h","n","r"]:
            if ch in label and ch not in shortcuts:
                shortcuts[ch] = i
                break
    while True:
        banner()
        print(f" {BOLD}{title}{R}\n")
        for i, (label, _) in enumerate(items):
            arrow = "▸" if i == idx else " "
            fmt = f"{BOLD}{G}" if i == idx else ""
            print(f"  {arrow} {fmt}{label}{R}")
        print(f"\n {B}[↑/↓]  [Enter] select  [q/b] back{R}")
        key = get_key()
        if key == 'UP': idx = max(0, idx - 1)
        elif key == 'DOWN': idx = min(len(items) - 1, idx + 1)
        elif key in ('\r', '\n'): return items[idx][1]
        elif key in ('q', 'b'): return None
        elif key in shortcuts: return items[shortcuts[key]][1]

def pick_resolution(url):
    banner()
    print(f" {Y}Fetching video info...{R}")
    try:
        r = subprocess.run(
            [YTDLP, "--print", "%(title)s", "--print", "%(duration_string)s",
             "--no-playlist", url], capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            print(f" {RED}{r.stderr.strip()}{R}")
            get_key(); return None, None
        lines = r.stdout.strip().split("\n")
        title = lines[0] if lines else "Unknown"
        duration = lines[1] if len(lines) > 1 else "?"
        print(f"\n {G}{BOLD}{title}{R}")
        print(f" {C}Duration:{R} {duration}\n")

        r2 = subprocess.run(
            [YTDLP, "-j", "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if r2.returncode != 0:
            print(f" {RED}Error fetching formats{R}"); get_key(); return None, None

        info = json.loads(r2.stdout)
        fmts = info.get("formats", [])
        video_fmts = [f for f in fmts if f.get("vcodec") and f.get("vcodec") != "none"]
        audio_fmts = [f for f in fmts if f.get("acodec") and f.get("acodec") != "none" and not f.get("vcodec")]

        seen = {}
        clean = []
        for f in video_fmts:
            h = f.get("height") or 0
            ext = f.get("ext", "?")
            label = f.get("format_note") or f"{h}p"
            if h == 0:
                continue
            key = (h, ext)
            if key not in seen or f.get("filesize") or 0 > seen[key].get("filesize") or 0:
                seen[key] = f

        sorted_vids = sorted(seen.values(), key=lambda x: -(x.get("height") or 0))
        options = []
        options.append(("Best (auto)", "bestvideo+bestaudio/best"))

        for f in sorted_vids:
            h = f.get("height") or 0
            ext = f.get("ext", "?")
            note = f.get("format_note") or f"{h}p"
            fr = f.get("fps") or ""
            fs = f.get("filesize")
            size = f" {fs // 1024 // 1024}MB" if fs else ""
            fps = f" {fr}fps" if fr else ""
            label = f"{note} {ext}{fps}{size}"
            options.append((label, f["format_id"]))

        if audio_fmts:
            best_a = max(audio_fmts, key=lambda x: x.get("abr") or 0)
            options.append((f"Audio only ({best_a.get('abr',128)}kbps {best_a.get('ext','m4a')})", "bestaudio/best"))

        options.append(("Audio MP3 (convert)", "bestaudio/best"))
        print(f" {BOLD}Select quality:{R}\n")
        choices = [(l, f) for l, f in options]
        fmt = select_menu(choices, "Select quality:")
        return fmt, title
    except Exception as e:
        print(f" {RED}{e}{R}"); get_key(); return None, None

def pick_folder():
    items = [(f"  [{k}] {v[0]}", str(v[1])) for k, v in QUICK_DIRS.items()]
    items.append(("  [m] Manual path", "__manual__"))
    items.append(("  [b] Browse...", "__browse__"))

    choice = select_menu(items, "Choose save location:")
    if choice is None:
        return None
    if choice == "__manual__":
        print(f"\n {Y}Enter full path:{R}")
        p = input("  > ").strip()
        return p if p else None
    if choice == "__browse__":
        return browse_dir()
    return choice

def browse_dir():
    current = HOME
    idx = 0
    while True:
        banner()
        print(f" {BOLD}Browse folders{R}\n")
        print(f" {C}Current:{R} {current}\n")
        try:
            dirs = sorted([p for p in current.iterdir() if p.is_dir() and not p.name.startswith(".")])
        except:
            dirs = []
        entries = ["✓ Select this folder"]
        paths = [current]
        if current.parent != current:
            entries.append(".. (go up)")
            paths.append(current.parent)
        for p in dirs:
            entries.append(f" {p.name}")
            paths.append(p)
        if idx >= len(entries): idx = len(entries) - 1

        for i, e in enumerate(entries):
            arrow = "▸" if i == idx else " "
            fmt = f"{BOLD}{G}" if i == idx else ""
            print(f"  {arrow} {fmt}{e}{R}")
        print(f"\n {B}[↑/↓]  [Enter] select folder  [q] back{R}")
        key = get_key()
        if key == 'UP': idx = max(0, idx - 1)
        elif key == 'DOWN': idx = min(len(entries) - 1, idx + 1)
        elif key in ('\r', '\n'):
            if idx == 0:
                return str(current)
            elif entries[idx] == ".. (go up)":
                current = current.parent; idx = 0
            else:
                current = paths[idx]; idx = 0
        elif key == 'q': return None

def download(url, fmt, out_dir):
    banner()
    print(f" {G}{BOLD}Downloading...{R}\n")
    print(f" {C}Save to:{R} {out_dir}\n")

    is_audio = "audio" in fmt or fmt == "bestaudio/best"
    out_tmpl = f"{out_dir}/%(title)s.%(ext)s"
    cmd = [YTDLP, "-f", fmt, "-o", out_tmpl, url, "--newline", "--no-playlist"]

    if is_audio:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            if "%" in line:
                try:
                    pct = line.split("%")[0].split()[-1]
                    p = float(pct.replace(",", "."))
                    bar_w = 40
                    filled = int(bar_w * p / 100)
                    bar = "█" * filled + "░" * (bar_w - filled)
                    sys.stdout.write(f"\r  {G}{bar}{R} {BOLD}{pct}%{R}")
                    sys.stdout.flush()
                except:
                    pass
            elif "Destination" in line:
                fname = line.split(":")[-1].strip()
                print(f"  {C}File:{R} {Path(fname).name}")
            elif "Merger" in line or "Converting" in line:
                print(f"  {Y}Processing...{R}")
        proc.wait()
        print(f"\n\n {G}{BOLD}Done!{R}")
        print(f" {C}Folder:{R} {out_dir}")
    except Exception as e:
        print(f"\n {RED}Error: {e}{R}")
    print(f"\n {B}Press any key to continue...{R}")
    get_key()

def main():
    while True:
        banner()
        print(f" {BOLD}Paste video URL:{R}")
        print(f" (or 'q' to quit)\n")
        url = input("  > ").strip()
        if url.lower() == 'q': break
        if not url: continue

        fmt, title = pick_resolution(url)
        if fmt is None: continue

        out_dir = pick_folder()
        if out_dir is None: continue

        download(url, fmt, out_dir)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {Y}Bye!{R}")
