#!/usr/bin/env python3
"""Generate every image used by the profile README (English and Russian).

All text is converted to SVG outlines (fonts in scripts/fonts, OFL) and all
logos are inlined from scripts/icons (Devicon — MIT, Simple Icons — CC0),
so the SVGs have no external dependencies and render the same everywhere.

Output layout:
    assets/{light,dark}/*.svg        English, per theme (README switches with <picture>)
    assets/ru/{light,dark}/*.svg     Russian
    assets/static/[ru/]{theme}/      motion-free copies of animated assets
    assets/stack/*.svg               logo tiles (theme-independent)

Usage:
    GH_TOKEN=$(gh auth token) python3 scripts/build_assets.py

Token lookup order: GH_STATS_TOKEN, GH_TOKEN, GITHUB_TOKEN. Without a token
the GitHub stats cards are skipped and the previous files are kept.
Requires: fonttools, uharfbuzz.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONTS = Path(__file__).resolve().parent / "fonts"
ICONS = Path(__file__).resolve().parent / "icons"

LOGIN = "samnesvoj"
CODEWARS_USER = "ex-lain"
# Not original work (recovered third-party code) or empty — excluded from stats.
EXCLUDED_REPOS = {"yuvelirochka", "dzen-rss", LOGIN}

# Every Japanese string used below; make_fonts.py subsets the fonts to these.
JP_TEXT = "ソーニャコードで、ものをつくる創わたしについて技術作品活動記録学習中連絡先またね日本語機材"

# ── palette ────────────────────────────────────────────────────────────────
PINK = "#D8A7BC"
BLUSH = "#F2DCE5"
LAVENDER = "#B7ADB9"
CHARCOAL = "#28262D"
GRAPHITE = "#1B1A20"
PEARL = "#F5F1F4"

THEMES = {
    "dark": dict(name="dark", bg0=GRAPHITE, bg1="#24222A", card=CHARCOAL, card2="#2E2B33", line="#3A3640",
                 text=PEARL, muted=LAVENDER, soft="#8C8291", accent=PINK, petal=BLUSH,
                 petal_edge=PINK, branch="#4B4351", moon0="#F6E9EF", moon1="#DDB3C5",
                 glow=PINK, wave=LAVENDER, seal=PINK, seal_text=GRAPHITE),
    "light": dict(name="light", bg0=PEARL, bg1="#F1E4EA", card="#FBF8FA", card2="#F6EEF2", line="#E8D9E1",
                  text=CHARCOAL, muted="#6E6473", soft="#9C90A0", accent="#B07890", petal="#FFF8FB",
                  petal_edge=PINK, branch="#857684", moon0="#FBEFF4", moon1="#EBC6D6",
                  glow=PINK, wave="#B7ADB9", seal="#C48DA5", seal_text=PEARL),
}
# heatmap: zero → most
HEAT = {
    "dark": ["#2E2B33", "#5A4652", "#86627A", "#B385A0", PINK],
    "light": ["#EFE6EB", "#EDD1DD", "#DFB2C5", "#C98FA9", "#A86E88"],
}
LANG_SHADES = [PINK, LAVENDER, "#8E6F82", BLUSH, "#6D6472", "#E7C3D3"]

W = 860

# ── copy ───────────────────────────────────────────────────────────────────
HEADINGS_ALL = {"about": "about me", "stack": "tech stack", "hardware": "hardware & homelab", "projects": "projects",
                "activity": "github & codewars", "learning": "currently learning", "find": "contact"}
SPOKEN = [("русский", "", ""), ("english", "", "B1"), ("日本語", "", "")]

TX = {
    "en": dict(
        hello="hello, i'm",
        sub="software engineer | backend | ai/ml | full stack",
        featured="main project",
        featured_desc=["A platform that automatically processes long videos into",
                       "short clips: computer vision, speech recognition, LLMs, GPUs."],
        private_repo="sonya.group → · private repository",
        thanks="thanks for stopping by",
        gh_label="github · last 12 months",
        stat_labels=["contributions", "active days", "projects"],
        contrib_label="contributions",
        weekdays=["mon", "wed", "fri"],
        months=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
        contrib_total="{n} contributions in the last year",
        less="less", more="more",
        kata="kata solved", honor="honor",
        headings=HEADINGS_ALL,
        background="background",
        spoken_label="languages i speak",
        cards={
            "pylens": ("PyLens", "interactive python learning",
                       ["Python built-ins with examples, visualizations,",
                        "an example generator and tests."], "open →"),
            "group-bot": ("SONYA GROUP Bot", "telegram bot for the sonya platform",
                          ["Sign-up, document consent and Mini App access.",
                           "aiogram 3, SQLite, automated tests."], "github →"),
            "automation": ("Content Automation", "custom pipelines & automation",
                           ["Zen and TikTok: data collection, LLMs, generation,",
                            "Telegram approval and publishing."], "private repositories"),
            "aminelli": ("Aminelli", "flower brand website",
                         ["Responsive interface, catalog and",
                          "1C integration. React, Vite."], "lookbook →"),
            "taplinks": ("Custom Web Projects", "websites · landing pages · taplink",
                         ["Websites, landing pages, Taplink pages and",
                          "small web apps for businesses."], "example →"),
            "gforms": ("Google Forms & Apps Script", "custom google forms built in code",
                       ["Forms with custom logic, Google Sheets,",
                        "notifications and integrations."], "on request"),
        },
        learning=[("c++ middle", "yandex practicum"),
                  ("modern c++", "memory · templates"),
                  ("performance", "systems · hpc · low latency")],
        spoken=SPOKEN,
        hardware=[("macos", "Mac mini M4", "16 GB RAM · 256 GB SSD"), ("macos", "MacBook M5", "macOS"),
                  ("windows", "Windows PC", "windows"), ("linux", "Linux laptop", "linux"),
                  ("linux", "Linux VMs", "virtual machines"), (None, "Home NAS", "homelab")],
        badges={"university": "first-year applied informatics student · kubsau",
                "timeweb": "timeweb cloud partner",
                "apple": "apple developer certificate",
                "gosuslugi": "verified it skills on gosuslugi",
                "education": "academy of design and programming (nadip) · javascript, css, machine learning"},
    ),
    "ru": dict(
        hello="привет, я",
        sub="software engineer | backend | ai/ml | full stack",
        featured="основной проект",
        featured_desc=["Платформа для автоматической обработки длинных видео",
                       "и создания коротких роликов: CV, речь, LLM и GPU."],
        private_repo="sonya.group → · репозиторий приватный",
        thanks="спасибо, что заглянули",
        gh_label="github · последние 12 месяцев",
        stat_labels=["контрибуции", "активные дни", "проекты"],
        contrib_label="контрибуции",
        weekdays=["пн", "ср", "пт"],
        months=["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
        contrib_total="контрибуций за последний год: {n}",
        less="меньше", more="больше",
        kata="решённые ката", honor="honor",
        headings=HEADINGS_ALL,
        background="background",
        spoken_label="languages i speak",
        cards={
            "pylens": ("PyLens", "интерактивное изучение python",
                       ["Встроенные функции Python: примеры,",
                        "визуализации, генератор примеров и тесты."], "открыть →"),
            "group-bot": ("SONYA GROUP Bot", "telegram-бот платформы sonya",
                          ["Регистрация, согласия с документами",
                           "и доступ к Mini App. aiogram 3, SQLite, тесты."], "github →"),
            "automation": ("Content Automation", "пайплайны и автоматизация на заказ",
                           ["Дзен и TikTok: данные, LLM, генерация,",
                            "согласование в Telegram и публикация."], "репозитории приватные"),
            "aminelli": ("Аминелли", "сайт цветочного бренда",
                         ["Адаптивный интерфейс, каталог",
                          "и интеграция с 1С. React, Vite."], "лукбук →"),
            "taplinks": ("Custom Web Projects", "сайты · лендинги · taplink",
                         ["Сайты, лендинги, Taplink-страницы и",
                          "небольшие веб-приложения для бизнеса."], "пример →"),
            "gforms": ("Google Forms & Apps Script", "google формы на заказ с помощью кода",
                       ["Индивидуальная логика, Google Таблицы,",
                        "уведомления и интеграции."], "на заказ"),
        },
        learning=[("c++ middle", "яндекс практикум"),
                  ("современный c++", "память и шаблоны"),
                  ("производительность", "системы · hpc · low latency")],
        spoken=SPOKEN,
        hardware=[("macos", "Mac mini M4", "16 ГБ RAM · 256 ГБ SSD"), ("macos", "MacBook M5", "macOS"),
                  ("windows", "ПК на Windows", "windows"), ("linux", "Ноутбук на Linux", "linux"),
                  ("linux", "Linux VM", "виртуальные машины"), (None, "Домашний NAS", "домашняя инфраструктура")],
        badges={"university": "1 курс · прикладная информатика · кубгау",
                "timeweb": "партнёр timeweb cloud",
                "apple": "сертификат apple developer",
                "gosuslugi": "подтверждённые it-компетенции на госуслугах",
                "education": "академия дизайна и программирования надип · javascript, css, машинное обучение"},
    ),
}

# (key, title en, title ru, logos, also en, also ru) — "also" lists tools without a logo
STACK = [
    ("languages", "languages", "languages",
     ["python", "cpp", "swift", "javascript", "typescript", "html", "css", "bash"], "sql", "sql"),
    ("web", "frontend & backend", "frontend & backend",
     ["react", "nextjs", "nodejs", "fastapi", "vite", "tailwind", "framer", "threejs", "pydantic",
      "postgresql", "sqlite", "supabase"],
     "rest api · webhooks · apscheduler · payment integrations",
     "rest api · webhooks · apscheduler · payment integrations"),
    ("ai", "ai & computer vision", "ai & computer vision",
     ["opencv", "numpy", "mediapipe", "ffmpeg", "openai", "gemini"],
     "yolo11 · faster-whisper · pyscenedetect · yt-dlp · openrouter",
     "yolo11 · faster-whisper · pyscenedetect · yt-dlp · openrouter"),
    ("automation", "automation", "automation",
     ["n8n", "claude", "appsscript", "gforms", "gsheets", "telegram"],
     "aiogram · telegraf · telegram mini apps · apify", "aiogram · telegraf · telegram mini apps · apify"),
    ("infra", "infrastructure", "infrastructure",
     ["docker", "git", "actions", "linux", "nginx", "s3", "yandexcloud", "vercel", "pytest"],
     "timeweb cloud · vast.ai · systemd · ghcr", "timeweb cloud · vast.ai · systemd · ghcr"),
    ("platforms", "platforms", "platforms",
     ["macos", "windows", "cuda", "amd"], "", ""),
]

HEADING_JP = {"about": "わたしについて", "stack": "技術", "hardware": "機材", "projects": "作品", "activity": "活動記録",
              "learning": "学習中", "find": "連絡先"}

CARD_STACKS = {
    "pylens": ["typescript", "nextjs", "react", "tailwind", "framer"],
    "group-bot": ["python", "telegram", "sqlite", "pytest"],
    "automation": ["n8n", "python", "javascript", "supabase", "telegram"],
    "aminelli": ["react", "typescript", "vite", "tailwind"],
    "taplinks": ["html", "css", "javascript"],
    "gforms": ["appsscript", "gforms", "gsheets"],
}
BADGE_ICONS = {"apple": "si-apple.svg"}
LEARNING_LOGOS = ["cpp", "cmake", "linux"]

LOC = "en"


def tr(key: str):
    return TX[LOC][key]


# ── typography: text → outlines ────────────────────────────────────────────
def _num(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Font:
    def __init__(self, name: str):
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont

        path = FONTS / name
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def _shape(self, text: str, direction: str = "ltr"):
        import uharfbuzz as hb

        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        buf.direction = direction
        hb.shape(self.hb_font, buf, {"kern": True, "liga": True})
        for info in buf.glyph_infos:
            if info.codepoint == 0:
                raise ValueError(f"missing glyph in {text!r} — rerun make_fonts.py")
        return buf.glyph_infos, buf.glyph_positions

    def _glyph(self, gid: int, s: float, x: float, y: float) -> str:
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen

        pen = SVGPathPen(self.gs, ntos=_num)
        self.gs[self.order[gid]].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
        return pen.getCommands()

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        _, pos = self._shape(text)
        return sum(p.x_advance for p in pos) * size / self.upem + tracking * size * (len(pos) - 1)

    def fit(self, text: str, size: float, max_w: float, tracking: float = 0) -> float:
        """Largest size ≤ `size` at which the text fits in max_w."""
        w = self.width(text, size, tracking)
        return size if w <= max_w else size * max_w / w

    def glyphs(self, text: str, size: float, x: float, y: float, anchor: str = "start",
               tracking: float = 0) -> list[str]:
        """Path data per visible glyph."""
        infos, pos = self._shape(text)
        s = size / self.upem
        x -= {"start": 0, "middle": .5, "end": 1}[anchor] * self.width(text, size, tracking)
        out = []
        for info, p in zip(infos, pos):
            d = self._glyph(info.codepoint, s, x + p.x_offset * s, y - p.y_offset * s)
            if d:
                out.append(d)
            x += p.x_advance * s + tracking * size
        return out

    def text(self, text: str, size: float, x: float, y: float, fill: str, anchor: str = "start",
             tracking: float = 0, attrs: str = "", max_w: float | None = None) -> str:
        if max_w:
            size = self.fit(text, size, max_w, tracking)
        d = "".join(self.glyphs(text, size, x, y, anchor, tracking))
        return f'<path d="{d}" fill="{fill}"{attrs}/>'

    def vertical(self, text: str, size: float, cx: float, top: float, fill: str) -> str:
        """Top-to-bottom Japanese text centred on cx (uses the font's vert features)."""
        infos, pos = self._shape(text, "ttb")
        s = size / self.upem
        px = py = 0
        ds = []
        for info, p in zip(infos, pos):
            ds.append(self._glyph(info.codepoint, s, cx + (px + p.x_offset) * s, top - (py + p.y_offset) * s))
            px += p.x_advance
            py += p.y_advance
        return f'<path d="{"".join(ds)}" fill="{fill}"/>'


DISPLAY = ITALIC = SANS = SANS_M = MINCHO = None  # loaded in main()


def load_fonts() -> None:
    global DISPLAY, ITALIC, SANS, SANS_M, MINCHO
    DISPLAY, ITALIC = Font("display.ttf"), Font("display-italic.ttf")
    SANS, SANS_M, MINCHO = Font("sans.ttf"), Font("sans-medium.ttf"), Font("mincho.ttf")


# ── logos ──────────────────────────────────────────────────────────────────
# key: (label, icon file, colour for single-colour marks or None to keep the original)
LOGOS = {
    "python": ("Python", "dv-python-original.svg", None),
    "cpp": ("C++", "dv-cplusplus-original.svg", None),
    "swift": ("Swift", "dv-swift-original.svg", None),
    "javascript": ("JavaScript", "dv-javascript-original.svg", None),
    "typescript": ("TypeScript", "dv-typescript-original.svg", None),
    "html": ("HTML", "dv-html5-original.svg", None),
    "css": ("CSS", "dv-css3-original.svg", None),
    "bash": ("Bash", "si-gnubash.svg", PEARL),
    "react": ("React", "dv-react-original.svg", None),
    "nextjs": ("Next.js", "dv-nextjs-original.svg", None),
    "nodejs": ("Node.js", "dv-nodejs-original.svg", None),
    "vite": ("Vite", "dv-vitejs-original.svg", None),
    "tailwind": ("Tailwind CSS", "dv-tailwindcss-original.svg", None),
    "framer": ("Framer Motion", "dv-framermotion-original.svg", PEARL),
    "threejs": ("Three.js", "si-threedotjs.svg", PEARL),
    "fastapi": ("FastAPI", "dv-fastapi-original.svg", None),
    "pydantic": ("Pydantic", "si-pydantic.svg", "#E92063"),
    "postgresql": ("PostgreSQL", "dv-postgresql-original.svg", None),
    "sqlite": ("SQLite", "dv-sqlite-original.svg", None),
    "supabase": ("Supabase", "dv-supabase-original.svg", None),
    "telegram": ("Telegram Bot API & Mini Apps", "si-telegram.svg", "#26A5E4"),
    "opencv": ("OpenCV", "dv-opencv-original.svg", None),
    "numpy": ("NumPy", "dv-numpy-original.svg", None),
    "mediapipe": ("MediaPipe", "si-mediapipe.svg", "#0097A7"),
    "ffmpeg": ("FFmpeg", "si-ffmpeg.svg", "#2E9E3A"),
    "openai": ("OpenAI API", "si-openai.svg", PEARL),
    "gemini": ("Gemini API", "si-googlegemini.svg", "#8E75B2"),
    "n8n": ("n8n", "si-n8n.svg", "#EA4B71"),
    "claude": ("Claude Code", "si-claude.svg", "#D97757"),
    "macos": ("macOS", "si-apple.svg", PEARL),
    "cuda": ("NVIDIA CUDA", "si-nvidia.svg", "#76B900"),
    "amd": ("AMD", "si-amd.svg", PEARL),
    "docker": ("Docker", "dv-docker-original.svg", None),
    "git": ("Git", "dv-git-original.svg", None),
    "github": ("GitHub", "si-github.svg", PEARL),
    "actions": ("GitHub Actions", "dv-githubactions-original.svg", None),
    "linux": ("Linux", "si-linux.svg", PEARL),
    "nginx": ("Nginx", "dv-nginx-original.svg", None),
    "s3": ("S3 storage", "si-amazons3.svg", "#569A31"),
    "yandexcloud": ("Yandex Cloud", "si-yandexcloud.svg", "#5282FF"),
    "vercel": ("Vercel", "si-vercel.svg", PEARL),
    "pytest": ("pytest", "dv-pytest-original.svg", None),
    "cmake": ("CMake", "dv-cmake-original.svg", None),
    "windows": ("Windows", "dv-windows11-original.svg", None),
    "appsscript": ("Google Apps Script", "si-googleappsscript.svg", "#4285F4"),
    "gforms": ("Google Forms", "si-googleforms.svg", "#7248B9"),
    "gsheets": ("Google Sheets", "si-googlesheets.svg", "#34A853"),
}

_logo_seq = 0


def logo(key: str, x: float, y: float, size: float, colour: str | None = None, file: str | None = None) -> str:
    """Inline a logo as a nested <svg>; ids are prefixed so several can share a file."""
    global _logo_seq
    _logo_seq += 1
    if file is None:
        _, file, mono = LOGOS[key]
        colour = colour or mono
    src = (ICONS / file).read_text(encoding="utf-8")
    src = re.sub(r"<\?xml.*?\?>|<!--.*?-->|<title>.*?</title>", "", src, flags=re.S)
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, flags=re.S).group(1).strip()
    p = f"l{_logo_seq}_"
    inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{p}{m.group(1)}"', inner)
    inner = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{p}{m.group(1)})", inner)
    inner = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}{m.group(1)}"', inner)
    if colour:
        inner = re.sub(r'\sfill="[^"]*"', "", inner)
    fill_attr = f' fill="{colour}"' if colour else ""
    return (f'<svg x="{_num(x)}" y="{_num(y)}" width="{_num(size)}" height="{_num(size)}" '
            f'viewBox="{vb}"{fill_attr}>{inner}</svg>')


