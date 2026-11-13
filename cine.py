"""
Lirik gaya kode versi SINEMATIK (kamera zoom/pan/tilt, blur kedalaman,
glow, bokeh, garis cahaya, bunga doodle, pantulan, aberasi warna).

Jalankan :  python lirik_sinematik.py
Butuh    :  pip install pygame   (atau pygame-ce)
Kontrol  :  SPASI = pause | R = ulang | F = fullscreen | ESC = keluar
Lirik    :  isi file lirik.txt di folder yang sama (boleh pakai [mm:ss.xx])
"""
import math
import os
import random
import re
import sys

import pygame

# ============================ PENGATURAN ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LYRICS_FILE = os.path.join(BASE_DIR, "lirik.txt")
AUDIO_FILE = "lagu.mp3"    # None = tanpa musik. Kalau file tidak ada, tetap jalan.
CODIFY = True              # True = lirik biasa diubah jadi gaya kode otomatis
TYPE_SPEED = 13            # huruf per detik (kalau lirik tanpa timestamp)
LINE_PAUSE = 1.1           # jeda antar baris (tanpa timestamp)
LOOP = True
WINDOW_SIZE = (540, 960)   # potret seperti video; tekan F untuk fullscreen
FPS = 60
CINEMATIC = {              # matikan efek yang bikin berat dengan False
    "glow": True, "reflection": True, "bokeh": True, "streaks": True,
    "flowers": True, "dense_code": True, "aberration": True, "shake": True,
}
# Urutan "shot" kamera per baris: (jenis, kemiringan kamera dalam derajat)
SHOTS = [("close", 0), ("pull", -3), ("medium", 2), ("close", 0), ("push", 3),
         ("wide", -2), ("close", 2.5), ("pull", 0), ("medium", -2), ("push", 0)]
DEFAULT_LYRICS = [
    'const hari = kemarin.lupakan();',
    'kamu.datang("pelan-pelan", () => {',
    '  langit.berubah(warna("jingga"));',
    '  aku.tersenyum();',
    '});',
    'hidup.is("indah");',
]
FONT_FILES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]
FONT_NAMES = "consolas,dejavusansmono,menlo,couriernew,monospace"
# ====================================================================

C_FN, C_STR, C_OBJ = (255, 170, 80), (240, 120, 90), (110, 170, 255)
C_KW, C_ID, C_PUNC = (190, 130, 255), (236, 236, 236), (175, 175, 185)
C_NUM, C_ARROW, C_CURSOR = (120, 220, 170), (255, 200, 120), (255, 32, 32)

TOKEN_RE = re.compile(
    r"""(?P<str>"[^"]*"?|'[^']*'?)
       |(?P<kw>\b(?:let|const|var|if|else|return|function|new|await|async|for|while)\b)
       |(?P<fn>[A-Za-z_]\w*)(?=\()
       |(?P<obj>[A-Za-z_]\w*)(?=\.)
       |(?P<num>\d+)
       |(?P<arrow>=>)
       |(?P<id>[A-Za-z_]\w*)
       |(?P<ws>\s+)
       |(?P<punc>.)""",
    re.X,
)
COLORS = {"str": C_STR, "kw": C_KW, "fn": C_FN, "obj": C_OBJ, "num": C_NUM,
          "arrow": C_ARROW, "id": C_ID, "ws": C_ID, "punc": C_PUNC}
LRC_RE = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)$")


def clamp(v, a, b):
    return max(a, min(b, v))


def tokenize(text):
    return [(m.group(0), COLORS[m.lastgroup]) for m in TOKEN_RE.finditer(text)]


def codify(line):
    line = line.strip()
    if not line or re.search(r"[(){};=]", line):
        return line
    words = re.sub(r"[^\w\s'-]", "", line).split()
    if not words:
        return line
    ident = lambda w: re.sub(r"\W", "", w) or "x"
    words[0] = ident(words[0])
    if len(words) > 1:
        words[1] = ident(words[1])
    if len(words) == 1:
        return f"{words[0]}();"
    rest = " ".join(words[2:]).replace('"', "'")
    return f'{words[0]}.{words[1]}("{rest}");' if rest else f"{words[0]}.{words[1]}();"


