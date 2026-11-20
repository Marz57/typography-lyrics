#!/usr/bin/env python3
"""
cine.py - lirik sinematik bergaya kode, 5 tipografi.

Lirik TIDAK dibungkus kode asli. Lirik-nya sendiri yang diubah bentuknya
(huruf kapital, pemisah . :: => ||, kurung, dll) jadi mirip sintaks bahasanya.
Baris yang diawali "=" di lyrics.txt tetap ditampilkan apa adanya.

  ./cine.py -typ 1      # JavaScript   (neon, kursor blok merah)
  ./cine.py -typ 2      # Rust         (karat, lifetime, kursor garis bawah)
  ./cine.py -typ 3      # Haskell      (ungu, ligatur λ → ⇒ ≠)
  ./cine.py -typ 4      # SQL          (terminal hijau + scanline CRT)
  ./cine.py -typ 5      # Lisp         (kurung pelangi)

Butuh : pip install pygame   (atau pygame-ce)
Input : lyrics.txt  -> format LRC:  [mm:ss.xx] teks lirik
        file musik  -> music.mp3 / lagu.mp3 / audio apa saja (.mp3 .ogg .wav .flac)
Semua teks rata kiri + nomor baris ala VS Code; kamera zoom dekat ikut teks yg diketik (zoom out pas jeda); kode latar cuma muncul pas ending; looping otomatis (--no-loop utk mati)
Kontrol: SPASI pause | R ulang | F fullscreen | [ ] geser sinkron 0.1s | ESC keluar
"""
import argparse
import math
import os
import random
import re
import sys

try:
    import pygame