# ── shared decoration ──────────────────────────────────────────────────────
def petal_d(L: float) -> str:
    """One notched sakura petal pointing up from the origin."""
    n = _num
    return (f"M0 0C{n(-.55 * L)} {n(-.3 * L)} {n(-.62 * L)} {n(-.88 * L)} {n(-.2 * L)} {n(-L)}"
            f"L0 {n(-.84 * L)}L{n(.2 * L)} {n(-L)}C{n(.62 * L)} {n(-.88 * L)} {n(.55 * L)} {n(-.3 * L)} 0 0Z")


def blossom(cx: float, cy: float, r: float, t: dict, rot: float = 0) -> str:
    petals = "".join(f'<path d="{petal_d(r)}" transform="rotate({i * 72 + rot:.0f})"/>' for i in range(5))
    stamens = "".join(
        f'<circle cx="{_num(math.cos(math.radians(a)) * r * .38)}" cy="{_num(math.sin(math.radians(a)) * r * .38)}" '
        f'r="{_num(r * .065)}"/>' for a in range(int(rot) + 18, int(rot) + 378, 72))
    return (f'<g transform="translate({_num(cx)} {_num(cy)})">'
            f'<g fill="{t["petal"]}" stroke="{t["petal_edge"]}" stroke-width="{_num(max(.6, r * .05))}" '
            f'stroke-opacity=".75">{petals}</g>'
            f'<circle r="{_num(r * .2)}" fill="{PINK}"/><g fill="#B5718F">{stamens}</g></g>')


