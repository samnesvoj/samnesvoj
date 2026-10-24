#!/usr/bin/env python3
"""Generate every image used by the profile README (English and Russian).

Design system: Japanese editorial, soft dark minimalism, muted pink and graphite.
Type: Instrument Serif (display), Manrope (labels), IBM Plex Mono (metadata),
Noto Serif JP (Japanese) — all OFL, subset in scripts/fonts and converted to
outlines, so nothing depends on fonts installed on the viewer's machine.
Logos come from scripts/icons (Devicon — MIT, Simple Icons — CC0).
The floral artwork is generated here (pointillism, written from scratch).

Output layout:
    assets/{light,dark}/*.svg        English, per theme (README switches with <picture>)
    assets/ru/{light,dark}/*.svg     Russian
    assets/static/[ru/]{theme}/      motion-free copies of animated assets
    assets/stack/*.svg               logo tiles (theme-independent)
    assets/variants/                 the two explored directions (A and B)

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
JP_TEXT = "ソーニャ創作品技術記録連絡先紹介機材経歴依頼日本語またねコードで、ものをつくる"

W = 860

# ── palette ────────────────────────────────────────────────────────────────
GRAPHITE = "#1B1A20"
PINK = "#D8A7BC"
ROSE = "#EAD0DD"
GREY = "#ADA5AC"
PEARL = "#F5F1F4"

THEMES = {
    "dark": dict(name="dark", panel=GRAPHITE, text=PEARL, muted=GREY, faint="#6E6670", accent=PINK,
                 rule="#3A353F", tile=GRAPHITE, dots=[PINK, "#E2BCCD", "#A9708A", GREY, ROSE],
                 heat=["#2A2730", "#5A4652", "#86627A", "#B385A0", PINK]),
    "light": dict(name="light", panel=PEARL, text=GRAPHITE, muted="#6F676E", faint="#A79FA6", accent="#A9708A",
                  rule="#E3D8DE", tile=GRAPHITE, dots=["#C08AA2", "#D8A7BC", "#A9708A", "#9C949B", "#E2BFCE"],
                  heat=["#EEE7EB", "#EDD1DD", "#DFB2C5", "#C98FA9", "#A9708A"]),
}

# ── copy ───────────────────────────────────────────────────────────────────
TX = {
    "en": dict(
        role="Software engineer",
        role_line="Backend · AI/ML · Full stack",
        cover_meta=("samnesvoj", "portfolio", "2026"),
        cover_index="backend — ai/ml — automation — web",
        cover_fig="fig. 01 — lotus, {n:,} points",
        about=[
            "I build websites and web applications with React, JavaScript, HTML and CSS — not only interfaces, "
            "but also the server side, databases, APIs and deployment.",
            "I develop and integrate AI chats into websites, connect language models and set up integrations "
            "with external services. I also build Telegram apps, automated pipelines and tools for clients' needs.",
            "My main project is SONYA, a platform for automated video processing with computer vision, speech "
            "recognition and LLMs. Alongside it, I'm studying modern C++, systems programming and performance "
            "optimization.",
        ],
        facts=[("study", "Applied Informatics", "KubSAU · 1st year"),
               ("course", "C++ Middle", "Yandex Practicum"),
               ("work", "Self-employed", "open for orders"),
               ("cloud", "Timeweb Cloud partner", "Yandex Cloud")],
        headings={"about": "About", "work": "Selected work", "stack": "Stack", "services": "Commissions",
                  "studio": "Studio", "background": "Background", "activity": "Activity", "contact": "Contact"},
        projects={
            "sonya": ("SONYA", "Long videos in, short clips out — computer vision, speech recognition and LLMs on GPU workers.",
                      "python · fastapi · postgresql · yolo11 · ffmpeg", "sonya.group ↗"),
            "pylens": ("PyLens", "An interactive guide to Python built-ins: examples, visualizations, a quiz.",
                       "next.js · react · typescript", "live demo ↗"),
            "group-bot": ("SONYA GROUP Bot", "Telegram bot for the platform: sign-up, consent, Mini App access.",
                          "python · aiogram 3 · sqlite · pytest", "private"),
            "automation": ("Content Automation", "Custom pipelines for Zen and TikTok: data, LLMs, approval in Telegram.",
                           "n8n · python · supabase · openrouter", "private"),
            "aminelli": ("Aminelli", "Website and lookbook for a flower brand, with a 1C integration layer.",
                         "react · vite · typescript", "lookbook ↗"),
            "web": ("Custom web projects", "Websites, landing pages and Taplink pages built to a brand's design.",
                    "html · css · javascript", "example ↗"),
            "gforms": ("Google Forms & Apps Script", "Forms generated in code, with response logic, Sheets and notifications.",
                       "apps script · google apis", "on request"),
        },
        sonya_label="main project",
        services=[("Backend & APIs", "FastAPI, PostgreSQL, integrations, deployment"),
                  ("AI integrations", "AI chats on websites, LLMs, computer vision, speech"),
                  ("Telegram apps", "bots and Mini Apps"),
                  ("Custom pipelines", "n8n, Python, JavaScript — data, content, publishing"),
                  ("Web development", "sites, landing pages, Taplink pages"),
                  ("Google Forms in code", "Apps Script, Sheets, notifications"),
                  ("Payments", "Robokassa, YooKassa, Samozanyatye.rf")],
        services_note="self-employed · contracts and one-off work",
        studio=[("Mac mini M4", "16 GB · 256 GB"), ("MacBook M5", "macOS"), ("Windows PC", "windows"),
                ("Linux laptop", "linux"), ("Linux VMs", "virtual machines"), ("Home NAS", "homelab")],
        background=[
            ("education", [("Applied Informatics", "Kuban State Agrarian University · 1st year"),
                           ("C++ Middle", "Yandex Practicum · in progress"),
                           ("JavaScript, CSS, ML", "Academy of Design and Programming NADIP")]),
            ("credentials", [("Apple Developer", "certificate"),
                             ("Verified IT skills", "Gosuslugi"),
                             ("Timeweb Cloud", "partner")]),
            ("languages", [("Русский", ""), ("English", "B1"), ("日本語", "N5")]),
        ],
        gh_label="github · last 12 months",
        stat_labels=["contributions", "active days", "projects"],
        months=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
        contrib_total="{n} contributions in the last year",
        kata="kata solved", honor="honor",
        thanks="thanks for reading",
        colophon="set in Instrument Serif, Manrope, IBM Plex Mono and Noto Serif JP · drawn as SVG",
    ),
    "ru": dict(
        role="Software engineer",
        role_line="Backend · AI/ML · Full stack",
        cover_meta=("samnesvoj", "portfolio", "2026"),
        cover_index="backend — ai/ml — automation — web",
        cover_fig="рис. 01 — лотос, {n:,} точек",
        about=[
            "Делаю сайты и веб-приложения на React, JavaScript, HTML и CSS. Работаю не только с интерфейсами, "
            "но и с серверной частью, базами данных, API и развёртыванием проектов.",
            "Разрабатываю и интегрирую AI-чаты на сайты, подключаю языковые модели и настраиваю взаимодействие "
            "с внешними сервисами. Также создаю Telegram-приложения, автоматизированные пайплайны и инструменты "
            "под задачи заказчиков.",
            "Мой основной проект SONYA, платформа для автоматической обработки видео с использованием "
            "компьютерного зрения, распознавания речи и LLM. Параллельно изучаю современный C++, системное "
            "программирование и оптимизацию производительности.",
        ],
        facts=[("учёба", "Прикладная информатика", "КубГАУ · 1 курс"),
               ("курс", "C++ Middle", "Яндекс Практикум"),
               ("работа", "Самозанятая", "принимаю заказы"),
               ("облака", "Партнёр Timeweb Cloud", "Yandex Cloud")],
        headings={"about": "About", "work": "Selected work", "stack": "Stack", "services": "Commissions",
                  "studio": "Studio", "background": "Background", "activity": "Activity", "contact": "Contact"},
        projects={
            "sonya": ("SONYA", "Длинные видео на входе, короткие ролики на выходе — CV, речь и LLM на GPU-воркерах.",
                      "python · fastapi · postgresql · yolo11 · ffmpeg", "sonya.group ↗"),
            "pylens": ("PyLens", "Интерактивный гид по встроенным функциям Python: примеры, визуализации, тесты.",
                       "next.js · react · typescript", "демо ↗"),
            "group-bot": ("SONYA GROUP Bot", "Telegram-бот платформы: регистрация, согласия, доступ к Mini App.",
                          "python · aiogram 3 · sqlite · pytest", "приватный"),
            "automation": ("Content Automation", "Пайплайны на заказ для Дзена и TikTok: данные, LLM, модерация в Telegram.",
                           "n8n · python · supabase · openrouter", "приватный"),
            "aminelli": ("Аминелли", "Сайт и лукбук цветочного бренда с интеграцией с 1С.",
                         "react · vite · typescript", "лукбук ↗"),
            "web": ("Custom web projects", "Сайты, лендинги и Taplink-страницы под фирменный стиль.",
                    "html · css · javascript", "пример ↗"),
            "gforms": ("Google Forms & Apps Script", "Формы, созданные кодом: логика ответов, Таблицы, уведомления.",
                       "apps script · google apis", "на заказ"),
        },
        sonya_label="основной проект",
        services=[("Backend и API", "FastAPI, PostgreSQL, интеграции, деплой"),
                  ("AI-интеграции", "AI-чаты на сайтах, LLM, компьютерное зрение, речь"),
                  ("Telegram-приложения", "боты и Mini Apps"),
                  ("Пайплайны на заказ", "n8n, Python, JavaScript — данные, контент, публикации"),
                  ("Веб-разработка", "сайты, лендинги, Taplink-страницы"),
                  ("Google Формы кодом", "Apps Script, Таблицы, уведомления"),
                  ("Платежи", "Robokassa, YooKassa, Самозанятые.рф")],
        services_note="самозанятая · проекты и разовые задачи",
        studio=[("Mac mini M4", "16 ГБ · 256 ГБ"), ("MacBook M5", "macOS"), ("ПК на Windows", "windows"),
                ("Ноутбук на Linux", "linux"), ("Linux VM", "виртуальные машины"), ("Домашний NAS", "homelab")],
        background=[
            ("образование", [("Прикладная информатика", "КубГАУ · 1 курс"),
                             ("C++ Middle", "Яндекс Практикум · в процессе"),
                             ("JavaScript, CSS, ML", "Академия дизайна и программирования НАДИП")]),
            ("подтверждения", [("Apple Developer", "сертификат"),
                               ("IT-компетенции", "подтверждены на Госуслугах"),
                               ("Timeweb Cloud", "партнёр")]),
            ("языки", [("Русский", ""), ("English", "B1"), ("日本語", "N5")]),
        ],
        gh_label="github · последние 12 месяцев",
        stat_labels=["контрибуции", "активные дни", "проекты"],
        months=["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
        contrib_total="контрибуций за последний год: {n}",
        kata="решённые ката", honor="honor",
        thanks="спасибо, что дочитали",
        colophon="набрано Instrument Serif, Manrope, IBM Plex Mono и Noto Serif JP · нарисовано в SVG",
    ),
}

HEADING_JP = {"about": "紹介", "work": "作品", "stack": "技術", "services": "依頼", "studio": "機材",
              "background": "経歴", "activity": "記録", "contact": "連絡先"}
HEADING_NO = {"about": "01", "work": "02", "stack": "03", "services": "04", "studio": "05",
              "background": "06", "activity": "07", "contact": "08"}

# (key, title, logos, extra tools without a logo)
STACK = [
    ("languages", "languages", ["python", "cpp", "swift", "javascript", "typescript", "html", "css", "bash"], "sql"),
    ("web", "frontend & backend", ["react", "nextjs", "nodejs", "fastapi", "vite", "tailwind", "framer", "threejs",
                                   "pydantic", "postgresql", "sqlite", "supabase"],
     "rest api · webhooks · apscheduler · payment integrations"),
    ("ai", "ai & computer vision", ["opencv", "numpy", "mediapipe", "ffmpeg", "openai", "gemini"],
     "yolo11 · faster-whisper · pyscenedetect · yt-dlp · openrouter"),
    ("automation", "automation", ["n8n", "claude", "appsscript", "gforms", "gsheets", "telegram"],
     "aiogram · telegraf · telegram mini apps · apify"),
    ("infra", "infrastructure", ["docker", "git", "actions", "linux", "nginx", "s3", "yandexcloud", "vercel", "pytest"],
     "timeweb cloud · vast.ai · systemd · ghcr"),
    ("platforms", "platforms", ["macos", "windows", "cuda", "amd"], ""),
]

PROJECT_ORDER = ["sonya", "pylens", "group-bot", "automation", "aminelli", "web", "gforms"]

LOC = "en"
_GLYPHS: dict[tuple[str, int], tuple[str | None, str]] = {}  # glyph outlines used by the current document
LAST_DOTS = 0  # dot count of the most recent flower, for the figure caption


def tr(key: str):
    return TX[LOC][key]


# ── typography: text → outlines ────────────────────────────────────────────
def _num(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Font:
    """A font converted to SVG outlines, with an optional fallback for missing characters."""

    def __init__(self, name: str, fallback: "Font | None" = None):
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont

        path = FONTS / name
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.cmap = self.tt.getBestCmap()
        self.upem = self.tt["head"].unitsPerEm
        self.hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self.fallback = fallback
        self.name = name

    def _for(self, text: str) -> "Font":
        if self.fallback and any(ord(c) not in self.cmap for c in text if not c.isspace()):
            return self.fallback._for(text)
        return self

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

    def ref(self, gid: int) -> str | None:
        """Id of this glyph's outline in the current document's <defs> (None for blank glyphs)."""
        key = (self.name, gid)
        if key not in _GLYPHS:
            from fontTools.pens.svgPathPen import SVGPathPen
            from fontTools.pens.transformPen import TransformPen

            pen = SVGPathPen(self.gs, ntos=lambda v: str(round(v)))
            self.gs[self.order[gid]].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
            d = pen.getCommands()
            _GLYPHS[key] = (f"g{len(_GLYPHS)}", d) if d else (None, "")
        return _GLYPHS[key][0]

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        f = self._for(text)
        _, pos = f._shape(text)
        return sum(p.x_advance for p in pos) * size / f.upem + tracking * size * (len(pos) - 1)

    def fit(self, text: str, size: float, max_w: float, tracking: float = 0) -> float:
        w = self.width(text, size, tracking)
        return size if w <= max_w else size * max_w / w

    def glyphs(self, text: str, size: float, x: float, y: float, anchor: str = "start",
               tracking: float = 0) -> list[str]:
        f = self._for(text)
        infos, pos = f._shape(text)
        s = size / f.upem
        x -= {"start": 0, "middle": .5, "end": 1}[anchor] * self.width(text, size, tracking)
        out = []
        for info, p in zip(infos, pos):
            d = f._glyph(info.codepoint, s, x + p.x_offset * s, y - p.y_offset * s)
            if d:
                out.append(d)
            x += p.x_advance * s + tracking * size
        return out

    def text(self, text: str, size: float, x: float, y: float, fill: str, anchor: str = "start",
             tracking: float = 0, attrs: str = "", max_w: float | None = None) -> str:
        """Each glyph is defined once per document and placed with <use>."""
        if not text:
            return ""
        if max_w:
            size = self.fit(text, size, max_w, tracking)
        f = self._for(text)
        infos, pos = f._shape(text)
        s = size / f.upem
        x -= {"start": 0, "middle": .5, "end": 1}[anchor] * self.width(text, size, tracking)
        uses = []
        for info, p in zip(infos, pos):
            gid = f.ref(info.codepoint)
            if gid:
                uses.append(f'<use href="#{gid}" transform="matrix({s:.5g} 0 0 {s:.5g} '
                            f'{_num(x + p.x_offset * s)} {_num(y - p.y_offset * s)})"/>')
            x += p.x_advance * s + tracking * size
        return f'<g fill="{fill}"{attrs}>{"".join(uses)}</g>'

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


SERIF = SERIF_I = SANS = SANS_M = MONO = MONO_M = JP = None  # loaded in main()


def load_fonts() -> None:
    global SERIF, SERIF_I, SANS, SANS_M, MONO, MONO_M, JP
    JP = Font("jp.ttf")
    SANS = Font("sans.ttf", JP)
    SANS_M = Font("sans-medium.ttf", JP)
    SERIF = Font("display.ttf", JP)  # Instrument Serif has no Cyrillic: Noto Serif JP covers it
    SERIF_I = Font("display-italic.ttf", JP)
    MONO = Font("mono.ttf", SANS)
    MONO_M = Font("mono-medium.ttf", SANS_M)


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
    "appsscript": ("Google Apps Script", "si-googleappsscript.svg", "#4285F4"),
    "gforms": ("Google Forms", "si-googleforms.svg", "#7248B9"),
    "gsheets": ("Google Sheets", "si-googlesheets.svg", "#34A853"),
    "macos": ("macOS", "si-apple.svg", PEARL),
    "windows": ("Windows", "dv-windows11-original.svg", None),
    "cuda": ("NVIDIA CUDA", "si-nvidia.svg", "#76B900"),
    "amd": ("AMD", "si-amd.svg", PEARL),
    "docker": ("Docker", "dv-docker-original.svg", None),
    "git": ("Git", "dv-git-original.svg", None),
    "actions": ("GitHub Actions", "dv-githubactions-original.svg", None),
    "linux": ("Linux", "si-linux.svg", PEARL),
    "nginx": ("Nginx", "dv-nginx-original.svg", None),
    "s3": ("S3 storage", "si-amazons3.svg", "#569A31"),
    "yandexcloud": ("Yandex Cloud", "si-yandexcloud.svg", "#5282FF"),
    "vercel": ("Vercel", "si-vercel.svg", PEARL),
    "pytest": ("pytest", "dv-pytest-original.svg", None),
    "cmake": ("CMake", "dv-cmake-original.svg", None),
}

DOCS = {
    "python": "https://docs.python.org/3/", "cpp": "https://en.cppreference.com/", "swift": "https://www.swift.org/documentation/",
    "javascript": "https://developer.mozilla.org/docs/Web/JavaScript", "typescript": "https://www.typescriptlang.org/docs/",
    "html": "https://developer.mozilla.org/docs/Web/HTML", "css": "https://developer.mozilla.org/docs/Web/CSS",
    "bash": "https://www.gnu.org/software/bash/manual/", "react": "https://react.dev/", "nextjs": "https://nextjs.org/docs",
    "nodejs": "https://nodejs.org/docs/latest/api/", "vite": "https://vite.dev/guide/", "tailwind": "https://tailwindcss.com/docs",
    "framer": "https://motion.dev/docs", "threejs": "https://threejs.org/docs/", "fastapi": "https://fastapi.tiangolo.com/",
    "pydantic": "https://docs.pydantic.dev/", "postgresql": "https://www.postgresql.org/docs/", "sqlite": "https://sqlite.org/docs.html",
    "supabase": "https://supabase.com/docs", "telegram": "https://core.telegram.org/bots/api",
    "opencv": "https://github.com/opencv/opencv", "numpy": "https://numpy.org/doc/", "mediapipe": "https://ai.google.dev/edge/mediapipe",
    "ffmpeg": "https://ffmpeg.org/documentation.html", "openai": "https://platform.openai.com/docs",
    "gemini": "https://ai.google.dev/gemini-api/docs", "n8n": "https://docs.n8n.io/", "claude": "https://docs.claude.com/en/docs/claude-code",
    "appsscript": "https://developers.google.com/apps-script", "gforms": "https://developers.google.com/forms",
    "gsheets": "https://developers.google.com/sheets", "macos": "https://developer.apple.com/macos/",
    "windows": "https://learn.microsoft.com/windows/", "cuda": "https://docs.nvidia.com/cuda/", "amd": "https://rocm.docs.amd.com/",
    "docker": "https://docs.docker.com/", "git": "https://git-scm.com/doc", "actions": "https://docs.github.com/actions",
    "linux": "https://www.kernel.org/doc/html/latest/", "nginx": "https://nginx.org/en/docs/",
    "s3": "https://docs.aws.amazon.com/s3/", "yandexcloud": "https://yandex.cloud/docs", "vercel": "https://vercel.com/docs",
    "pytest": "https://docs.pytest.org/", "cmake": "https://cmake.org/documentation/",
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


# ── motion ─────────────────────────────────────────────────────────────────
# Seen rarely (a profile visit), so a short entrance is allowed; everything else stays still.
# ease-out curve from the design-engineering guide; 40 ms stagger; no scale-from-zero.
MOTION_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(8px)}}
@keyframes fade{from{opacity:0}}
@keyframes turn{to{transform:rotate(360deg)}}
.rise{animation:rise .7s cubic-bezier(.23,1,.32,1) backwards}
.fade{animation:fade 1.2s cubic-bezier(.23,1,.32,1) backwards}
.turn{animation:turn 240s linear infinite;transform-box:fill-box;transform-origin:center}
@keyframes flutter{0%,70%,100%{transform:scaleX(1)}80%{transform:scaleX(.9)}90%{transform:scaleX(.97)}}
.flutter{animation:flutter 7s cubic-bezier(.77,0,.175,1) infinite;transform-box:fill-box;transform-origin:center}
@media (prefers-reduced-motion:reduce){.rise{animation-name:fade}.turn,.flutter{animation:none}}
"""