except ImportError:
    sys.exit("pygame belum terpasang. Jalankan: pip install pygame  (atau pygame-ce)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WINDOW_SIZE = (540, 960)
FPS = 60
END_FX = 2.6   # detik: kode latar muncul sekali (fade in -> fade out) pas mau ending
AUDIO_EXT = (".mp3", ".ogg", ".wav", ".flac", ".m4a", ".opus")
FX = {"glow": True, "reflection": True, "bokeh": True, "streaks": True,
      "dense_code": True, "aberration": True, "shake": True}


ASCII_OPS = str.maketrans({"λ": "\\", "→": "->", "←": "<-", "⇒": "=>", "≠": "/=", "≥": ">=", "≤": "<="})


def has_glyphs(font, chars):
    """True kalau SEMUA karakter benar-benar punya glyph (bukan kotak tofu / kosong)."""
    def shot(ch):
        try:
            return pygame.image.tostring(font.render(ch, False, (255, 255, 255)), "RGBA")
        except Exception:
            return None
    ref = shot("\uffff")                      # karakter tak-ada -> gambar tofu font ini
    for ch in chars:
        img = shot(ch)
        if img is None or img == ref:
            return False
    return True


def clamp(v, a, b):
    return max(a, min(b, v))


# ======================================================================
#  BAHASA: tokenizer + pewarnaan per sintaks
# ======================================================================
class Lang:
    def __init__(self, rules, colors, fixup=None):
        self.re = re.compile("|".join(f"(?P<{n}>{p})" for n, p in rules))
        self.colors = colors
        self.fixup = fixup

    def tokenize(self, text):
        kinds = [(m.group(0), m.lastgroup) for m in self.re.finditer(text)]
        if self.fixup:
            return self.fixup(kinds, self.colors)
        return [(t, self.colors.get(k, self.colors["id"])) for t, k in kinds]


# ---- 1. JavaScript ---------------------------------------------------
JS = Lang(
    [("comment", r"//.*"),
     ("str", r"\"[^\"]*\"?|'[^']*'?|`[^`]*`?"),
     ("kw", r"\b(?:const|let|var|await|async|new|return|function|yield|if|else|for|of|in|break|throw|try|catch)\b"),
     ("fn", r"[A-Za-z_$][\w$]*(?=\()"),
     ("obj", r"[A-Za-z_$][\w$]*(?=\.)"),
     ("num", r"\d+"), ("arrow", r"=>"),
     ("id", r"[A-Za-z_$][\w$]*"), ("ws", r"\s+"), ("punc", r".")],
    {"kw": (190, 130, 255), "fn": (255, 170, 80), "obj": (110, 170, 255),
     "str": (240, 120, 90), "num": (120, 220, 170), "arrow": (255, 200, 120),
     "id": (236, 236, 236), "punc": (175, 175, 185), "comment": (110, 115, 130)})

# ---- 2. Rust ---------------------------------------------------------
RUST = Lang(
    [("comment", r"//.*"),
     ("life", r"'[A-Za-z_]\w*(?!['\w])"),
     ("str", r"\"[^\"]*\"?"),
     ("macro", r"[A-Za-z_]\w*!"),
     ("kw", r"\b(?:fn|let|mut|match|impl|pub|struct|enum|use|as|where|move|loop|if|else|return|dyn|for|in|self|Some|None|Ok|Err)\b"),
     ("type", r"\b[A-Z]\w*"),
     ("fn", r"[A-Za-z_]\w*(?=[(<])"),
     ("num", r"\d+"), ("arrow", r"->|=>"), ("path", r"::"),
     ("id", r"[A-Za-z_]\w*"), ("ws", r"\s+"), ("punc", r".")],
    {"kw": (255, 120, 80), "type": (255, 200, 110), "life": (120, 220, 230),
     "macro": (255, 160, 60), "fn": (255, 215, 150), "str": (170, 210, 120),
     "num": (255, 160, 100), "arrow": (255, 130, 90), "path": (185, 160, 140),
     "id": (232, 222, 208), "punc": (170, 150, 135), "comment": (120, 105, 95)})

# ---- 3. Haskell (dengan ligatur) --------------------------------------
HASKELL = Lang(
    [("comment", r"--.*"),
     ("str", r"\"[^\"]*\"?"),
     ("kw", r"\b(?:let|in|where|do|case|of|if|then|else|data|type|module|import|newtype|instance|class)\b"),
     ("type", r"\b[A-Z]\w*"),
     ("op", r"λ|→|←|⇒|≠|≥|≤|<\$>|>>=|=<<|<\*>|\+\+|::|\$|\.|\|"),
     ("fn", r"[a-z_]\w*'*(?=\s*(?:::|=(?!=)))"),
     ("num", r"\d+"),
     ("id", r"[A-Za-z_]\w*'*"), ("ws", r"\s+"), ("punc", r".")],
    {"kw": (200, 140, 255), "type": (255, 150, 200), "op": (110, 235, 225),
     "fn": (225, 195, 255), "str": (255, 220, 140), "num": (150, 230, 200),
     "id": (238, 232, 245), "punc": (170, 160, 190), "comment": (120, 110, 140)})

# ---- 4. SQL ------------------------------------------------------------
SQL = Lang(
    [("comment", r"--.*"),
     ("str", r"'(?:[^']|'')*'?"),
     ("kw", r"(?i:\b(?:select|from|where|with|as|join|on|group|by|order|limit|having|union|insert|into|values|update|set|delete|and|or|not|in|case|when|then|else|end|over|partition|desc|asc|distinct|exists|returning|conflict|do|nothing)\b)"),
     ("fn", r"[A-Za-z_]\w*(?=\()"),
     ("num", r"\d+"),
     ("id", r"[A-Za-z_]\w*"), ("ws", r"\s+"), ("punc", r".")],
    {"kw": (160, 255, 160), "fn": (90, 235, 125), "str": (215, 255, 195),
     "num": (255, 255, 255), "id": (110, 205, 125), "punc": (70, 155, 88),
     "comment": (60, 110, 70)})

# ---- 5. Lisp (kurung pelangi) -----------------------------------------
RAINBOW = [(255, 110, 110), (255, 190, 90), (240, 230, 100),
           (120, 230, 140), (100, 200, 255), (190, 140, 255)]
LISP_KW = {"define", "lambda", "let", "let*", "letrec", "cond", "else", "if", "begin",
           "define-syntax", "syntax-rules", "quote", "and", "or", "do", "when",
           "unless", "set!"}


def lisp_fixup(kinds, colors):
    out, depth, prev = [], 0, None
    for text, kind in kinds:
        if kind == "paren":
            if text in "([":
                col = RAINBOW[depth % 6]
                depth += 1
                prev = "("
            else:
                depth = max(0, depth - 1)
                col = RAINBOW[depth % 6]
                prev = ")"
        elif kind == "sym":
            if text in LISP_KW:
                col = colors["kw"]
            elif prev == "(":
                col = colors["fn"]
            elif text.startswith("'"):
                col = colors["quote"]
            elif re.fullmatch(r"-?\d+(\.\d+)?", text):
                col = colors["num"]
            else:
                col = colors["id"]
            prev = "sym"
        else:
            col = colors.get(kind, colors["id"])
            if kind != "ws":
                prev = kind
        out.append((text, col))
    return out


LISP = Lang(
    [("comment", r";.*"), ("str", r"\"[^\"]*\"?"), ("paren", r"[()\[\]]"),
     ("ws", r"\s+"), ("sym", r"""[^\s()\[\]";]+""")],
    {"kw": (255, 140, 200), "fn": (120, 200, 255), "quote": (170, 240, 255),
     "str": (255, 215, 130), "num": (140, 235, 170), "id": (225, 235, 245),
     "comment": (110, 125, 145)},
    fixup=lisp_fixup)


# ======================================================================
#  WARNA: meniru tema editor asli tiap bahasa
#  JS = VS Code Dark+ | Rust = One Dark | Haskell = Dracula
#  SQL = Monokai      | Lisp = Tokyo Night + kurung pelangi
# ======================================================================
def make_pal(**c):
    c.setdefault("arrow", c["op"])
    c.setdefault("path", c["op"])
    for k in ("obj", "prop", "param", "type", "const", "life", "macro", "fn", "kw", "str", "num", "quote"):
        c.setdefault(k, c["id"])
    return c


JS_PAL = make_pal(kw=(197, 134, 192), fn=(220, 220, 170), obj=(156, 220, 254), prop=(130, 170, 255),
                  param=(255, 160, 100), type=(78, 201, 176), str=(206, 145, 120), num=(181, 206, 168),
                  op=(212, 212, 212), arrow=(86, 156, 214), punc=(255, 203, 107), id=(156, 220, 254),
                  comment=(106, 153, 85))
RUST_PAL = make_pal(kw=(198, 120, 221), type=(229, 192, 123), fn=(97, 175, 239), macro=(86, 182, 194),
                    life=(209, 154, 102), str=(152, 195, 121), num=(209, 154, 102), const=(209, 154, 102),
                    obj=(224, 108, 117), prop=(224, 108, 117), param=(224, 108, 117), op=(86, 182, 194),
                    arrow=(198, 120, 221), path=(171, 178, 191), punc=(171, 178, 191), id=(171, 178, 191),
                    comment=(92, 99, 112))
HASKELL_PAL = make_pal(kw=(255, 121, 198), type=(139, 233, 253), fn=(80, 250, 123), param=(255, 184, 108),
                       str=(241, 250, 140), num=(189, 147, 249), op=(255, 121, 198), arrow=(255, 121, 198),
                       punc=(248, 248, 242), id=(248, 248, 242), comment=(98, 114, 164))
SQL_PAL = make_pal(kw=(249, 38, 114), fn=(166, 226, 46), type=(102, 217, 239), str=(230, 219, 116),
                   num=(174, 129, 255), const=(174, 129, 255), op=(249, 38, 114), punc=(248, 248, 242),
                   id=(248, 248, 242), comment=(117, 113, 94))
LISP_PAL = make_pal(kw=(187, 154, 247), fn=(122, 162, 247), quote=(125, 207, 255), str=(158, 206, 106),
                    num=(255, 158, 100), op=(137, 221, 255), punc=(192, 202, 245), id=(192, 202, 245),
                    comment=(86, 95, 137))
for _lang, _pal in ((JS, JS_PAL), (RUST, RUST_PAL), (HASKELL, HASKELL_PAL), (SQL, SQL_PAL), (LISP, LISP_PAL)):
    _lang.colors = _pal          # dipakai juga untuk baris "=" (kode apa adanya)

JS_KW = set("const let var await async new return function yield if else for of in break throw try catch".split())
RUST_KW = set("fn let mut match impl pub struct enum use as where move loop if else return dyn for in self".split())
HASKELL_KW = set("let in where do case of if then else data type module import newtype instance class".split())
SQL_KW = set("select from where with as join on group by order limit having union insert into values update "
             "set delete and or not in case when then else end over partition desc asc distinct exists "
             "returning conflict do nothing".split())


# ======================================================================
#  GAYA SINTAKS: lirik-nya sendiri yang diubah jadi "bentuk kode"
#  Tidak ada kerangka/keyword kode asli yang ditempel. Yang berubah hanya:
#  huruf kapital, pemisah, simbol. Tiap token dapat peran (fungsi, properti,
#  tipe, operator, dst) -> warna sesuai peran seperti di editor asli.
#  Kata lirik yang kebetulan sama dengan keyword bahasanya ikut berwarna keyword.
# ======================================================================
def clean_words(raw):
    """Ambil kata-kata lirik; tanda baca dibuang supaya aman jadi identifier."""
    ws = [re.sub(r"[\W_]", "", w) for w in raw.split()]
    return [w for w in ws if w] or ["..."]


def cap(w):
    return w[:1].upper() + w[1:].lower()


def camel(ws):
    return ws[0].lower() + "".join(cap(w) for w in ws[1:])


def P(t):
    return (t, "punc")


def O(t):
    return (t, "op")


def S(t):
    return (t, "str")


def _tf(tf, k, x):
    if tf == "up":
        return x.upper()
    if tf == "all" or (tf == "first" and k == 0) or (tf == "rest" and k > 0):
        return cap(x)
    return x


def _chain(ws, W, sep, first, mid, last, tf=None):
    """kata1 <sep> kata2 <sep> kata3 ... ; peran: pertama / tengah / terakhir."""
    out, n = [], len(ws)
    for k, x in enumerate(ws):
        if k:
            out.append(sep)
        out.append(W(_tf(tf, k, x), last if k == n - 1 else first if k == 0 else mid))
    return out


def _c(sep, first, mid, last, tf=None, pre=(), post=()):
    return lambda w, W: list(pre) + _chain(w, W, sep, first, mid, last, tf) + list(post)


def _str(post, q='"'):
    return lambda w, W: [S(q + " ".join(w) + q)] + ([P(post)] if post else [])


# ---- JavaScript ------------------------------------------------------
def _js_dollar(w, W):
    out = []
    for k, x in enumerate(w):
        out += ([P(" ")] if k else []) + [O("$"), W(x, "obj")]
    return out + [P(";")]


def _js_call(w, W):
    k = max(1, len(w) // 2)
    return ([(camel(w[:k]), "fn"), P("(")]
            + _chain(w[k:], W, P(", "), "param", "param", "param") + [P(");")])


JS_S = [
    _c(O("."), "obj", "prop", "fn", post=[P("();")]),                  # aku.masih.mencintaimu();
    _c((" => ", "arrow"), "param", "param", "obj", post=[P(";")]),     # aku => masih => mencintaimu;
    _c(O("?."), "obj", "prop", "prop", post=[P(";")]),                 # aku?.masih?.mencintaimu;
    _c(P(", "), "prop", "prop", "prop", pre=[P("{ ")], post=[P(" }")]),  # { aku, masih, mencintaimu }
    _c(P(", "), "obj", "obj", "obj", pre=[P("["), O("...")], post=[P("]")]),  # [...aku, masih]
    _js_dollar,                                                        # $aku $masih $mencintaimu;
    _js_call,                                                          # akuMasih(mencintaimu);
    _str(";"),                                                         # "aku masih mencintaimu";
]


# ---- Rust --------------------------------------------------------------
def _rust_amp(w, W):
    out = []
    for k, x in enumerate(w):
        out += ([P(", ")] if k else []) + [O("&"), W(x, "obj")]
    return out + [P(";")]


def _rust_gen(w, W):
    items = ([("'" + w[1], "life")] if len(w) > 1 else []) + [W(cap(x), "type") for x in w[2:]]
    out = [W(cap(w[0]), "type"), P("<")]
    for k, it in enumerate(items):
        out += ([P(", ")] if k else []) + [it]
    return out + [P(">;")]


RUST_S = [
    _c(("::", "path"), "type", "obj", "fn", tf="first", post=[P("();")]),   # Aku::masih::mencintaimu();
    _rust_amp,                                                              # &aku, &masih, &mencintaimu;
    _c((" -> ", "arrow"), "obj", "type", "type", tf="rest", post=[P(";")]),  # aku -> Masih -> Mencintaimu;
    lambda w, W: ([(w[0] + "!", "macro"), P("(")]
                  + _chain(w[1:], W, P(", "), "obj", "obj", "obj") + [P(");")]),  # aku!(masih, mencintaimu);
    _rust_gen,                                                              # Aku<'masih, Mencintaimu>;
    lambda w, W: [("_".join(x.upper() for x in w), "const"), P(";")],       # AKU_MASIH_MENCINTAIMU;
    _str(";"),
]


# ---- Haskell (ligatur ditulis langsung: λ → ← ⇒ ≠) ----------------------
def _hs_lam(w, W):
    return ([("λ", "op"), W(w[0], "param"), (" → ", "arrow")]
            + _chain(w[1:] or w[:1], W, O(" ++ "), "id", "id", "id"))


def _hs_sig(w, W):
    return ([W(w[0], "fn"), O(" :: ")]
            + (_chain(w[1:], W, (" → ", "arrow"), "type", "type", "type", "all") or [P("()")]))


def _hs_bind(w, W):
    return ([W(w[0], "id"), (" ← ", "arrow")]
            + (_chain(w[1:], W, O(" ++ "), "id", "id", "id") or [P("()")]))


def _hs_dollar(w, W):
    return (_chain(w[:-1], W, O(" . "), "fn", "fn", "fn")
            + ([O(" $ ")] if len(w) > 1 else []) + [W(w[-1], "id")])


HASKELL_S = [
    _hs_lam,                                                     # λaku → masih ++ mencintaimu
    _hs_sig,                                                     # aku :: Masih → Mencintaimu
    _hs_bind,                                                    # aku ← masih ++ mencintaimu
    _hs_dollar,                                                  # aku . masih $ mencintaimu
    _c(O(" <$> "), "fn", "fn", "id"),
    _c(O(" >>= "), "fn", "fn", "id"),
    _c((" ⇒ ", "arrow"), "type", "type", "type", tf="all"),      # Aku ⇒ Masih ⇒ Mencintaimu
    _c(O(" ≠ "), "id", "id", "id"),
    _c(P(", "), "id", "id", "id", pre=[P("(")], post=[P(")")]),  # (aku, masih, mencintaimu)
    _str(""),
]


# ---- SQL (HURUF KAPITAL) -------------------------------------------------
def _sql_fn(w, W):
    return ([W(w[0].upper(), "fn"), P("(")]
            + _chain(w[1:], W, P(", "), "id", "id", "id", "up") + [P(");")])


SQL_S = [
    _c(P(", "), "id", "id", "id", "up", post=[P(";")]),          # AKU, MASIH, MENCINTAIMU;
    lambda w, W: [W("_".join(w).upper(), "id"), P(";")],         # AKU_MASIH_MENCINTAIMU;
    _sql_fn,                                                     # AKU(MASIH, MENCINTAIMU);
    _c(O(" || "), "id", "id", "id", "up", post=[P(";")]),
    _c(P(", "), "id", "id", "id", "up", pre=[P("(")], post=[P(")")]),
    _c(P("."), "type", "id", "id", "up", post=[P(";")]),         # AKU.MASIH.MENCINTAIMU;
    _c(O("::"), "id", "id", "type", "up", post=[P(";")]),
    _c(O(" * "), "id", "id", "id", "up", post=[P(";")]),
    _str(";", "'"),                                              # 'aku masih mencintaimu';
]


# ---- Lisp (string -> diwarnai tokenizer LISP: kurung pelangi per kedalaman) --
LISP_S = [
    lambda w, W: "(" + " ".join(w) + ")",
    lambda w, W: "(" + " (".join(w) + ")" * len(w),                      # (aku (masih (mencintaimu)))
    lambda w, W: "'(" + " ".join(w) + ")",
    lambda w, W: "(" + " ".join("(" + x + ")" for x in w) + ")",
    lambda w, W: "(" + "-".join(w) + ")",
    lambda w, W: "(" + w[0] + " . (" + " ".join(w[1:]) + "))",
    lambda w, W: "(" + w[0] + " [" + " ".join(w[1:]) + "])",
    lambda w, W: "'(" + " ".join('"' + x + '"' for x in w) + ")",
]


def codify(th, i, raw):
    """Baris lirik -> daftar (teks, warna). Baris diawali "=" dipakai apa adanya."""
    raw = raw.strip()
    pal, lang, kws = th["pal"], th["lang"], th["kws"]
    if raw.startswith("="):
        return lang.tokenize(raw[1:].strip())
    ws = [w.lower() for w in clean_words(raw)]

    def W(x, kind):
        if x.lower() in kws:
            kind = "kw"
        elif x.isdigit():
            kind = "num"
        return (x, kind)

    styles = th["styles"]
    out = styles[(i + len(ws)) % len(styles)](ws, W)
    if isinstance(out, str):
        return lang.tokenize(out)
    return [(t, pal.get(k, pal["id"])) for t, k in out]


# ======================================================================
#  5 TIPOGRAFI
# ======================================================================
GUT, GUT_HI = (110, 118, 129), (205, 210, 220)     # nomor baris ala VS Code (redup / baris aktif)
DEFAULT_FONTS = "dejavusansmono,consolas,menlo,couriernew"

# font = (daftar nama font dicoba berurutan, bold, italic, glyph wajib ada)
THEMES = {
    1: dict(
        name="JavaScript neon", lang=JS, styles=JS_S, pal=JS_PAL, kws=JS_KW,
        font=("jetbrainsmono,firacode,cascadiamono,consolas,menlo,dejavusansmono", False, False, ""),
        bg=((5, 9, 18), (0, 0, 0)), glow1=(22, 70, 120), glow2=(110, 55, 10),
        bokeh=[(255, 150, 50), (70, 130, 220), (60, 170, 170)],
        streak=(255, 135, 35), flower=(255, 150, 60),
        cursor=("block", (255, 32, 32)),
        scale=1.0, lh=2.1, cam_k=1.0, shake=1.0, ab=1.0, scan=False, speed=13,
        shots=[("close", 0), ("pull", -3), ("medium", 2), ("close", 0), ("push", 3),
               ("wide", -2), ("close", 2.5), ("pull", 0), ("medium", -2), ("push", 0)]),
    2: dict(
        name="Rust karat", lang=RUST, styles=RUST_S, pal=RUST_PAL, kws=RUST_KW,
        font=("sourcecodepro,ubuntumono,liberationmono,couriernew,dejavusansmono", True, False, ""),
        bg=((17, 9, 6), (2, 1, 1)), glow1=(125, 50, 15), glow2=(90, 30, 10),
        bokeh=[(255, 140, 60), (200, 90, 40), (255, 200, 120)],
        streak=(255, 120, 40), flower=None,
        cursor=("under", (255, 180, 60)),
        scale=1.08, lh=2.2, cam_k=1.2, shake=1.0, ab=0.8, scan=False, speed=11,
        shots=[("close", 0), ("push", 2), ("pull", -2), ("close", 0), ("medium", 1.5), ("push", -1.5)]),
    3: dict(
        name="Haskell ligatur", lang=HASKELL, styles=HASKELL_S, pal=HASKELL_PAL, kws=HASKELL_KW,
        font=("firacode,cascadiacode,jetbrainsmono,dejavusansmono,consolas,menlo", False, True, "λ→←⇒≠"),
        bg=((12, 6, 20), (0, 0, 4)), glow1=(90, 30, 130), glow2=(20, 90, 110),
        bokeh=[(200, 100, 255), (90, 220, 220), (255, 120, 200)],
        streak=(190, 90, 255), flower=(210, 130, 255),
        cursor=("bar", (255, 90, 200)),
        scale=0.95, lh=2.0, cam_k=0.9, shake=0.7, ab=1.0, scan=False, speed=12,
        shots=[("medium", -3), ("wide", 2), ("pull", -2.5), ("medium", 3), ("push", 2), ("wide", -3)]),
    4: dict(
        name="SQL terminal CRT", lang=SQL, styles=SQL_S, pal=SQL_PAL, kws=SQL_KW,
        font=("lucidaconsole,vt323,couriernew,consolas,dejavusansmono", True, False, ""),
        bg=((0, 9, 2), (0, 0, 0)), glow1=(10, 90, 30), glow2=(5, 60, 20),
        bokeh=[(60, 255, 120), (30, 200, 90)],
        streak=(80, 255, 130), flower=None,
        cursor=("block", (110, 255, 140)),
        scale=0.88, lh=2.0, cam_k=1.3, shake=1.7, ab=1.6, scan=True, speed=16,
        shots=[("medium", 0), ("close", 0), ("medium", 0.8), ("push", 0), ("wide", -0.8)]),
    5: dict(
        name="Lisp kurung pelangi", lang=LISP, styles=LISP_S, pal=LISP_PAL, kws=LISP_KW,
        font=("couriernew,liberationmono,ibmplexmono,menlo,dejavusansmono", False, False, ""),
        bg=((4, 10, 16), (0, 0, 2)), glow1=(20, 80, 110), glow2=(100, 40, 110),
        bokeh=[(120, 220, 255), (255, 140, 200), (150, 255, 200)],
        streak=(150, 210, 255), flower=(170, 230, 255),
        cursor=("box", (240, 245, 255)),
        scale=1.0, lh=2.15, cam_k=0.55, shake=0.35, ab=0.4, scan=False, speed=10,
        shots=[("pull", -2), ("push", 2), ("wide", 0), ("pull", 3), ("medium", -2), ("push", -3)]),
}


# ======================================================================
#  INPUT: lirik + musik
# ======================================================================
TIME_RE = re.compile(r"\[(\d+):(\d+(?:[.:]\d+)?)\]")
META_RE = re.compile(r"^\[[A-Za-z]+:.*\]$")


def parse_lyrics(path):
    entries = []
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            stamps = TIME_RE.findall(raw)
            text = re.sub(r"<\d+:\d+(?:\.\d+)?>", "", TIME_RE.sub("", raw)).strip()
            if not stamps:
                if META_RE.match(raw):
                    continue
                if text:
                    entries.append((None, text))
                continue
            if not text:
                continue
            for mm, ss in stamps:
                entries.append((int(mm) * 60 + float(ss.replace(":", ".")), text))
    if not entries:
        return [], None
    if all(t is None for t, _ in entries):
        return [t for _, t in entries], None
    last, fixed = 0.0, []
    for t, text in entries:
        if t is None:
            t = last + 3.0
        fixed.append((t, text))
        last = t
    fixed.sort(key=lambda e: e[0])
    return [t for _, t in fixed], [t for t, _ in fixed]


def find_lyrics(arg):
    if arg:
        return arg if os.path.exists(arg) else None
    for d in (os.getcwd(), BASE_DIR):
        for name in ("lyrics.txt", "lirik.txt"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def find_music(arg):
    if arg:
        return arg if os.path.exists(arg) else None
    for d in (os.getcwd(), BASE_DIR):
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        audio = [n for n in names if os.path.splitext(n)[1].lower() in AUDIO_EXT
                 and not n.endswith(".ogg")]
        pref = [n for n in audio if os.path.splitext(n)[0].lower() in ("music", "lagu", "song", "audio")]
        for n in pref + audio:
            return os.path.join(d, n)
    return None


# ======================================================================
#  TEKSTUR
# ======================================================================
def make_bg(w, h, top, bottom):
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surf, tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
                         (0, y), (w, y))
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


def make_streak(h, color):
    w = 80
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        a = int(255 * math.exp(-(((x - w / 2) / 15) ** 2)))
        pygame.draw.line(surf, (*color, a), (x, 0), (x, h))
    return pygame.transform.rotozoom(surf, -7, 1.0)


def make_flower(color, size=200):
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
        pygame.draw.polygon(surf, (*color, 255), pts, 2)
    pygame.draw.circle(surf, (*color, 255), (int(c), int(c)), 5, 2)
    return surf


def make_scanlines(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(surf, (0, 0, 0, 75), (0, y), (w, y))
    return surf


# ======================================================================
#  APLIKASI
# ======================================================================
class App:
    def __init__(self, th, num, texts, times, music, offset, loop, fullscreen):
        pygame.init()
        self.th, self.num = th, num
        self.texts = texts
        self.tokens = [codify(th, i, t) for i, t in enumerate(texts)]
        self.code = ["".join(s for s, _ in tk) for tk in self.tokens]
        self.times = times
        self.offset = offset
        self.loop = loop
        self.fullscreen = fullscreen
        self.cache = {}
        flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((0, 0) if fullscreen else WINDOW_SIZE, flags)
        pygame.display.set_caption(f"cine.py - typ {num}: {th['name']}")
        self.clock = pygame.time.Clock()
        self.on_resize()
        self.audio_ok = self.setup_audio(music) if music else False
        self.restart()

    # ---------- audio ----------
    def setup_audio(self, path):
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
        print("[AUDIO] Coba: ffmpeg -i musik.mp3 musik.ogg")
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

    # ---------- aset ----------
    _FP = {}

    @staticmethod
    def load_font(size, spec=None):
        names, bold, italic, need = spec or (DEFAULT_FONTS, False, False, "")
        f = None
        for n in names.split(","):
            n = n.strip()
            if n not in App._FP:
                App._FP[n] = pygame.font.match_font(n)
            p = App._FP[n]
            if not p:
                continue
            try:
                cand = pygame.font.Font(p, size)
                if need and not has_glyphs(cand, need):
                    continue
            except Exception:
                continue
            f = cand
            break
        if f is None:
            for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                      "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                      "C:/Windows/Fonts/consola.ttf", "/System/Library/Fonts/Menlo.ttc"):
                if os.path.exists(p):
                    f = pygame.font.Font(p, size)
                    break
        if f is None:
            f = pygame.font.SysFont("consolas,dejavusansmono,menlo,couriernew,monospace", size)
        try:
            if bold:
                f.set_bold(True)
            if italic:
                f.set_italic(True)
        except Exception:
            pass
        return f

    def on_resize(self):
        th = self.th
        w, h = self.screen.get_size()
        size = max(16, int(min(w, h * 0.56) / 12 * th["scale"]))
        spec = th["font"]
        self.font = self.load_font(size, spec)
        self.small = self.load_font(max(10, int(size * 0.62)), (spec[0], False, False, ""))
        self.fh = self.font.get_height()
        self.PAD = 12
        self.LH = int(self.fh * th["lh"])
        self.line_h = self.fh + self.PAD * 2
        self.char_w = self.font.size("M")[0]
        need = spec[3]
        if need and not getattr(self, "ascii_ops", False) and not has_glyphs(self.font, need):
            self.ascii_ops = True
            print("[FONT] font tidak punya simbol ligatur -> pakai ASCII (\\ -> <- => /=)")
            self.tokens = [[(t.translate(ASCII_OPS), c) for t, c in tk] for tk in self.tokens]
            self.code = ["".join(s for s, _ in tk) for tk in self.tokens]
        digits = max(2, len(str(len(self.code))))      # nomor baris ala VS Code, rata kanan
        gw = self.small.size("0")[0]
        self.NUMTXT_W = gw * digits
        self.NUM_W = int(gw * (digits + 2.2))
        self.cache.clear()

        self.bg = make_bg(w, h, *th["bg"])
        self.vig = make_vignette(w, h)
        self.glow_a = make_radial(th["glow1"], int(w * 1.5))
        self.glow_b = make_radial(th["glow2"], int(w * 1.1))
        self.streak_img = make_streak(int(h * 1.5), th["streak"]) if th["streak"] else None
        self.flower_img = make_flower(th["flower"]) if th["flower"] else None
        self.tex = [make_soft_circle(c, 40) for c in th["bokeh"]]
        self.scan = make_scanlines(w, h) if th["scan"] else None
        self.dense = self.make_dense(w, h) if FX["dense_code"] else None
        rnd = random.Random(3)
        self.particles = [{
            "x": rnd.uniform(0, w), "y": rnd.uniform(0, h),
            "vy": rnd.uniform(-14, -4), "s": rnd.uniform(0.5, 1.6),
            "tex": rnd.randrange(len(self.tex)), "a": rnd.uniform(40, 110),
            "ph": rnd.uniform(0, 6.28)} for _ in range(14)]

    def make_dense(self, w, h):
        W, H = int(w * 1.4), int(h * 1.4)
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        f = self.load_font(max(9, int(self.fh * 0.36)), self.th["font"])
        rnd = random.Random(7)
        row_h = int(f.get_height() * 1.3)
        toks = self.tokens or [[("...", (120, 120, 120))]]
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
        self.t = 0.0
        self.song_t = 0.0
        self.zoom = 1.0
        self.roll = 0.0
        self.cam_x = 0.45 * self.screen.get_width()
        self.cam_y = 0.0
        self.sway = (0.0, 0.0)
        self.punch = 0.0
        self.shake = 0.0
        self.idle = 0.0
        self.end_t0 = None
        self.streaks = []
        self.flowers = []
        if self.audio_ok:
            pygame.mixer.music.play()

    def is_typing(self):
        return not self.finished and self.typed < len(self.code[self.idx])

    def update(self, dt):
        self.t += dt
        self.update_fx(dt)
        if self.paused or self.finished:
            return
        if self.times:
            self.update_timed(dt)
            return
        line = self.code[self.idx]
        if self.typed < len(line):
            self.typed = min(len(line), self.typed + dt * self.th["speed"] * random.uniform(0.6, 1.4))
            return
        self.wait += dt
        if self.wait >= 1.1:
            self.wait = 0.0
            if self.idx + 1 < len(self.code):
                self.idx += 1
                self.typed = 0.0
            elif self.loop:
                self.restart()
            else:
                self.finished = True

    def update_timed(self, dt):
        pos = -1
        if self.audio_ok:
            pos = pygame.mixer.music.get_pos()
        if pos >= 0:
            self.song_t = pos / 1000.0
        else:
            self.song_t += dt
        now = self.song_t + self.offset
        T = self.times
        i = 0
        while i + 1 < len(T) and T[i + 1] <= now:
            i += 1
        self.idx = i
        nxt = T[i + 1] if i + 1 < len(T) else T[i] + 3.0
        dur = clamp(nxt - T[i] - 0.25, 0.4, 4.5)
        speed = max(len(self.code[i]) / dur, 6)
        self.typed = min(len(self.code[i]), max(0.0, (now - T[i]) * speed))
        if now > T[-1] + 4.0 and self.loop:
            self.restart()
        elif now > T[-1] + 4.0 and not (self.audio_ok and pygame.mixer.music.get_busy()):
            self.finished = True

    # ---------- kamera & efek ----------
    def shot_targets(self):
        mode, roll_t = self.th["shots"][self.idx % len(self.th["shots"])]
        p = self.typed / max(1, len(self.code[self.idx]))
        z = {"close": 1.75, "medium": 1.45, "wide": 1.25}.get(mode)
        if z is None:
            z = 1.9 - 0.5 * p if mode == "pull" else 1.25 + 0.5 * p
        return z, roll_t

    def full_w(self, i):
        return self.line_surface(i, len(self.code[i]), False)[0].get_width()

    def fit_zoom(self):
        """Zoom maksimum supaya baris aktif (dan baris di atasnya) muat penuh di layar."""
        W = self.screen.get_width()
        fw = max(self.full_w(j) for j in (self.idx, self.idx - 1) if j >= 0)
        return 0.86 * W / fw

    def update_fx(self, dt):
        W, H = self.screen.get_size()
        k = self.th["cam_k"]
        self.idle = 0.0 if self.is_typing() else self.idle + dt   # lama jeda (detik)
        if self.idx != self.last_idx:
            self.last_idx = self.idx
            self.on_new_line()
        self.scroll += (self.idx - self.scroll) * min(1.0, dt * 6)
        self.punch = max(0.0, self.punch - dt * 3.0)
        self.shake = max(0.0, self.shake - dt * 4.0)

        zt, rt = self.shot_targets()
        pause = self.idle > 0.7 or self.finished
        if pause:                                  # jeda: zoom out sebentar, seluruh baris kelihatan
            zt = min(0.85, self.fit_zoom())
        self.zoom += (zt - self.zoom) * min(1.0, dt * 3.2 * k)
        self.roll += (rt * 0.5 - self.roll) * min(1.0, dt * 2.5 * k)

        z = max(0.1, self.zoom)
        if pause:
            cx_t = 0.45 * W / z                    # tepi kiri teks di margin kiri layar
        else:                                      # mengetik: kamera dekat, ikut kursor
            _, x_end = self.line_surface(self.idx, self.typed, True)
            cx_t = max(0.45 * W / z, x_end - 0.18 * W / z)
        self.cam_x += (cx_t - self.cam_x) * min(1.0, dt * 7)
        self.cam_y = self.scroll * self.LH + self.line_h / 2

        t = self.t
        sh = self.shake * self.th["shake"] if FX["shake"] else 0
        self.sway = (math.sin(t * 0.9) * 5 + math.sin(t * 1.7) * 2.5 + random.uniform(-1, 1) * sh * 9,
                     math.cos(t * 0.7) * 4 + math.sin(t * 2.1) * 2 + random.uniform(-1, 1) * sh * 9)

    def on_new_line(self):
        W, H = self.screen.get_size()
        self.punch = 1.0
        self.shake = 1.0
        if self.idx == len(self.code) - 1 and self.idx > 0:   # baris terakhir mulai -> kode latar muncul sekali
            self.end_t0 = self.t
        if FX["streaks"] and self.streak_img and random.random() < 0.6:
            self.streaks.append({"t0": self.t, "life": random.uniform(1.6, 2.6),
                                 "x": random.uniform(0.15, 0.85) * W,
                                 "vx": random.uniform(-40, 40), "peak": random.uniform(70, 130)})
        if self.flower_img and random.random() < 0.35:
            self.flowers.append({"t0": self.t, "life": 3.4,
                                 "x": random.uniform(0.2, 0.8) * W,
                                 "y": random.uniform(0.08, 0.3) * H})

    # ---------- permukaan baris ----------
    def line_surface(self, i, chars, cursor_on):
        n = int(chars)
        cur = i == self.idx
        key = (i, n, cursor_on, cur)
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
        surf = pygame.Surface((x_end + cw * 2 + pad * 2 + 6, fh + pad * 2), pygame.SRCALPHA)
        g = self.small.render(str(i + 1), True, GUT_HI if cur else GUT)
        surf.blit(g, (pad + self.NUMTXT_W - g.get_width(), pad + (fh - g.get_height()) // 2))
        x = pad + self.NUM_W
        for r in rendered:
            surf.blit(r, (x, pad))
            x += r.get_width()
        if cursor_on:
            shape, col = self.th["cursor"]
            cx0 = x + 3
            if shape == "block":
                pygame.draw.rect(surf, col, (cx0, pad + int(fh * 0.04), cw, int(fh * 0.92)))
            elif shape == "under":
                pygame.draw.rect(surf, col, (cx0, pad + int(fh * 0.88), int(cw * 1.4), max(3, fh // 10)))
            elif shape == "bar":
                pygame.draw.rect(surf, col, (cx0, pad + int(fh * 0.05), max(3, cw // 4), int(fh * 0.9)))
            else:
                pygame.draw.rect(surf, col, (cx0, pad + int(fh * 0.04), cw, int(fh * 0.92)), 2)
        if len(self.cache) > 400:
            self.cache.clear()
        self.cache[key] = (surf, x_end)
        return surf, x_end

    # ---------- gambar ----------
    def to_screen(self, wx, wy, depth_scale):
        W, H = self.screen.get_size()
        z = self.zoom * (1 + 0.05 * self.punch)
        fy = H * 0.46
        ax = W / 2 - self.cam_x * z + self.sway[0]          # posisi tepi kiri teks
        sx = W / 2 + (wx - self.cam_x) * z + self.sway[0]
        sy = fy + (wy - self.cam_y) * z + self.sway[1]
        sx = ax + (sx - ax) * depth_scale
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
        scr, th = self.screen, self.th
        W, H = scr.get_size()
        t = self.t
        z_eff = self.zoom * (1 + 0.05 * self.punch)
        scr.blit(self.bg, (0, 0))

        ga, gb = self.glow_a, self.glow_b
        scr.blit(ga, (int(W * 0.3 + math.sin(t * 0.25) * W * 0.15) - ga.get_width() // 2,
                      int(H * 0.30) - ga.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
        scr.blit(gb, (int(W * 0.78 + math.cos(t * 0.2) * W * 0.1) - gb.get_width() // 2,
                      int(H * 0.72) - gb.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)

        if self.dense is not None and self.end_t0 is not None:
            age = self.t - self.end_t0
            da = math.sin(math.pi * age / END_FX) * 170 if 0 <= age <= END_FX else 0
            if da > 5:
                self.dense.set_alpha(int(da))
                dw, dh = self.dense.get_size()
                scr.blit(self.dense, (-(dw - W) // 2 + int(math.sin(t * 0.3) * 25),
                                      -(dh - H) // 2 + int(math.cos(t * 0.22) * 25 - self.scroll * 10 % 40)))

        for s in self.streaks[:]:
            age = t - s["t0"]
            if age > s["life"]:
                self.streaks.remove(s)
                continue
            img = self.streak_img
            img.set_alpha(int(math.sin(math.pi * age / s["life"]) * s["peak"]))
            scr.blit(img, (int(s["x"] + s["vx"] * age) - img.get_width() // 2, -int(H * 0.25)))

        if FX["bokeh"]:
            for p in self.particles:
                p["y"] += p["vy"] / FPS
                if p["y"] < -60:
                    p["y"] = H + 60
                x = (p["x"] - self.cam_x * 0.06 * z_eff) % (W + 120) - 60
                size = int(80 * p["s"])
                img = pygame.transform.smoothscale(self.tex[p["tex"]], (size, size))
                img.set_alpha(int(p["a"] * (0.6 + 0.4 * math.sin(t * 0.8 + p["ph"]))))
                scr.blit(img, (int(x) - size // 2, int(p["y"]) - size // 2))

        for f in self.flowers[:]:
            age = t - f["t0"]
            if age > f["life"]:
                self.flowers.remove(f)
                continue
            img = pygame.transform.rotozoom(self.flower_img, age * 22, 0.9 + 0.3 * age / f["life"])
            img.set_alpha(int(math.sin(math.pi * age / f["life"]) * 150))
            scr.blit(img, img.get_rect(center=(int(f["x"]), int(f["y"]))))

        idx = self.idx
        cursor_on = self.is_typing() or int(t * 2) % 2 == 0
        for i in range(max(0, idx - 5), idx + 1):
            d = max(0.0, self.scroll - i)
            is_cur = i == idx
            if is_cur:
                surf, _ = self.line_surface(i, self.typed, cursor_on)
                key = (i, int(self.typed), cursor_on, True)
            else:
                surf, _ = self.line_surface(i, len(self.code[i]), False)
                key = (i, len(self.code[i]), False, False)
            alpha = 255 if d <= 0.05 else 255 - 78 * d
            ds = max(0.5, 1 - 0.09 * d)
            blur = 1.0 + 1.0 * d
            wx = surf.get_width() / 2
            wy = i * self.LH + self.line_h / 2
            cx, cy = self.to_screen(wx, wy, ds)
            scale = z_eff * ds
            angle = self.roll
            if is_cur and FX["glow"]:
                self.put(surf, key + ("glow",), cx, cy, scale, angle, 120, blur=3.0)
            self.put(surf, key, cx, cy, scale, angle, alpha, blur)
            if is_cur and FX["reflection"]:
                flipped = pygame.transform.flip(surf, False, True)
                rcx, rcy = self.to_screen(wx, wy + self.line_h * 0.95, ds)
                self.put(flipped, key + ("ref",), rcx, rcy, scale, angle, 42, blur=2.5)

        scr.blit(self.vig, (0, 0))
        if self.scan is not None:
            self.scan.set_alpha(random.randint(190, 255))
            scr.blit(self.scan, (0, 0))
        if FX["aberration"]:
            self.aberrate(self.punch * th["ab"])
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
                    if e.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
                        self.offset += 0.1 if e.key == pygame.K_RIGHTBRACKET else -0.1
                        print(f"offset sinkron: {self.offset:+.1f}s  (pakai -o {self.offset:+.1f} biar permanen)")
                    if e.key == pygame.K_f:
                        self.fullscreen = not self.fullscreen
                        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
                        self.screen = pygame.display.set_mode((0, 0) if self.fullscreen else WINDOW_SIZE, flags)
                        self.on_resize()
            self.update(dt)
            self.draw()


# ======================================================================
#  CLI
# ======================================================================
def main():
    ap = argparse.ArgumentParser(
        prog="cine.py", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Lirik sinematik bergaya kode. Baca lyrics.txt (LRC) + file musik.",
        epilog="\n".join(["tipografi:"] + [f"  -typ {k}  {v['name']}" for k, v in THEMES.items()]))
    ap.add_argument("-typ", "--typ", type=int, default=1, choices=sorted(THEMES), metavar="1-5",
                    help="pilih tipografi 1-5 (default 1)")
    ap.add_argument("-l", "--lyrics", help="path lirik (default: lyrics.txt)")
    ap.add_argument("-m", "--music", help="path musik (default: otomatis cari di folder)")
    ap.add_argument("-o", "--offset", type=float, default=0.0,
                    help="geser sinkron lirik dalam detik (+ = lebih cepat)")
    ap.add_argument("--no-loop", action="store_true", help="jangan ulang otomatis (default: looping terus)")
    ap.add_argument("--fullscreen", action="store_true", help="mulai fullscreen")
    args = ap.parse_args()

    lyr = find_lyrics(args.lyrics)
    if not lyr:
        sys.exit("lyrics.txt tidak ditemukan. Taruh di folder yang sama dengan cine.py "
                 "(format: [mm:ss.xx] teks) atau pakai  -l path/lirik.txt")
    texts, times = parse_lyrics(lyr)
    if not texts:
        sys.exit(f"{lyr} kosong / tidak ada baris lirik yang terbaca.")
    music = find_music(args.music)
    print(f"[LIRIK] {lyr}  ({len(texts)} baris, {'dengan' if times else 'TANPA'} timestamp)")
    if music:
        print(f"[MUSIK] {music}")
    else:
        print("[MUSIK] tidak ditemukan -> jalan tanpa suara (taruh music.mp3 atau pakai -m)")
    if not times:
        print("[INFO] tanpa timestamp: baris diketik dengan kecepatan tetap.")

    th = THEMES[args.typ]
    try:
        App(th, args.typ, texts, times, music, args.offset, not args.no_loop, args.fullscreen).run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()