def sparkle(cx: float, cy: float, r: float, fill: str, cls: str = "", delay: float = 0) -> str:
    k = r * .16
    d = f"M0 {-r}C{k} {-k} {k} {-k} {r} 0C{k} {k} {k} {k} 0 {r}C{-k} {k} {-k} {k} {-r} 0C{-k} {-k} {-k} {-k} 0 {-r}Z"
    st = f' style="animation-delay:{delay:.1f}s"' if delay else ""
    c = f' class="{cls}"' if cls else ""
    return f'<g transform="translate({_num(cx)} {_num(cy)})"><path d="{d}" fill="{fill}"{c}{st}/></g>'


def falling_petals(t: dict, seed: int, n: int, x0: float, x1: float, y0: float, y1: float,
                   size: tuple[float, float]) -> str:
    """Rest positions double as the static composition."""
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        px, py, L, dur = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(*size), rnd.uniform(9, 15)
        out.append(f'<g transform="translate({px:.0f} {py:.0f}) rotate({rnd.uniform(0, 360):.0f})">'
                   f'<path d="{petal_d(L)}" fill="{t["petal"]}" stroke="{PINK}" stroke-width=".6" class="fall" '
                   f'style="animation-duration:{dur:.1f}s;animation-delay:-{rnd.uniform(0, dur):.1f}s"/></g>')
    return "".join(out)