def delay(i: int, base: float = 0.0, step: float = 0.04) -> str:
    return f' style="animation-delay:{base + i * step:.2f}s"'


def svg(w: float, h: float, body: str, label: str, animated: bool = False) -> str:
    css = f"<style>{MOTION_CSS}</style>" if animated else ""
    defs = "".join(f'<path id="{i}" d="{d}"/>' for i, d in _GLYPHS.values() if i)
    _GLYPHS.clear()
    if defs:
        css += f"<defs>{defs}</defs>"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(w)}" height="{_num(h)}" '
            f'viewBox="0 0 {_num(w)} {_num(h)}" fill="none" role="img" aria-label="{escape(label)}">'
            f"<title>{escape(label)}</title>{css}{body}</svg>\n")


def rule(x1: float, y: float, x2: float, t: dict, opacity: float = 1) -> str:
    return f'<path d="M{_num(x1)} {_num(y)}H{_num(x2)}" stroke="{t["rule"]}" stroke-opacity="{opacity}"/>'


# ── pointillist flora (original code; inspired by the idea of a dotted lotus) ─
def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _petal(rnd, ox, oy, angle, length, width, n, colors, dots, edge_bias=0.55):
    """Dots inside a pointed petal (vesica) rotated by `angle` (radians from vertical)."""
    ca, sa = math.cos(angle), math.sin(angle)
    for _ in range(n):
        u = rnd.random() ** 0.8                     # along the petal, 0 = base, 1 = tip
        half = width * math.sin(math.pi * min(u, .999)) ** .9 * (1 - .35 * u)
        if rnd.random() < edge_bias:                 # concentrate dots on the outline, like an engraving
            v = rnd.choice((-1, 1)) * (1 - abs(rnd.gauss(0, .08)))
        else:
            v = rnd.uniform(-1, 1)
        lx, ly = v * half, -u * length
        x = ox + lx * ca - ly * sa
        y = oy + lx * sa + ly * ca
        tone = colors[min(len(colors) - 1, int(u * len(colors) + rnd.random() * .8))]
        dots.append((x, y, rnd.uniform(.45, 1.15) * (1.1 - .4 * u), tone, rnd.uniform(.55, 1)))