def load_lyrics():
    try:
        with open(LYRICS_FILE, encoding="utf-8") as f:
            raw = [l.rstrip("\n") for l in f if l.strip()]
    except OSError:
        print(f"'{LYRICS_FILE}' tidak ditemukan, memakai contoh bawaan.")
        return list(DEFAULT_LYRICS), None
    texts, times = [], []
    for l in raw:
        m = LRC_RE.match(l)
        if m:
            times.append(int(m.group(1)) * 60 + float(m.group(2)))
            texts.append(m.group(3))
        else:
            times.append(None)
            texts.append(l)
    texts = [codify(t) if CODIFY else t for t in texts]
    keep = [i for i, t in enumerate(texts) if t.strip()]
    texts = [texts[i] for i in keep]
    times = [times[i] for i in keep]
    return texts, (times if times and all(t is not None for t in times) else None)


LYRICS, TIMES = load_lyrics()


# ------------------------- pembuat tekstur -------------------------
def make_bg(w, h):
    top, bottom = (5, 9, 18), (0, 0, 0)
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (w, y))
    return surf


def make_vignette(w, h):
    n = 48
    small = pygame.Surface((n, n), pygame.SRCALPHA)
    for y in range(n):
        for x in range(n):
            nx, ny = (x - (n - 1) / 2) / (n / 2), (y - (n - 1) / 2) / (n / 2)
            r = math.hypot(nx, ny) / 1.25
            small.set_at((x, y), (0, 0, 0, int(clamp(r ** 2.4 * 215, 0, 235))))
    return pygame.transform.smoothscale(small, (w, h))


def make_radial(color, size):
    n = 64
    small = pygame.Surface((n, n))
    for y in range(n):
        for x in range(n):
            r = math.hypot(x - n / 2, y - n / 2) / (n / 2)
            f = clamp(1 - r, 0, 1) ** 2
            small.set_at((x, y), tuple(int(c * f) for c in color))
    return pygame.transform.smoothscale(small, (size, size))


def make_soft_circle(color, radius):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for k in range(radius, 0, -2):
        a = int(255 * (1 - k / radius) ** 1.4 * 0.55)
        pygame.draw.circle(surf, (*color, a), (radius, radius), k)
    return surf


def make_streak(h):
    w = 80
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        a = int(255 * math.exp(-(((x - w / 2) / 15) ** 2)))
        pygame.draw.line(surf, (255, 135, 35, a), (x, 0), (x, h))
    return pygame.transform.rotozoom(surf, -7, 1.0)


def make_flower(size=200):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size / 2
    for k in range(12):
        ang = math.radians(k * 30)
        pts = []
        for j in range(24):
            u = j / 24 * 2 * math.pi
            lx, ly = 46 + 38 * math.cos(u), 13 * math.sin(u)
            pts.append((c + lx * math.cos(ang) - ly * math.sin(ang),
                        c + lx * math.sin(ang) + ly * math.cos(ang)))
        pygame.draw.polygon(surf, (255, 150, 60, 255), pts, 2)
    pygame.draw.circle(surf, (255, 150, 60, 255), (int(c), int(c)), 5, 2)
    return surf