MOTION_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(12px)}}
@keyframes fall{0%{opacity:0;transform:translate(0,-24px) rotate(0)}12%{opacity:.95}
88%{opacity:.95}100%{opacity:0;transform:translate(-90px,170px) rotate(300deg)}}
@keyframes twinkle{50%{opacity:.2}}
@keyframes breathe{50%{opacity:.55}}
@keyframes slide{0%,12%{transform:translateX(-64px)}50%,62%{transform:translateX(64px)}100%{transform:translateX(-64px)}}
.rise{animation:rise 1.1s cubic-bezier(.2,.7,.2,1) backwards}
.fall{animation:fall linear infinite;transform-box:fill-box;transform-origin:center}
.tw{animation:twinkle 3.6s ease-in-out infinite}
.breathe{animation:breathe 7s ease-in-out infinite}
.slide{animation:slide 9s cubic-bezier(.45,0,.25,1) infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def svg(w: float, h: float, body: str, label: str, animated: bool = False) -> str:
    css = f"<style>{MOTION_CSS}</style>" if animated else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(w)}" height="{_num(h)}" '
            f'viewBox="0 0 {_num(w)} {_num(h)}" fill="none" role="img" aria-label="{escape(label)}">'
            f"<title>{escape(label)}</title>{css}{body}</svg>\n")


def card_bg(w: float, h: float, t: dict, rx: float = 22, uid: str = "c") -> str:
    return (f'<defs><linearGradient id="{uid}g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{t["card"]}"/><stop offset="1" stop-color="{t["card2"]}"/></linearGradient></defs>'
            f'<rect x=".5" y=".5" width="{_num(w - 1)}" height="{_num(h - 1)}" rx="{rx}" fill="url(#{uid}g)" stroke="{t["line"]}"/>')


def seigaiha(t: dict, uid: str, x: float, y: float, w: float, h: float, opacity: float) -> str:
    """Japanese wave pattern band, faded out with a mask."""
    rings = "".join(f'<circle r="{r}" fill="{t["bg1"]}" stroke="{t["wave"]}" stroke-width=".8"/>' for r in (19, 14, 9, 4))
    tile_ = "".join(f'<g transform="translate({cx} {cy})">{rings}</g>'
                    for cx, cy in ((0, 0), (40, 0), (20, 10), (0, 20), (40, 20)))
    return (f'<defs><pattern id="{uid}p" width="40" height="20" patternUnits="userSpaceOnUse">'
            f'<rect width="40" height="20" fill="{t["bg1"]}"/>{tile_}</pattern>'
            f'<radialGradient id="{uid}r" cx=".75" cy="1" r=".9"><stop offset="0" stop-color="#fff"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="{uid}m"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{uid}r)"/></mask></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{uid}p)" opacity="{opacity}" mask="url(#{uid}m)"/>')