def _dots_svg(dots) -> str:
    """Group dots by colour and opacity bucket; integer centres keep files small."""
    groups: dict[tuple[str, float], list[str]] = {}
    for x, y, r, c, o in dots:
        bucket = .45 if o < .6 else .7 if o < .85 else 1.0
        rr = f"{r:.1f}".lstrip("0") or "0"
        groups.setdefault((c, bucket), []).append(f'<circle cx="{round(x)}" cy="{round(y)}" r="{rr}"/>')
    return "".join(f'<g fill="{c}" opacity="{o}">{"".join(cs)}</g>' for (c, o), cs in groups.items())


def flower(cx: float, ground: float, scale: float, t: dict, seed: int = 11, aura: bool = True,
           lean: float = 0.0) -> str:
    """A dotted lotus on a curved stem with two leaves and a broken (enso-like) dotted ring."""
    rnd = random.Random(seed)
    s = scale
    pink, rose, deep, grey, pearl = t["dots"]
    dots: list[tuple[float, float, float, str, float]] = []
    top = (cx + 18 * s * lean, ground - 200 * s)
    p0, p1, p2 = (cx, ground), (cx - 26 * s, ground - 70 * s), (cx + 30 * s, ground - 140 * s)
    # stem
    for i in range(int(200 * s)):
        tt = rnd.random()
        x, y = _bezier(p0, p1, p2, top, tt)
        dots.append((x + rnd.gauss(0, 1.1 * s), y + rnd.gauss(0, .8), rnd.uniform(.4, .95), grey, rnd.uniform(.5, .95)))
    # leaves
    for tt, side, ln in ((.32, -1, 62), (.5, 1, 52)):
        bx, by = _bezier(p0, p1, p2, top, tt)
        ang = side * math.radians(rnd.uniform(58, 68))
        _petal(rnd, bx, by, ang, ln * s, 15 * s, int(170 * s), [grey, grey, rose], dots, .45)
        for k in range(int(30 * s)):                 # midrib
            u = k / (30 * s)
            dots.append((bx + math.sin(ang) * ln * s * u, by - math.cos(ang) * ln * s * u, .5, pearl, .5))
    # lotus: three layers of pointed petals fanning upward
    bx, by = top
    layers = [(9, 62, 15, (-74, 74), [deep, pink, rose]),
              (7, 74, 17, (-50, 50), [deep, pink, rose, pearl]),
              (5, 58, 15, (-24, 24), [deep, pink, rose, pearl])]
    for count, length, width, (a0, a1), colors in layers:
        for i in range(count):
            a = math.radians(a0 + (a1 - a0) * i / (count - 1) + rnd.uniform(-3, 3))
            _petal(rnd, bx, by, a, length * s * rnd.uniform(.92, 1.06), width * s, int(115 * s), colors, dots)
    for _ in range(int(100 * s)):                    # stamens: a soft cloud of light dots
        r, a = abs(rnd.gauss(0, 7 * s)), rnd.uniform(math.pi, 2 * math.pi)
        dots.append((bx + r * math.cos(a), by - 14 * s + r * .6 * math.sin(a), rnd.uniform(.5, 1.2), pearl, .9))
    global LAST_DOTS
    LAST_DOTS = len(dots)
    out = []
    if aura:  # dotted rings, one left open like an ensō
        ring = []
        for k, (r, gap) in enumerate(((118 * s, 0), (146 * s, .55))):
            n = int(2 * math.pi * r / (5.2 if k == 0 else 7.5))
            for i in range(n):
                a = 2 * math.pi * i / n
                if gap and (a % (2 * math.pi)) < gap:
                    continue
                rr = r + rnd.gauss(0, .9)
                ring.append(f'<circle cx="{round(bx + rr * math.cos(a))}" cy="{round(by - 30 * s + rr * math.sin(a))}" '
                            f'r="{rnd.uniform(.5, 1.05):.1f}"/>')
        out.append(f'<g class="turn" fill="{grey}" opacity=".5">{"".join(ring)}</g>')
    out.append(_dots_svg(dots))
    return "".join(out)