# ------------------------------ aplikasi ------------------------------
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Lirik Sinematik")
        self.clock = pygame.time.Clock()
        self.fullscreen = False
        self.cache = {}
        self.on_resize()
        self.audio_ok = self.setup_audio() if AUDIO_FILE else False
        self.restart()

    # ---------- audio ----------
    def setup_audio(self):
        path = AUDIO_FILE if os.path.isabs(AUDIO_FILE) else os.path.join(BASE_DIR, AUDIO_FILE)
        if not os.path.exists(path):
            print(f"[AUDIO] File tidak ditemukan: {path} (lanjut tanpa musik)")
            return False
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"[AUDIO] Mixer gagal start: {e}")
            return False
        for cand in (path, self.convert_audio(path)):
            if not cand:
                continue
            try:
                pygame.mixer.music.load(cand)
                print(f"[AUDIO] OK: {cand}")
                return True
            except Exception as e:
                print(f"[AUDIO] Gagal memuat {cand}: {e}")
        print("[AUDIO] Coba: ffmpeg -i lagu.mp3 lagu.ogg  lalu AUDIO_FILE = \"lagu.ogg\"")
        return False

    @staticmethod
    def convert_audio(path):
        import shutil
        import subprocess
        if not shutil.which("ffmpeg"):
            return None
        out = os.path.splitext(path)[0] + "_conv.ogg"
        if not os.path.exists(out):
            print("[AUDIO] Mengonversi dengan ffmpeg...")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, out])
        return out if os.path.exists(out) else None

    # ---------- ukuran / aset ----------
    @staticmethod
    def load_font(size):
        for path in FONT_FILES:
            if os.path.exists(path):
                return pygame.font.Font(path, size)
        return pygame.font.SysFont(FONT_NAMES, size)

    def on_resize(self):
        w, h = self.screen.get_size()
        size = max(18, int(min(w, h * 0.56) / 12))
        self.font = self.load_font(size)
        self.small = self.load_font(max(10, int(size * 0.5)))
        self.fh = self.font.get_height()
        self.PAD = 12
        self.LH = int(self.fh * 2.1)
        self.char_w = self.font.size("M")[0]
        self.NUM_W = int(self.char_w * 2.6)
        self.line_h = self.fh + self.PAD * 2
        self.cache.clear()

        self.bg = make_bg(w, h)
        self.vig = make_vignette(w, h)
        self.glow_blue = make_radial((22, 70, 120), int(w * 1.5))
        self.glow_orange = make_radial((110, 55, 10), int(w * 1.1))
        self.streak_img = make_streak(int(h * 1.5))
        self.flower_img = make_flower()
        self.tex = [make_soft_circle(c, 40) for c in ((255, 150, 50), (70, 130, 220), (60, 170, 170))]
        self.dense = self.make_dense(w, h) if CINEMATIC["dense_code"] else None
        rnd = random.Random(3)
        self.particles = [{
            "x": rnd.uniform(0, w), "y": rnd.uniform(0, h),
            "vy": rnd.uniform(-14, -4), "s": rnd.uniform(0.5, 1.6),
            "tex": rnd.randrange(3), "a": rnd.uniform(40, 110), "ph": rnd.uniform(0, 6.28),
        } for _ in range(14)]

    def make_dense(self, w, h):
        """Lapisan kode kecil memenuhi layar (terlihat saat kamera mundur)."""
        W, H = int(w * 1.4), int(h * 1.4)
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        f = self.load_font(max(9, int(self.fh * 0.36)))
        rnd = random.Random(7)
        row_h = int(f.get_height() * 1.3)
        toks = [tokenize(t) for t in LYRICS] or [[("...", C_PUNC)]]
        for r in range(H // row_h):
            x = rnd.randint(0, 40)
            for text, color in rnd.choice(toks):
                s = f.render(text, True, color)
                surf.blit(s, (x, r * row_h))
                x += s.get_width()
        return surf

    # ---------- state ----------
    def restart(self):
        self.idx = 0
        self.last_idx = -1
        self.typed = 0.0
        self.wait = 0.0
        self.scroll = 0.0
        self.paused = False
        self.finished = False
        self.tokens = [tokenize(t) for t in LYRICS]
        self.t = 0.0
        self.song_t = 0.0
        self.zoom = 1.0
        self.roll = 0.0
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.sway = (0.0, 0.0)
        self.punch = 0.0
        self.shake = 0.0
        self.streaks = []
        self.flowers = []
        if self.audio_ok:
            pygame.mixer.music.play()

    def is_typing(self):
        return not self.finished and self.typed < len(LYRICS[self.idx])

    def update(self, dt):
        self.t += dt
        self.update_fx(dt)
        if self.paused or self.finished:
            return
        if TIMES:
            self.update_timed(dt)
            return
        line = LYRICS[self.idx]
        if self.typed < len(line):
            self.typed = min(len(line), self.typed + dt * TYPE_SPEED * random.uniform(0.6, 1.4))
            return
        self.wait += dt
        if self.wait >= LINE_PAUSE:
            self.wait = 0.0
            if self.idx + 1 < len(LYRICS):
                self.idx += 1
                self.typed = 0.0
            elif LOOP:
                self.restart()
            else:
                self.finished = True

    def update_timed(self, dt):
        self.song_t += dt
        i = 0
        while i + 1 < len(TIMES) and TIMES[i + 1] <= self.song_t:
            i += 1
        self.idx = i
        nxt = TIMES[i + 1] if i + 1 < len(TIMES) else TIMES[i] + 3.0
        dur = max(0.4, nxt - TIMES[i] - 0.25)
        speed = max(len(LYRICS[i]) / dur, 6)
        self.typed = min(len(LYRICS[i]), max(0.0, (self.song_t - TIMES[i]) * speed))
        if self.song_t > TIMES[-1] + 3.0:
            if LOOP:
                self.restart()
            else:
                self.finished = True

    # ---------- kamera & efek ----------
    def shot_targets(self):
        mode, roll_t = SHOTS[self.idx % len(SHOTS)]
        p = self.typed / max(1, len(LYRICS[self.idx]))
        if mode == "close":
            z = 1.65
        elif mode == "medium":
            z = 1.0
        elif mode == "wide":
            z = 0.62
        elif mode == "pull":
            z = 1.9 - 1.1 * p
        else:  # push
            z = 0.8 + 0.85 * p
        return z, roll_t

    def update_fx(self, dt):
        W, H = self.screen.get_size()
        if self.idx != self.last_idx:
            self.last_idx = self.idx
            self.on_new_line()
        self.scroll += (self.idx - self.scroll) * min(1.0, dt * 6)
        self.punch = max(0.0, self.punch - dt * 3.0)
        self.shake = max(0.0, self.shake - dt * 4.0)

        zt, rt = self.shot_targets()
        self.zoom += (zt - self.zoom) * min(1.0, dt * 3.2)
        self.roll += (rt - self.roll) * min(1.0, dt * 2.5)

        _, x_end = self.line_surface(self.idx, self.typed, True)
        z = max(0.2, self.zoom)
        cx_t = max(0.40 * W / z, x_end - 0.12 * W / z)
        self.cam_x += (cx_t - self.cam_x) * min(1.0, dt * 7)
        self.cam_y = self.scroll * self.LH + self.line_h / 2

        t = self.t
        sh = self.shake if CINEMATIC["shake"] else 0
        self.sway = (math.sin(t * 0.9) * 5 + math.sin(t * 1.7) * 2.5 + random.uniform(-1, 1) * sh * 9,
                     math.cos(t * 0.7) * 4 + math.sin(t * 2.1) * 2 + random.uniform(-1, 1) * sh * 9)

    def on_new_line(self):
        W, H = self.screen.get_size()
        self.punch = 1.0
        self.shake = 1.0
        if CINEMATIC["streaks"] and random.random() < 0.6:
            self.streaks.append({"t0": self.t, "life": random.uniform(1.6, 2.6),
                                 "x": random.uniform(0.15, 0.85) * W,
                                 "vx": random.uniform(-40, 40), "peak": random.uniform(70, 130)})
        if CINEMATIC["flowers"] and random.random() < 0.35:
            self.flowers.append({"t0": self.t, "life": 3.4,
                                 "x": random.uniform(0.2, 0.8) * W,
                                 "y": random.uniform(0.08, 0.3) * H})

    # ---------- permukaan baris ----------
    def line_surface(self, i, chars, cursor_on):
        n = int(chars)
        key = (i, n, cursor_on)
        hit = self.cache.get(key)
        if hit:
            return hit
        parts, remaining = [], n
        for text, color in self.tokens[i]:
            if remaining <= 0:
                break
            piece = text[:remaining]
            remaining -= len(piece)
            parts.append((piece, color))
        rendered = [self.font.render(p, True, c) for p, c in parts if p]
        text_w = sum(r.get_width() for r in rendered)
        pad, fh = self.PAD, self.fh
        cw = max(4, int(self.char_w * 0.55))
        x_end = pad + self.NUM_W + text_w
        surf = pygame.Surface((x_end + cw + pad * 2 + 6, fh + pad * 2), pygame.SRCALPHA)
        num = self.small.render(f"{i + 1:02d}", True, (95, 95, 110))
        surf.blit(num, (pad, pad + (fh - num.get_height()) // 2))
        x = pad + self.NUM_W
        for r in rendered:
            surf.blit(r, (x, pad))
            x += r.get_width()
        if cursor_on:
            pygame.draw.rect(surf, C_CURSOR, (x + 3, pad + int(fh * 0.04), cw, int(fh * 0.92)))
        if len(self.cache) > 400:
            self.cache.clear()
        self.cache[key] = (surf, x_end)
        return surf, x_end

    # ---------- gambar ----------
    def to_screen(self, wx, wy, depth_scale):
        W, H = self.screen.get_size()
        z = self.zoom * (1 + 0.05 * self.punch)
        fy = H * 0.46
        sx = W / 2 + (wx - self.cam_x) * z + self.sway[0]
        sy = fy + (wy - self.cam_y) * z + self.sway[1]
        sx = W / 2 + (sx - W / 2) * depth_scale
        sy = fy + (sy - fy) * depth_scale
        th = math.radians(self.roll)
        dx, dy = sx - W / 2, sy - H / 2
        return (W / 2 + dx * math.cos(th) + dy * math.sin(th),
                H / 2 - dx * math.sin(th) + dy * math.cos(th))

    def put(self, surf, key, cx, cy, scale, angle, alpha, blur=1.0):
        W, H = self.screen.get_size()
        if alpha <= 2:
            return
        w, h = surf.get_size()
        scale = clamp(scale, 0.05, 5.0)
        half = math.hypot(w, h) * scale / 2
        if cx + half < 0 or cx - half > W or cy + half < 0 or cy - half > H:
            return
        if blur > 1.15:
            b = round(blur * 2) / 2
            bk = ("b", key, b)
            s = self.cache.get(bk)
            if s is None:
                small = pygame.transform.smoothscale(surf, (max(1, int(w / b)), max(1, int(h / b))))
                s = pygame.transform.smoothscale(small, (w, h))
                self.cache[bk] = s
            surf = s
        img = pygame.transform.rotozoom(surf, angle, scale)
        img.set_alpha(int(clamp(alpha, 0, 255)))
        self.screen.blit(img, img.get_rect(center=(int(cx), int(cy))))

    def draw(self):
        scr = self.screen
        W, H = scr.get_size()
        t = self.t
        z_eff = self.zoom * (1 + 0.05 * self.punch)
        scr.blit(self.bg, (0, 0))

        # cahaya ambient
        gb, go = self.glow_blue, self.glow_orange
        scr.blit(gb, (int(W * 0.3 + math.sin(t * 0.25) * W * 0.15) - gb.get_width() // 2,
                      int(H * 0.30) - gb.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
        scr.blit(go, (int(W * 0.78 + math.cos(t * 0.2) * W * 0.1) - go.get_width() // 2,
                      int(H * 0.72) - go.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)

        # kode kecil memenuhi layar saat kamera mundur
        if self.dense is not None:
            da = clamp((1.05 - z_eff) * 260, 0, 150)
            if da > 5:
                self.dense.set_alpha(int(da))
                dw, dh = self.dense.get_size()
                scr.blit(self.dense, (-(dw - W) // 2 + int(math.sin(t * 0.3) * 25),
                                      -(dh - H) // 2 + int(math.cos(t * 0.22) * 25 - self.scroll * 10 % 40)))

        # garis cahaya oranye
        for s in self.streaks[:]:
            age = t - s["t0"]
            if age > s["life"]:
                self.streaks.remove(s)
                continue
            img = self.streak_img
            img.set_alpha(int(math.sin(math.pi * age / s["life"]) * s["peak"]))
            scr.blit(img, (int(s["x"] + s["vx"] * age) - img.get_width() // 2, -int(H * 0.25)))

        # bokeh
        if CINEMATIC["bokeh"]:
            for p in self.particles:
                p["y"] += p["vy"] * (1 / FPS)
                if p["y"] < -60:
                    p["y"] = H + 60
                tex = self.tex[p["tex"]]
                x = (p["x"] - self.cam_x * 0.06 * z_eff) % (W + 120) - 60
                size = int(80 * p["s"])
                img = pygame.transform.smoothscale(tex, (size, size))
                img.set_alpha(int(p["a"] * (0.6 + 0.4 * math.sin(t * 0.8 + p["ph"]))))
                scr.blit(img, (int(x) - size // 2, int(p["y"]) - size // 2))

        # bunga doodle
        for f in self.flowers[:]:
            age = t - f["t0"]
            if age > f["life"]:
                self.flowers.remove(f)
                continue
            img = pygame.transform.rotozoom(self.flower_img, age * 22, 0.9 + 0.3 * age / f["life"])
            img.set_alpha(int(math.sin(math.pi * age / f["life"]) * 150))
            scr.blit(img, img.get_rect(center=(int(f["x"]), int(f["y"]))))

        # baris lirik (lama -> baru)
        idx = self.idx
        cursor_on = self.is_typing() or int(t * 2) % 2 == 0
        for i in range(max(0, idx - 5), idx + 1):
            d = max(0.0, self.scroll - i)
            is_cur = i == idx
            if is_cur:
                surf, _ = self.line_surface(i, self.typed, cursor_on)
                key = (i, int(self.typed), cursor_on)
            else:
                surf, _ = self.line_surface(i, len(LYRICS[i]), False)
                key = (i, len(LYRICS[i]), False)
            alpha = 255 if d <= 0.05 else 255 - 78 * d
            ds = max(0.5, 1 - 0.09 * d)
            blur = 1.0 + 1.0 * d
            wx = surf.get_width() / 2
            wy = i * self.LH + self.line_h / 2
            cx, cy = self.to_screen(wx, wy, ds)
            scale = z_eff * ds
            angle = self.roll + d * 1.4

            if is_cur and CINEMATIC["glow"]:
                self.put(surf, key + ("glow",), cx, cy, scale, angle, 120, blur=3.0)
            self.put(surf, key, cx, cy, scale, angle, alpha, blur)
            if is_cur and CINEMATIC["reflection"]:
                flipped = pygame.transform.flip(surf, False, True)
                rcx, rcy = self.to_screen(wx, wy + self.line_h * 0.95, ds)
                self.put(flipped, key + ("ref",), rcx, rcy, scale, angle, 42, blur=2.5)

        scr.blit(self.vig, (0, 0))
        if CINEMATIC["aberration"]:
            self.aberrate(self.punch)
        pygame.display.flip()

    def aberrate(self, amt):
        sh = int(amt * 14)
        if sh < 1:
            return
        scr = self.screen
        base = scr.copy()
        r, g, b = base.copy(), base.copy(), base.copy()
        r.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        g.fill((0, 255, 0), special_flags=pygame.BLEND_RGB_MULT)
        b.fill((0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
        scr.fill((0, 0, 0))
        scr.blit(r, (-sh, 0), special_flags=pygame.BLEND_RGB_ADD)
        scr.blit(g, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        scr.blit(b, (sh, 0), special_flags=pygame.BLEND_RGB_ADD)

    # ---------- loop ----------
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.screen = pygame.display.set_mode(e.size, pygame.RESIZABLE)
                    self.on_resize()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return
                    if e.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        if self.audio_ok:
                            (pygame.mixer.music.pause if self.paused else pygame.mixer.music.unpause)()
                    if e.key == pygame.K_r:
                        self.restart()
                    if e.key == pygame.K_f:
                        self.fullscreen = not self.fullscreen
                        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
                        size = (0, 0) if self.fullscreen else WINDOW_SIZE
                        self.screen = pygame.display.set_mode(size, flags)
                        self.on_resize()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    try:
        App().run()
    finally:
        pygame.quit()
    sys.exit()