# ── hero ───────────────────────────────────────────────────────────────────
def hero(t: dict, animated: bool) -> str:
    H = 330
    b = [
        '<defs>'
        f'<linearGradient id="hbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["bg1"]}"/>'
        f'<stop offset="1" stop-color="{t["bg0"]}"/></linearGradient>'
        f'<radialGradient id="moon" cx=".38" cy=".35" r=".75"><stop offset="0" stop-color="{t["moon0"]}"/>'
        f'<stop offset="1" stop-color="{t["moon1"]}"/></radialGradient>'
        f'<radialGradient id="glow"><stop offset="0" stop-color="{t["glow"]}" stop-opacity=".42"/>'
        f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="hc"><rect width="{W}" height="{H}" rx="26"/></clipPath></defs>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="26" fill="url(#hbg)" stroke="{t["line"]}"/>'
        '<g clip-path="url(#hc)">'
    ]
    b.append(seigaiha(t, "sw", 430, 210, 430, 120, .32 if t["name"] == "dark" else .5))
    mx, my, mr = 690, 150, 84
    b.append(f'<circle cx="{mx}" cy="{my}" r="{mr * 1.9}" fill="url(#glow)" class="breathe"/>'
             f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="url(#moon)"/>')
    for cx, cy, r in ((-30, 22, 13), (26, -28, 8), (34, 30, 6), (-8, -44, 5)):
        b.append(f'<circle cx="{mx + cx}" cy="{my + cy}" r="{r}" fill="{PINK}" opacity=".16"/>')
    b.append(
        f'<g stroke="{t["branch"]}" stroke-linecap="round" fill="none">'
        '<path d="M884 6C836 22 800 44 754 60C712 74 676 98 636 106C604 112 580 126 562 142" stroke-width="6.5"/>'
        '<path d="M754 60C744 46 734 36 718 28" stroke-width="3.2"/>'
        '<path d="M704 80C702 94 696 106 686 118" stroke-width="3"/>'
        '<path d="M636 106C628 96 620 88 606 80" stroke-width="2.6"/>'
        '<path d="M810 40C816 56 818 72 812 90" stroke-width="3"/>'
        '<path d="M562 142C552 150 546 160 540 172" stroke-width="2"/></g>'
    )
    for cx, cy, r, rot in ((718, 28, 15, 10), (686, 120, 13, 40), (606, 80, 13, 20), (812, 92, 16, 0),
                           (562, 142, 11, 30), (760, 56, 11, 50), (846, 26, 13, 15)):
        b.append(blossom(cx, cy, r, t, rot))
    for cx, cy in ((660, 100), (540, 172), (780, 46)):
        b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="4" ry="6" fill="{PINK}" transform="rotate(-30 {cx} {cy})"/>')
    b.append(falling_petals(t, 7, 11, 470, 850, 150, 300, (6.5, 10)))
    for cx, cy, r, d in ((600, 44, 5, 0), (792, 222, 4, 1.2), (512, 120, 3.5, 2.1), (836, 168, 3, .6), (470, 58, 4, 1.7)):
        b.append(sparkle(cx, cy, r, t["accent"] if r > 4 else t["muted"], "tw", d))
    b.append("</g>")
    b.append(MINCHO.vertical("ソーニャ", 19, 826, 150, t["muted"]))
    b.append(f'<rect x="812" y="246" width="28" height="28" rx="5" fill="{t["seal"]}" transform="rotate(-4 826 260)"/>')
    b.append(MINCHO.text("創", 19, 826, 267, t["seal_text"], anchor="middle"))
    b.append(ITALIC.text(tr("hello"), 22, 58, 98, t["muted"], attrs=' class="rise"'))
    for i, d in enumerate(DISPLAY.glyphs("sonya", 118, 52, 196, tracking=.01)):
        b.append(f'<path d="{d}" fill="{t["text"]}" class="rise" style="animation-delay:{.15 + i * .09:.2f}s"/>')
    dot_x = 52 + DISPLAY.width("sonya", 118, .01) + 4
    b.append(DISPLAY.text(".", 118, dot_x, 196, t["accent"], attrs=' class="rise" style="animation-delay:.7s"'))
    b.append(SANS.text(tr("sub"), 16.5, 58, 238, t["muted"], tracking=.02, max_w=410,
                       attrs=' class="rise" style="animation-delay:.9s"'))
    b.append(f'<path d="M58 276h34" stroke="{t["accent"]}" stroke-width="1.5" stroke-linecap="round"/>')
    b.append(SANS.text("コードで、ものをつくる", 12, 104, 280, t["soft"], tracking=.28))
    return svg(W, H, "".join(b), f"sonya. — {tr('sub')}", animated)


# ── section headings ───────────────────────────────────────────────────────
def heading(key: str, t: dict) -> str:
    title, jp = tr("headings")[key], HEADING_JP[key]
    jx = 40 + ITALIC.width(title, 34) + 18
    lx = jx + SANS.width(jp, 12, .25) + 18
    b = [blossom(15, 34, 10, t, 18),
         ITALIC.text(title, 34, 38, 44, t["text"]),
         SANS.text(jp, 12, jx, 42, t["soft"], tracking=.25),
         f'<defs><linearGradient id="hl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["accent"]}" stop-opacity=".55"/>'
         f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></linearGradient></defs>'
         f'<rect x="{_num(lx)}" y="37.5" width="{_num(max(40, 640 - lx))}" height="1" fill="url(#hl)"/>']
    return svg(640, 60, "".join(b), title)


def group_label(title: str, t: dict) -> str:
    w = ITALIC.width(title, 22) + 24
    return svg(w, 34, sparkle(6, 19, 5, t["accent"]) + ITALIC.text(title, 22, 18, 26, t["muted"]), title)


# ── stack tiles (single theme: charcoal tiles read well on both) ───────────
def tile(key: str) -> str:
    body = (f'<rect x=".75" y=".75" width="94.5" height="94.5" rx="24" fill="{CHARCOAL}" stroke="#4A4350" stroke-width="1.5"/>'
            + logo(key, 22, 22, 52))
    return svg(96, 96, body, LOGOS[key][0])


def spoken(name: str, jp: str, level: str, t: dict) -> str:
    """Spoken-language pill: the name in its own script and an optional level badge."""
    font, size = (SANS_M, 17) if any(ord(ch) > 0x3000 for ch in name) else (ITALIC, 21)
    nw = font.width(name, size, .04)
    lw = SANS_M.width(level, 12, .06) + 26 if level else 0
    w, h = 22 + nw + (14 + lw + 8 if level else 22), 46
    b = [f'<rect x=".5" y=".5" width="{_num(w - 1)}" height="{h - 1}" rx="23" fill="{t["card"]}" stroke="{t["line"]}"/>',
         font.text(name, size, 22, 30, t["text"], tracking=.04)]
    if level:
        bx = w - lw - 8
        b.append(f'<rect x="{_num(bx)}" y="9" width="{_num(lw)}" height="28" rx="14" fill="{PINK}" fill-opacity=".18" '
                 f'stroke="{t["accent"]}" stroke-opacity=".55"/>')
        b.append(SANS_M.text(level, 12, bx + lw / 2, 27.5, t["accent"], anchor="middle", tracking=.06))
    return svg(w, h, "".join(b), f"{name} {level}".strip())


def badge(text: str, icon: str | None, t: dict) -> str:
    """Credential badge. Logo only when a real one exists, otherwise a sparkle."""
    tw = SANS_M.width(text, 13, .05)
    w, h = tw + 66, 40
    mark = (logo("", 18, 11, 18, t["text"], file=icon) if icon else sparkle(27, 20, 7, t["accent"]))
    b = [f'<rect x=".75" y=".75" width="{_num(w - 1.5)}" height="{h - 1.5}" rx="20" fill="{PINK}" fill-opacity=".1" '
         f'stroke="{t["accent"]}" stroke-opacity=".6" stroke-width="1.5"/>', mark,
         SANS_M.text(text, 13, 46, 25, t["text"], tracking=.05)]
    return svg(w, h, "".join(b), text)


# ── project cards ──────────────────────────────────────────────────────────
def mini_logos(keys: list[str], x: float, y: float, t: dict, size: float = 34) -> tuple[str, float]:
    out = []
    for k in keys:
        pad = size * .2
        out.append(f'<rect x="{_num(x)}" y="{_num(y)}" width="{size}" height="{size}" rx="{_num(size * .27)}" '
                   f'fill="{CHARCOAL}" stroke="{t["line"]}"/>' + logo(k, x + pad, y + pad, size - 2 * pad))
        x += size + 8
    return "".join(out), x


def featured(t: dict, animated: bool) -> str:
    H = 228
    fx_max = 540
    b = [card_bg(W, H, t, uid="f")]
    b.append(SANS_M.text(tr("featured"), 11.5, 34, 44, t["accent"], tracking=.18))
    b.append(DISPLAY.text("SONYA", 50, 32, 98, t["text"], tracking=.04))
    for i, line in enumerate(tr("featured_desc")):
        b.append(SANS.text(line, 15, 34, 130 + i * 22, t["muted"], max_w=496))
    logos, lx = mini_logos(["python", "fastapi", "postgresql", "docker", "mediapipe", "ffmpeg"], 34, 172, t)
    b.append(logos)
    b.append(SANS_M.text(tr("private_repo"), 12, lx + 8, 194, t["accent"], tracking=.06, max_w=fx_max - lx - 16))
    # a 16:9 frame with a 9:16 window gliding across it
    fx, fy, fw, fh = 548, 42, 268, 151
    cw = fh * 9 / 16
    b.append(f'<defs><clipPath id="fr"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="12"/></clipPath>'
             f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["card2"]}"/>'
             f'<stop offset="1" stop-color="{t["bg1"]}"/></linearGradient></defs>'
             f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="12" fill="url(#sky)" stroke="{t["line"]}"/>'
             '<g clip-path="url(#fr)">'
             f'<circle cx="{fx + 196}" cy="{fy + 50}" r="24" fill="{t["moon1"]}" opacity=".55"/>'
             f'<path d="M{fx} {fy + 118}C{fx + 60} {fy + 96} {fx + 110} {fy + 128} {fx + 170} {fy + 108}'
             f'S{fx + 240} {fy + 98} {fx + fw} {fy + 112}V{fy + fh}H{fx}Z" fill="{t["line"]}" opacity=".7"/>'
             + blossom(fx + 70, fy + 52, 11, t, 12) + blossom(fx + 92, fy + 76, 8, t, 40) + "</g>"
             f'<g class="slide"><rect x="{_num(fx + fw / 2 - cw / 2)}" y="{fy - 6}" width="{_num(cw)}" height="{fh + 12}" '
             f'rx="10" stroke="{t["accent"]}" stroke-width="2" fill="{PINK}" fill-opacity=".08"/>'
             + SANS.text("9:16", 10.5, fx + fw / 2 - cw / 2 + 10, fy + fh - 2, t["accent"]) + "</g>")
    return svg(W, H, "".join(b), "SONYA — " + " ".join(tr("featured_desc")), animated)