def sprig(x: float, y: float, scale: float, t: dict, seed: int, angle: float = 0) -> str:
    """A small dotted bud on a short stem, used as a corner ornament."""
    rnd = random.Random(seed)
    pink, rose, deep, grey, pearl = t["dots"]
    dots: list = []
    ca, sa = math.cos(angle), math.sin(angle)
    length = 90 * scale
    for i in range(int(70 * scale)):
        u = rnd.random()
        bend = 10 * scale * math.sin(u * math.pi)
        lx, ly = bend, -u * length
        dots.append((x + lx * ca - ly * sa + rnd.gauss(0, .7), y + lx * sa + ly * ca, rnd.uniform(.4, .8), grey, .7))
    tx, ty = x + length * sa, y - length * ca
    for a in (-24, 0, 24):
        _petal(rnd, tx, ty, angle + math.radians(a), 24 * scale, 7 * scale, int(55 * scale), [deep, pink, rose], dots)
    return _dots_svg(dots)


def butterfly(cx: float, cy: float, span: float, t: dict, seed: int = 12) -> str:
    """Fay's butterfly curve (T. H. Fay, 1989) drawn as short strokes pointing to the centre.

    r(a) = e^cos(a) − 2·cos(4a) + sin(a/12)^5, sampled over 0…24π; colour runs from the body to the wing tips.
    """
    rnd = random.Random(seed)
    pink, rose, deep, grey, pearl = t["dots"]
    ramp = [deep, pink, pink, rose, grey]
    scale = span / 2 / 5.6
    groups: dict[tuple[str, float], list[str]] = {}
    for _ in range(2200):
        a = rnd.uniform(0, 24 * math.pi)
        r = math.exp(math.cos(a)) - 2 * math.cos(4 * a) + math.sin(a / 12) ** 5
        if r <= 0:
            continue
        k = rnd.uniform(.62, .94)  # each stroke runs from the curve part of the way toward the body
        x, y = cx + r * math.sin(a) * scale, cy - r * math.cos(a) * scale
        x2, y2 = cx + r * k * math.sin(a) * scale, cy - r * k * math.cos(a) * scale
        tone = ramp[min(len(ramp) - 1, int(r / 5.2 * len(ramp)))]
        op = .45 if rnd.random() < .45 else .75 if rnd.random() < .7 else 1.0
        groups.setdefault((tone, op), []).append(f"M{x:.1f} {y:.1f}L{x2:.1f} {y2:.1f}")
    paths = "".join(f'<path d="{"".join(ds)}" stroke="{c}" stroke-opacity="{o}" stroke-width=".55" '
                    f'stroke-linecap="round"/>' for (c, o), ds in groups.items())
    tilt = rnd.uniform(-14, -8)
    return f'<g transform="rotate({tilt:.0f} {cx:.0f} {cy:.0f})"><g class="flutter">{paths}</g></g>'


def fig_caption() -> str:
    text = tr("cover_fig").format(n=LAST_DOTS)
    return text.replace(",", " ") if LOC == "ru" else text


# ── cover (two directions) ─────────────────────────────────────────────────
def cover_a(t: dict, animated: bool) -> str:
    """Direction A — editorial cover: oversized serif name, metadata rails, flower plate at right."""
    H = 440
    b = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{t["panel"]}" stroke="{t["rule"]}"/>']
    left, right = 44, W - 44
    meta = tr("cover_meta")
    b.append(MONO.text(meta[0].upper(), 10.5, left, 42, t["muted"], tracking=.18, attrs=' class="fade"'))
    b.append(MONO.text(meta[1].upper(), 10.5, W / 2, 42, t["faint"], anchor="middle", tracking=.18,
                       attrs=' class="fade"' + delay(1)))
    b.append(MONO.text(meta[2], 10.5, right, 42, t["muted"], anchor="end", tracking=.18, attrs=' class="fade"' + delay(2)))
    b.append(rule(left, 58, right, t))
    # flower plate on the right, rising from the bottom rule
    b.append(f'<defs><clipPath id="plate"><rect x="0" y="59" width="{W}" height="324"/></clipPath></defs>'
             f'<g clip-path="url(#plate)"><g class="fade"{delay(0, .25)}>{flower(650, 384, 1.0, t, seed=11)}</g></g>')
    b.append(JP.vertical("ソーニャ", 15, right - 6, 92, t["muted"]))
    b.append(f'<path d="M{right - 6} 166V214" stroke="{t["accent"]}" stroke-width="1"/>')
    # name and role
    b.append(SERIF.text("Sonya", 168, left - 6, 250, t["text"], attrs=' class="rise"' + delay(0, .05)))
    b.append(SERIF_I.text(tr("role"), 30, left, 300, t["accent"], attrs=' class="rise"' + delay(2, .05)))
    b.append(SANS.text(tr("role_line"), 15, left + 1, 330, t["muted"], tracking=.02, attrs=' class="rise"' + delay(3, .05)))
    b.append(rule(left, 384, right, t))
    b.append(MONO.text(tr("cover_index").upper(), 10, left, 410, t["muted"], tracking=.16))
    b.append(MONO.text(fig_caption(), 10, right, 410, t["faint"], anchor="end", tracking=.04))
    return svg(W, H, "".join(b), f"Sonya — {tr('role')}, {tr('role_line')}", animated)


def cover_b(t: dict, animated: bool) -> str:
    """Direction B — split cover: type block left, square flower plate with a museum caption right."""
    H = 440
    b = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{t["panel"]}" stroke="{t["rule"]}"/>']
    split = 470
    b.append(f'<path d="M{split} 0V{H}" stroke="{t["rule"]}"/>')
    b.append(JP.text("創", 300, 70, 330, t["rule"], attrs=' opacity=".55"'))
    b.append(MONO.text("01 / PROFILE", 10.5, 44, 52, t["muted"], tracking=.18))
    b.append(SERIF_I.text("sonya", 112, 40, 214, t["text"], attrs=' class="rise"'))
    b.append(SERIF.text(".", 112, 40 + SERIF_I.width("sonya", 112) + 2, 214, t["accent"]))
    b.append(SANS_M.text(tr("role").upper(), 11.5, 44, 262, t["text"], tracking=.2))
    b.append(SANS.text(tr("role_line"), 15, 44, 288, t["muted"]))
    b.append(MONO.text("samnesvoj · 2026", 10.5, 44, 400, t["faint"], tracking=.12))
    # plate
    b.append(f'<rect x="{split + 36}" y="40" width="{W - split - 72}" height="300" fill="none" stroke="{t["rule"]}"/>')
    b.append(flower(split + (W - split) / 2, 322, .78, t, seed=11))
    b.append(MONO.text(fig_caption(), 10, split + 36, 370, t["muted"], tracking=.04))
    b.append(MONO.text("pointillism · svg", 10, split + 36, 388, t["faint"], tracking=.04))
    return svg(W, H, "".join(b), f"Sonya — {tr('role')}", animated)