def card(key: str, t: dict) -> str:
    title, sub, desc, meta = tr("cards")[key]
    w, h = 400, 234
    b = [card_bg(w, h, t, uid="k"), blossom(366, 36, 10, t, 25), sparkle(342, 22, 3.5, t["muted"]),
         DISPLAY.text(title, 31, 28, 60, t["text"], tracking=.01, max_w=300),
         SANS_M.text(sub, 11, 29, 84, t["accent"], tracking=.1, max_w=344)]
    for i, line in enumerate(desc):
        b.append(SANS.text(line, 13.5, 28, 114 + i * 21, t["muted"], max_w=344))
    b.append(mini_logos(CARD_STACKS[key], 28, 152, t, 32)[0])
    b.append(f'<path d="M28 206h18" stroke="{t["accent"]}" stroke-linecap="round"/>')
    b.append(SANS_M.text(meta, 12, 54, 210, t["accent"] if "→" in meta else t["soft"], tracking=.06))
    return svg(w, h, "".join(b), f"{title} — {sub}. {' '.join(desc)}")


# ── currently learning ─────────────────────────────────────────────────────
def learning(t: dict) -> str:
    b = [card_bg(W, 128, t, uid="l")]
    col = (W - 56) / 3
    items = tr("learning")
    for i, (k, (title, sub)) in enumerate(zip(LEARNING_LOGOS, items)):
        x = 28 + i * col
        b.append(f'<rect x="{_num(x)}" y="34" width="60" height="60" rx="16" fill="{CHARCOAL}" stroke="{t["line"]}"/>')
        b.append(logo(k, x + 14, 48, 32))
        b.append(ITALIC.text(title, 22, x + 76, 60, t["text"], max_w=col - 88))
        b.append(SANS.text(sub, 12.5, x + 77, 84, t["muted"], max_w=col - 88))
    return svg(W, 128, "".join(b), ", ".join(x[0] for x in items))