# ── projects (two directions) ──────────────────────────────────────────────
def preview_frames(x: float, y: float, w: float, h: float, t: dict, seed: int) -> str:
    """SONYA preview: a dotted 16:9 frame with a 9:16 crop and a small lotus inside."""
    rnd = random.Random(seed)
    out = [f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" height="{_num(h)}" fill="none" stroke="{t["rule"]}"/>']
    cw = h * 9 / 16
    cx = x + w * .58 - cw / 2
    out.append(f'<rect x="{_num(cx)}" y="{_num(y)}" width="{_num(cw)}" height="{_num(h)}" fill="none" '
               f'stroke="{t["accent"]}" stroke-width="1.2"/>')
    out.append(flower(x + w * .58, y + h - 8, h / 300, t, seed=seed, aura=False))
    for i in range(3):
        out.append(f'<path d="M{_num(x + 10)} {_num(y + h - 14 - i * 7)}h{_num(rnd.uniform(18, 46))}" '
                   f'stroke="{t["faint"]}" stroke-width="1.6" stroke-linecap="round"/>')
    out.append(MONO.text("16:9 → 9:16", 9.5, cx + 6, y + 14, t["accent"]))
    return "".join(out)


def project_row(key: str, index: int, t: dict) -> str:
    """Direction A — an index row: number, serif name, one line, mono metadata."""
    name, desc, stack, link = tr("projects")[key]
    h = 104
    b = [rule(0, h - .5, W, t)]
    b.append(MONO.text(f"{index:02d}", 11, 0, 40, t["accent"], tracking=.1))
    b.append(SERIF.text(name, 40, 52, 46, t["text"], max_w=520))
    b.append(SANS.text(desc, 14, 53, 78, t["muted"], max_w=560))
    b.append(MONO.text(stack, 10.5, W, 36, t["faint"], anchor="end", tracking=.04, max_w=240))
    b.append(MONO_M.text(link, 11, W, 78, t["accent"] if "↗" in link else t["faint"], anchor="end", tracking=.06))
    return svg(W, h, "".join(b), f"{name} — {desc}")


def project_feature(t: dict, animated: bool) -> str:
    """Direction A — SONYA spread: text column left, preview plate right."""
    name, desc, stack, link = tr("projects")["sonya"]
    h = 300
    b = [rule(0, .5, W, t), rule(0, h - .5, W, t)]
    b.append(MONO.text("01", 11, 0, 44, t["accent"], tracking=.1))
    b.append(MONO.text(tr("sonya_label").upper(), 10.5, 52, 44, t["muted"], tracking=.18))
    b.append(SERIF.text(name, 76, 48, 132, t["text"], attrs=' class="rise"'))
    words, lines, cur = desc.split(), [], ""
    for wd in words:  # wrap into a narrow column
        if SANS.width(f"{cur} {wd}".strip(), 15) > 380:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    lines.append(cur)
    for i, ln in enumerate(lines):
        b.append(SANS.text(ln, 15, 53, 172 + i * 23, t["muted"]))
    b.append(MONO.text(stack, 10.5, 53, 262, t["faint"], tracking=.04))
    b.append(MONO_M.text(link, 11, 53, 282, t["accent"], tracking=.06))
    b.append(preview_frames(476, 36, 384, 216, t, seed=5))
    return svg(W, h, "".join(b), f"{name} — {desc}", animated)


def project_card_b(key: str, t: dict) -> str:
    """Direction B — a gallery card: preview plate on top, caption below."""
    name, desc, stack, link = tr("projects")[key]
    w, h = 400, 300
    b = [f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="4" fill="{t["panel"]}" stroke="{t["rule"]}"/>']
    b.append(f'<rect x="20" y="20" width="{w - 40}" height="150" fill="none" stroke="{t["rule"]}"/>')
    seed = sum(map(ord, key))
    b.append(sprig(200, 160, 1.15, t, seed, angle=math.radians(random.Random(seed).uniform(-15, 15))))
    b.append(SERIF.text(name, 30, 20, 214, t["text"], max_w=w - 40))
    b.append(SANS.text(desc, 12.5, 21, 240, t["muted"], max_w=w - 40))
    b.append(MONO.text(stack, 10, 21, 274, t["faint"], max_w=w - 120))
    b.append(MONO_M.text(link, 10.5, w - 20, 274, t["accent"], anchor="end"))
    return svg(w, h, "".join(b), f"{name} — {desc}")


# ── sections ───────────────────────────────────────────────────────────────
def heading(key: str, t: dict) -> str:
    """Section title: mono number, serif title, Japanese gloss, hairline to the edge."""
    title = tr("headings")[key]
    h = 76
    tw = SERIF.width(title, 44)
    b = [MONO.text(HEADING_NO[key], 11, 0, 50, t["accent"], tracking=.1),
         SERIF.text(title, 44, 40, 54, t["text"]),
         JP.text(HEADING_JP[key], 12, 40 + tw + 14, 52, t["muted"], tracking=.2),
         rule(40 + tw + 14 + JP.width(HEADING_JP[key], 12, .2) + 16, 48, W, t)]
    return svg(W, h, "".join(b), title)


def about(t: dict, animated: bool) -> str:
    """About: short paragraphs over a soft floral frame, facts in a mono sidebar."""
    size, lead, col_w = 16, 25, 450
    lines: list[tuple[int, list[str]]] = []  # (paragraph index, words)
    for p, para in enumerate(tr("about")):
        cur: list[str] = []
        for word in para.split(" "):
            if SANS.width(" ".join(cur + [word]), size) > col_w and cur:
                lines.append((p, cur))
                cur = [word]
            else:
                cur.append(word)
        lines.append((p, cur))
    text_h = len(lines) * lead + (len(tr("about")) - 1) * 14
    H = max(360, int(text_h + 110))
    b = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{t["panel"]}" stroke="{t["rule"]}"/>',
         f'<defs><clipPath id="ab"><rect width="{W}" height="{H}" rx="6"/></clipPath></defs>',
         f'<g clip-path="url(#ab)" opacity=".55">{flower(805, H + 40, .9, t, seed=23, aura=False, lean=-.6)}</g>']
    y, prev = 66, 0
    for n, (p, words) in enumerate(lines):
        if p != prev:
            y += 14
            prev = p
        colour = t["text"] if p == 0 else t["muted"]
        x, runs = 52.0, []
        for k, word in enumerate(words):  # SONYA is set in the accent colour, everything else plain
            token = word + (" " if k < len(words) - 1 else "")
            hit = word.strip(".,:;—").startswith("SONYA")
            font = SANS_M if hit else SANS
            runs.append(font.text(token, size, x, y, t["accent"] if hit else colour))
            x += font.width(token, size)
        b.append(f'<g class="rise"{delay(n, .05, .03)}>{"".join(runs)}</g>')
        y += lead
    x = 572
    b.append(f'<path d="M{x - 24} 46V{H - 46}" stroke="{t["rule"]}"/>')
    fy = 70
    for label, value, sub in tr("facts"):
        b.append(MONO.text(label.upper(), 10, x, fy, t["accent"], tracking=.18))
        b.append(SANS_M.text(value, 14, x, fy + 21, t["text"], max_w=230))
        b.append(SANS.text(sub, 12.5, x, fy + 40, t["muted"], max_w=230))
        fy += 66
    return svg(W, H, "".join(b), " ".join(tr("about")), animated)


def group_label(title: str, extra: str, t: dict) -> str:
    w = 640
    b = [MONO_M.text(title.upper(), 10.5, 0, 22, t["text"], tracking=.18)]
    if extra:
        tw = MONO_M.width(title.upper(), 10.5, .18)
        b.append(MONO.text(f"+ {extra}", 10.5, tw + 18, 22, t["faint"], tracking=.02, max_w=w - tw - 18))
    return svg(w, 32, "".join(b), f"{title}{' — ' + extra if extra else ''}")


def tile(key: str) -> str:
    """Logo on a graphite tile: reads well on both GitHub themes."""
    body = (f'<rect x=".75" y=".75" width="94.5" height="94.5" rx="18" fill="{GRAPHITE}" stroke="#3A353F" '
            f'stroke-width="1.5"/>' + logo(key, 24, 24, 48))
    return svg(96, 96, body, LOGOS[key][0])


CARD = {  # the dusty-pink stack card, per page theme
    "dark": dict(fill="#C99AAE", ink=GRAPHITE, soft="#4A3842", edge="#B88BA0",
                 dots=["#4A3842", "#5E4553", "#2E242A", "#6E5A64", "#F2E4EA"]),
    "light": dict(fill=PINK, ink=GRAPHITE, soft="#5C4452", edge="#C796AB",
                  dots=["#4A3842", "#5E4553", "#2E242A", "#7A6670", "#FBF2F6"]),
}


def stack_card(t: dict, animated: bool) -> str:
    """Every stack group on one dusty-pink specimen sheet: graphite logo tiles, mono captions, a butterfly."""
    c = CARD[t["name"]]
    cols, gap, pad = 3, 28, 36
    cw = (W - 2 * pad - (cols - 1) * gap) / cols
    tile_s, tile_gap = 38, 8
    per_row = int((cw + tile_gap) // (tile_s + tile_gap))

    def wrap(text: str, size: float) -> list[str]:
        lines, cur = [], ""
        for word in text.split(" "):
            trial = f"{cur} {word}".strip()
            if MONO.width(trial, size) > cw and cur:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return [ln for ln in lines + [cur] if ln]

    cells = []
    for key, title, keys, extra in STACK:
        rows = math.ceil(len(keys) / per_row)
        extra_lines = wrap(f"+ {extra}", 9.5) if extra else []
        cells.append((title, keys, extra_lines, 34 + rows * (tile_s + tile_gap) + len(extra_lines) * 14 + 14))
    header = 118
    row_h = [max(cl[3] for cl in cells[i:i + cols]) for i in range(0, len(cells), cols)]
    H = int(header + sum(row_h) + pad - 22)

    b = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="{c["fill"]}" stroke="{c["edge"]}"/>']
    total = sum(len(k) for _, _, k, _ in STACK)
    b.append(MONO.text(f"SPECIMEN — {total} TOOLS WITH LOGOS", 10, pad, 44, c["soft"], tracking=.18))
    b.append(SERIF_I.text("tools I build with", 40, pad - 2, 92, c["ink"], attrs=' class="rise"'))
    # a small butterfly crossing the top-right corner, with its dotted trail
    pseudo = dict(t, dots=c["dots"])
    rnd = random.Random(9)
    trail = []
    for i in range(26):
        u = i / 25
        x, y = _bezier((W - 132, 86), (W - 220, 118), (W - 330, 96), (W - 380, 52), u)
        trail.append(f'<circle cx="{x + rnd.gauss(0, 1.2):.0f}" cy="{y + rnd.gauss(0, 1.2):.0f}" '
                     f'r="{rnd.uniform(.6, 1.1):.1f}" opacity="{.75 * (1 - u) + .1:.2f}"/>')
    b.append(f'<g class="fade" fill="{c["soft"]}">{"".join(trail)}</g>')
    b.append(f'<g class="fade">{butterfly(W - 96, 72, 112, pseudo, seed=21)}</g>')
    b.append(f'<path d="M{pad} {header - 10.5}H{W - pad}" stroke="{c["soft"]}" stroke-opacity=".35"/>')

    y0 = header
    for r, rh in enumerate(row_h):
        for ci, (title, keys, extra_lines, _) in enumerate(cells[r * cols:(r + 1) * cols]):
            x = pad + ci * (cw + gap)
            n = r * cols + ci
            g = [MONO_M.text(title.upper(), 10.5, x, y0 + 16, c["ink"], tracking=.16),
                 MONO.text(f"{len(keys):02d}", 10.5, x + cw, y0 + 16, c["soft"], anchor="end")]
            for i, k in enumerate(keys):
                tx = x + (i % per_row) * (tile_s + tile_gap)
                ty = y0 + 32 + (i // per_row) * (tile_s + tile_gap)
                g.append(f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{tile_s}" height="{tile_s}" rx="9" fill="{GRAPHITE}"/>')
                g.append(logo(k, tx + 9, ty + 9, tile_s - 18))
            ey = y0 + 32 + math.ceil(len(keys) / per_row) * (tile_s + tile_gap) + 10
            for j, line in enumerate(extra_lines):
                g.append(MONO.text(line, 9.5, x, ey + j * 14, c["soft"]))
            b.append(f'<g class="rise"{delay(n, .15, .06)}>{"".join(g)}</g>')
        y0 += rh
    label = "; ".join(f"{title}: " + ", ".join(LOGOS[k][0] for k in keys) + (f" + {extra}" if extra else "")
                      for _, title, keys, extra in STACK)
    return svg(W, H, "".join(b), label, animated)


def services(t: dict) -> str:
    rows = tr("services")
    h = 40 + len(rows) * 40 + 24
    b = []
    for i, (title, desc) in enumerate(rows):
        y = 34 + i * 40
        b.append(rule(0, y + 14.5, W, t))
        b.append(MONO.text(f"{i + 1:02d}", 10.5, 0, y, t["faint"], tracking=.1))
        b.append(SERIF.text(title, 22, 44, y + 2, t["text"], max_w=300))
        b.append(SANS.text(desc, 13.5, 360, y, t["muted"], max_w=500))
    b.append(MONO.text(tr("services_note"), 10.5, 0, h - 6, t["accent"], tracking=.08))
    return svg(W, h, "".join(b), "; ".join(f"{a}: {d}" for a, d in rows))


def studio(t: dict) -> str:
    items = tr("studio")
    col = W / 3
    h = 2 * 62 + 10
    b = []
    for i, (name, sub) in enumerate(items):
        r, c = divmod(i, 3)
        x, y = c * col, 30 + r * 62
        b.append(MONO.text(f"{i + 1:02d}", 10, x, y, t["faint"], tracking=.1))
        b.append(SERIF.text(name, 22, x + 30, y + 2, t["text"], max_w=col - 40))
        b.append(MONO.text(sub, 10.5, x + 31, y + 22, t["muted"], tracking=.04, max_w=col - 40))
    return svg(W, h, "".join(b), "; ".join(f"{a} ({s})" for a, s in items))


def background(t: dict) -> str:
    cols = tr("background")
    cw = W / 3
    h = 232
    b = []
    for c, (label, items) in enumerate(cols):
        x = c * cw
        b.append(MONO_M.text(label.upper(), 10.5, x, 22, t["accent"], tracking=.18))
        b.append(rule(x, 36.5, x + cw - 24, t))
        for i, (title, sub) in enumerate(items):
            y = 72 + i * 54
            latin = all(ord(ch) < 0x400 for ch in title)  # Cyrillic/Japanese fall back to Noto Serif JP,
            size = 21 if latin else 17                   # which runs larger — balance the optical size
            b.append(SERIF.text(title, size, x, y, t["text"], max_w=cw - 30))
            b.append(SANS.text(sub, 12, x, y + 20, t["muted"], max_w=cw - 30))
    return svg(W, h, "".join(b), "; ".join(f"{l}: " + ", ".join(f"{a} {s}".strip() for a, s in it) for l, it in cols))


def link_label(text: str, sub: str, t: dict) -> str:
    """A contact link set as type: serif text over a hairline, mono caption."""
    tw = max(SERIF.width(text, 24), MONO.width(sub, 10, .14))
    w, h = tw + 4, 58
    b = [MONO.text(sub.upper(), 10, 0, 14, t["faint"], tracking=.14),
         SERIF.text(text, 24, 0, 42, t["text"]),
         f'<path d="M0 52.5H{_num(tw)}" stroke="{t["accent"]}"/>']
    return svg(w, h, "".join(b), f"{sub}: {text}")


def lang_pill(code: str, name: str, active: bool, t: dict) -> str:
    """Language switch: the current language is a filled dusty-pink pill, the other an outlined one."""
    nw = SANS_M.width(name, 15, .01)
    w, h = 26 + MONO_M.width(code, 10.5, .14) + 12 + nw + 26, 44
    fill = PINK if t["name"] == "dark" else t["accent"]
    ink = GRAPHITE if t["name"] == "dark" else PEARL
    if active:
        bg = f'<rect x="1" y="1" width="{_num(w - 2)}" height="{h - 2}" rx="21" fill="{fill}"/>'
        code_c, name_c = ink, ink
    else:
        bg = f'<rect x="1" y="1" width="{_num(w - 2)}" height="{h - 2}" rx="21" fill="none" stroke="{fill}" stroke-width="1.2"/>'
        code_c, name_c = t["accent"], t["text"]
    cx = 26
    b = [bg, MONO_M.text(code, 10.5, cx, 26.5, code_c, tracking=.14)]
    cx += MONO_M.width(code, 10.5, .14) + 12
    b.append(f'<circle cx="{_num(cx - 6)}" cy="22" r="1.4" fill="{code_c}" opacity=".6"/>')
    b.append(SANS_M.text(name, 15, cx, 27.5, name_c, tracking=.01))
    return svg(w, h, "".join(b), f"{name}{' (current)' if active else ''}")


CONTACTS = [("github", "samnesvoj", "github", "https://github.com/samnesvoj"),
            ("codewars", "ex-lain", "codewars", "https://www.codewars.com/users/ex-lain")]


def colophon(t: dict, animated: bool) -> str:
    h = 236
    bx, by = W - 118, 122
    rnd = random.Random(4)
    trail = []  # a dotted flight path that drifts from the butterfly back toward the text
    for i in range(34):
        u = i / 33
        x, y = _bezier((bx - 92, by + 34), (bx - 180, by + 90), (470, by + 70), (380, by + 10), u)
        trail.append(f'<circle cx="{x + rnd.gauss(0, 1.5):.0f}" cy="{y + rnd.gauss(0, 1.5):.0f}" '
                     f'r="{rnd.uniform(.6, 1.2):.1f}" opacity="{.7 * (1 - u) + .1:.2f}"/>')
    b = [rule(0, 20.5, W - 250, t),
         f'<g class="fade" fill="{t["dots"][0]}">{"".join(trail)}</g>',
         f'<g class="fade">{butterfly(bx, by, 270, t)}</g>',
         MONO.text("fig. 02 — fay's curve", 10, W, h - 10, t["faint"], anchor="end", tracking=.04),
         SERIF_I.text(tr("thanks"), 30, 0, 82, t["text"]),
         JP.text("またね", 12, SERIF_I.width(tr("thanks"), 30) + 14, 80, t["muted"], tracking=.3),
         MONO.text(tr("colophon"), 10, 0, 114, t["faint"], tracking=.04, max_w=W - 220)]
    return svg(W, h, "".join(b), f"{tr('thanks')} — {tr('colophon')}", animated)


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
    w, h = 410, 200
    b = [MONO_M.text(tr("gh_label").upper(), 10.5, 0, 20, t["accent"], tracking=.16), rule(0, 34.5, w, t)]
    for i, (val, lab) in enumerate(zip((cal["totalContributions"], active, len(repos)), tr("stat_labels"))):
        x = i * 136
        b.append(SERIF.text(str(val), 58, x - 2, 106, t["text"]))
        b.append(MONO.text(lab, 10.5, x, 128, t["muted"], tracking=.04))
    lx = 0.0
    for i, (name, size) in enumerate(top):
        lab = f"{name.lower()} {size / total * 100:.0f}%"
        b.append(f'<circle cx="{lx + 3:.1f}" cy="172" r="3" fill="{t["dots"][[0, 3, 2, 1][i]]}"/>')
        b.append(MONO.text(lab, 10.5, lx + 11, 176, t["muted"]))
        lx += MONO.width(lab, 10.5) + 26
    return svg(w, h, "".join(b), f"GitHub: {cal['totalContributions']} contributions, {active} active days, "
                                 f"{len(repos)} projects")


def fetch_codewars() -> dict | None:
    try:
        with urllib.request.urlopen(f"https://www.codewars.com/api/v1/users/{CODEWARS_USER}", timeout=30) as r:
            return json.load(r)
    except Exception as e:  # keep the previous card on network errors
        print(f"  codewars fetch failed: {e}", file=sys.stderr)
        return None


def codewars(u: dict, t: dict) -> str:
    overall = u["ranks"]["overall"]
    w, h = 410, 200
    b = [MONO_M.text(f"CODEWARS · {CODEWARS_USER.upper()}", 10.5, 0, 20, t["accent"], tracking=.16), rule(0, 34.5, w, t)]
    for i, (val, lab) in enumerate(((overall["name"], "rank"), (u["codeChallenges"]["totalCompleted"], tr("kata")),
                                    (u["honor"], tr("honor")))):
        x = i * 136
        b.append(SERIF.text(str(val), 58 if i else 46, x - 2, 106, t["text"]))
        b.append(MONO.text(lab, 10.5, x, 128, t["muted"], tracking=.04))
    langs = " · ".join(k for k in u["ranks"]["languages"])
    b.append(MONO.text(langs, 10.5, 0, 176, t["muted"]))
    return svg(w, h, "".join(b), f"Codewars {CODEWARS_USER}: {overall['name']}, "
                                 f"{u['codeChallenges']['totalCompleted']} kata, honor {u['honor']}")


def activity(user: dict, t: dict) -> str:
    """Contribution graph drawn as dots — the same pointillist language as the flowers."""
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    step = (W - 40) / len(weeks)
    gx, gy = 40, 40
    h = gy + 7 * step + 46
    counts = sorted(d["contributionCount"] for w in weeks for d in w["contributionDays"] if d["contributionCount"])
    q = lambda p: counts[min(len(counts) - 1, int(len(counts) * p))] if counts else 1  # noqa: E731
    th = [q(.25), q(.5), q(.75)]
    radii = [1.1, 2.4, 3.2, 4.0, 4.8]
    b = []
    for i, lab in zip((1, 3, 5), ("m", "w", "f")):
        b.append(MONO.text(lab, 10, 0, gy + i * step + 3.5, t["faint"]))
    last = None
    for wi, w in enumerate(weeks):
        x = gx + wi * step + step / 2
        m = w["contributionDays"][0]["date"][5:7]
        if m != last and wi < len(weeks) - 1:
            nxt = next((j for j in range(wi + 1, len(weeks)) if weeks[j]["contributionDays"][0]["date"][5:7] != m), len(weeks))
            if last is not None or nxt - wi >= 3:
                b.append(MONO.text(tr("months")[int(m) - 1], 10, x - step / 2, gy - 16, t["faint"]))
            last = m
        for d in w["contributionDays"]:
            c = d["contributionCount"]
            lv = 0 if c == 0 else 1 + sum(c > v for v in th)
            b.append(f'<circle cx="{x:.1f}" cy="{gy + d["weekday"] * step + step / 2:.1f}" r="{radii[lv]}" '
                     f'fill="{t["heat"][lv]}"><title>{d["date"]}: {c}</title></circle>')
    b.append(MONO.text(tr("contrib_total").format(n=cal["totalContributions"]), 10.5, gx, h - 8, t["muted"], tracking=.04))
    return svg(W, h, "".join(b), tr("contrib_total").format(n=cal["totalContributions"]))


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
                write(f"{folder}/cover.svg", cover_a(t, animated))
                write(f"{folder}/about.svg", about(t, animated))
                write(f"{folder}/work-sonya.svg", project_feature(t, animated))
                write(f"{folder}/stack-card.svg", stack_card(t, animated))
                write(f"{folder}/colophon.svg", colophon(t, animated))
            d = f"{pre}{name}"
            for key in HEADING_NO:
                write(f"{d}/h-{key}.svg", heading(key, t))
            for i, key in enumerate(PROJECT_ORDER[1:], start=2):
                write(f"{d}/work-{key}.svg", project_row(key, i, t))
            for key, title, _, extra in STACK:
                write(f"{d}/g-{key}.svg", group_label(title, extra, t))
            write(f"{d}/services.svg", services(t))
            write(f"{d}/studio.svg", studio(t))
            write(f"{d}/background.svg", background(t))
            if LOC == "en":
                for code, lname in (("EN", "English"), ("RU", "Русский")):
                    for active in (True, False):
                        write(f"{name}/lang-{code.lower()}{'-active' if active else ''}.svg",
                              lang_pill(code, lname, active, t))
                for key, text, sub, _ in CONTACTS:
                    write(f"{name}/contact-{key}.svg", link_label(text, sub, t))
                # the two explored directions, kept for reference
                write(f"variants/{name}/a-cover.svg", cover_a(t, False))
                write(f"variants/{name}/b-cover.svg", cover_b(t, False))
                write(f"variants/{name}/a-work-sonya.svg", project_feature(t, False))
                for key in PROJECT_ORDER[1:3]:
                    write(f"variants/{name}/a-work-{key}.svg", project_row(key, PROJECT_ORDER.index(key) + 1, t))
                for key in PROJECT_ORDER[:4]:
                    write(f"variants/{name}/b-card-{key}.svg", project_card_b(key, t))
    for _, _, keys, _ in STACK:
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