# ── hardware & homelab ─────────────────────────────────────────────────────
def hardware(t: dict) -> str:
    items = tr("hardware")
    col = (W - 56) / 3
    h = 34 + 76 + 52 + 34
    b = [card_bg(W, h, t, uid="hw")]
    for i, (key, title, sub) in enumerate(items):
        r, c = divmod(i, 3)
        x, y = 28 + c * col, 34 + r * 76
        b.append(f'<rect x="{_num(x)}" y="{y}" width="52" height="52" rx="14" fill="{CHARCOAL}" stroke="{t["line"]}"/>')
        b.append(logo(key, x + 13, y + 13, 26) if key else sparkle(x + 26, y + 26, 9, PINK))
        b.append(ITALIC.text(title, 20, x + 66, y + 24, t["text"], max_w=col - 78))
        b.append(SANS.text(sub, 12, x + 67, y + 44, t["muted"], max_w=col - 78))
    return svg(W, h, "".join(b), "hardware & homelab: " + ", ".join(x[1] for x in items))


# ── find me ────────────────────────────────────────────────────────────────
PILLS = [
    ("telegram", "@removed", "si-telegram.svg"),
    ("github", "github", "si-github.svg"),
    ("codewars", "codewars", "si-codewars.svg"),
    ("email", "removed", "si-gmail.svg"),
]


def pill(text: str, icon: str, t: dict) -> str:
    w, h = SANS_M.width(text, 14, .04) + 74, 48
    b = [f'<rect x=".5" y=".5" width="{_num(w - 1)}" height="{h - 1}" rx="24" fill="{t["card"]}" stroke="{t["line"]}"/>',
         logo("", 20, 14, 20, t["accent"], file=icon), SANS_M.text(text, 14, 52, 29, t["text"], tracking=.04)]
    return svg(w, h, "".join(b), text)


def footer(t: dict, animated: bool) -> str:
    b = [f'<g stroke="{t["branch"]}" stroke-linecap="round" fill="none">'
         '<path d="M300 58C340 50 372 54 404 44" stroke-width="2.4"/><path d="M372 52C378 42 386 36 396 32" stroke-width="1.6"/></g>',
         blossom(404, 44, 9, t, 10), blossom(396, 30, 7, t, 40), blossom(336, 52, 6, t, 0),
         ITALIC.text(tr("thanks"), 20, 430, 52, t["muted"]),
         SANS.text("またね", 12, 432, 72, t["soft"], tracking=.3),
         falling_petals(t, 3, 5, 230, 400, 10, 86, (5, 7))]
    return svg(W, 96, "".join(b), f"{tr('thanks')} — またね", animated)


# ── live data ──────────────────────────────────────────────────────────────
def token() -> str | None:
    for k in ("GH_STATS_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(k):
            return os.environ[k]
    return None


def gh(url: str, tok: str, payload: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None)
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch(tok: str) -> dict:
    q = """query($login:String!){ user(login:$login){
      contributionsCollection{ contributionCalendar{ totalContributions
        weeks{ contributionDays{ date contributionCount weekday } } } }
      repositories(ownerAffiliations:OWNER, first:100, isFork:false){ totalCount
        nodes{ name isPrivate isEmpty languages(first:20){ edges{ size node{ name } } } } } } }"""
    data = gh("https://api.github.com/graphql", tok, {"query": q, "variables": {"login": LOGIN}})
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]


def stats(user: dict, t: dict) -> str:
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"])
    repos = [r for r in user["repositories"]["nodes"] if not r["isEmpty"] and r["name"] not in EXCLUDED_REPOS]
    langs: dict[str, int] = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    rest = total - sum(v for _, v in top)

    w, h = 400, 214
    b = [card_bg(w, h, t, uid="s"), SANS_M.text(tr("gh_label"), 11.5, 28, 40, t["accent"], tracking=.14)]
    for i, (val, lab) in enumerate(zip((cal["totalContributions"], active, len(repos)), tr("stat_labels"))):
        x = 28 + i * 118
        b.append(DISPLAY.text(str(val), 40, x, 92, t["text"]))
        b.append(SANS.text(lab, 12, x + 1, 114, t["muted"], max_w=108))
    by, bw = 140, w - 56
    b.append(f'<clipPath id="sb"><rect x="28" y="{by}" width="{bw}" height="8" rx="4"/></clipPath><g clip-path="url(#sb)">')
    x = 28.0
    for i, (_, size) in enumerate(top + ([("other", rest)] if rest else [])):
        seg = bw * size / total
        b.append(f'<rect x="{x:.1f}" y="{by}" width="{seg + .6:.1f}" height="8" fill="{LANG_SHADES[i]}"/>')
        x += seg
    b.append("</g>")
    lx = 28.0
    for i, (name, size) in enumerate(top):
        lab = f"{name.lower()} {size / total * 100:.0f}%"
        b.append(f'<circle cx="{lx + 4:.1f}" cy="{by + 38}" r="4" fill="{LANG_SHADES[i]}"/>')
        b.append(SANS.text(lab, 11.5, lx + 13, by + 42, t["muted"]))
        lx += SANS.width(lab, 11.5) + 28
    return svg(w, h, "".join(b), f"GitHub: {cal['totalContributions']} / {active} / {len(repos)}")


def activity(user: dict, t: dict) -> str:
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    cell, gap = 11.6, 3
    gx, gy = 62, 66
    h = gy + 7 * (cell + gap) + 52
    b = [card_bg(W, h, t, uid="a"), SANS_M.text(tr("contrib_label"), 11.5, 28, 38, t["accent"], tracking=.14)]
    counts = sorted(d["contributionCount"] for w in weeks for d in w["contributionDays"] if d["contributionCount"])
    q = lambda p: counts[min(len(counts) - 1, int(len(counts) * p))] if counts else 1  # noqa: E731
    th = [q(.25), q(.5), q(.75)]
    scale = HEAT[t["name"]]
    for i, lab in zip((1, 3, 5), tr("weekdays")):
        b.append(SANS.text(lab, 10.5, gx - 10, gy + i * (cell + gap) + 10, t["soft"], anchor="end"))
    last = None
    for wi, w in enumerate(weeks):
        x = gx + wi * (cell + gap)
        first = w["contributionDays"][0]["date"]
        m = first[5:7]
        if m != last and wi < len(weeks) - 1:
            # skip the leading partial month when the next one starts within 3 weeks
            nxt = next((j for j in range(wi + 1, len(weeks)) if weeks[j]["contributionDays"][0]["date"][5:7] != m), len(weeks))
            if last is not None or nxt - wi >= 3:
                b.append(SANS.text(tr("months")[int(m) - 1], 10.5, x, gy - 10, t["soft"]))
            last = m
        for d in w["contributionDays"]:
            c = d["contributionCount"]
            lv = 0 if c == 0 else 1 + sum(c > v for v in th)
            b.append(f'<rect x="{x:.1f}" y="{gy + d["weekday"] * (cell + gap):.1f}" width="{cell}" height="{cell}" rx="3.5" '
                     f'fill="{scale[lv]}"><title>{d["date"]}: {c}</title></rect>')
    ly = gy + 7 * (cell + gap) + 26
    total = tr("contrib_total").format(n=cal["totalContributions"])
    b.append(SANS.text(total, 12, gx, ly + 10, t["muted"]))
    lx = W - 28 - 5 * (cell + gap) - SANS.width(tr("more"), 10.5) - 8
    b.append(SANS.text(tr("less"), 10.5, lx - 8, ly + 10, t["soft"], anchor="end"))
    for i, c in enumerate(scale):
        b.append(f'<rect x="{lx + i * (cell + gap):.1f}" y="{ly}" width="{cell}" height="{cell}" rx="3.5" fill="{c}"/>')
    b.append(SANS.text(tr("more"), 10.5, lx + 5 * (cell + gap) + 4, ly + 10, t["soft"]))
    return svg(W, h, "".join(b), total)


def fetch_codewars() -> dict | None:
    try:
        with urllib.request.urlopen(f"https://www.codewars.com/api/v1/users/{CODEWARS_USER}", timeout=30) as r:
            return json.load(r)
    except Exception as e:  # keep the previous card on network errors
        print(f"  codewars fetch failed: {e}", file=sys.stderr)
        return None


def codewars(u: dict, t: dict) -> str:
    w, h = 400, 214
    overall = u["ranks"]["overall"]
    langs = sorted(u["ranks"]["languages"].items(), key=lambda kv: -kv[1]["score"])
    names = {"cpp": "c++"}
    b = [card_bg(w, h, t, uid="w"), SANS_M.text(f"codewars · {CODEWARS_USER}", 11.5, 28, 40, t["accent"], tracking=.14),
         f'<rect x="28" y="60" width="62" height="62" rx="12" fill="{t["seal"]}" transform="rotate(-4 59 91)"/>',
         DISPLAY.text(overall["name"].split()[0], 34, 59, 95, t["seal_text"], anchor="middle"),
         SANS_M.text("kyu", 10.5, 59, 111, t["seal_text"], anchor="middle", tracking=.1),
         DISPLAY.text(overall["name"], 30, 110, 88, t["text"]),
         SANS.text(" · ".join(names.get(k, k) for k, _ in langs[:3]), 12.5, 111, 110, t["muted"])]
    for i, (val, lab) in enumerate(((u["codeChallenges"]["totalCompleted"], tr("kata")), (u["honor"], tr("honor")))):
        x = 28 + i * 130
        b.append(DISPLAY.text(str(val), 36, x, 172, t["text"]))
        b.append(SANS.text(lab, 12, x + 1, 192, t["muted"]))
    return svg(w, h, "".join(b), f"Codewars {CODEWARS_USER}: {overall['name']}, "
                                 f"{u['codeChallenges']['totalCompleted']} kata, honor {u['honor']}")


# ── main ───────────────────────────────────────────────────────────────────
def write(rel: str, content: str) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def prefix(loc: str) -> str:
    return "" if loc == "en" else f"{loc}/"


def main() -> int:
    global LOC
    load_fonts()
    for LOC in TX:
        pre = prefix(LOC)
        for name, t in THEMES.items():
            for animated, folder in ((True, f"{pre}{name}"), (False, f"static/{pre}{name}")):
                write(f"{folder}/hero.svg", hero(t, animated))
                write(f"{folder}/featured-sonya.svg", featured(t, animated))
                write(f"{folder}/footer.svg", footer(t, animated))
            d = f"{pre}{name}"
            for key in HEADING_JP:
                write(f"{d}/h-{key}.svg", heading(key, t))
            for key, en, ru, *_ in STACK:
                write(f"{d}/g-{key}.svg", group_label(en if LOC == "en" else ru, t))
            write(f"{d}/g-spoken.svg", group_label(tr("spoken_label"), t))
            write(f"{d}/g-background.svg", group_label(tr("background"), t))
            for i, (lang, jp, level) in enumerate(tr("spoken")):
                write(f"{d}/lang-{i}.svg", spoken(lang, jp, level, t))
            for key, text in tr("badges").items():
                write(f"{d}/badge-{key}.svg", badge(text, BADGE_ICONS.get(key), t))
            for key in CARD_STACKS:
                write(f"{d}/card-{key}.svg", card(key, t))
            write(f"{d}/learning.svg", learning(t))
            write(f"{d}/hardware.svg", hardware(t))
            if LOC == "en":  # contact pills carry no translatable text
                for key, text, icon in PILLS:
                    write(f"{name}/pill-{key}.svg", pill(text, icon, t))
    for _, _, _, keys, *_ in STACK:
        for k in keys:
            write(f"stack/{k}.svg", tile(k))
    print("  static assets written")

    cw = fetch_codewars()
    tok = token()
    user = fetch(tok) if tok else None
    if not tok:
        print("  no token — keeping existing GitHub stats cards", file=sys.stderr)
    for LOC in TX:
        for name, t in THEMES.items():
            d = f"{prefix(LOC)}{name}"
            if cw:
                write(f"{d}/codewars.svg", codewars(cw, t))
            if user:
                write(f"{d}/stats.svg", stats(user, t))
                write(f"{d}/activity.svg", activity(user, t))
    print("  live cards written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
