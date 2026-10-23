#!/usr/bin/env python3
"""Build README.md (English) and README.ru.md (Russian) from the same data as the assets.

    python3 scripts/build_readme.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import CONTACTS, DOCS, LOGOS, PROJECT_ORDER, STACK, TX  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/samnesvoj/samnesvoj/main/assets/"
FULL = 804  # every full-width block shares this width, so right edges line up

LINKS = {
    "sonya": "https://sonya.group/",
    "pylens": "https://py-lens.vercel.app",
    "aminelli": "https://xn--90arbb4bc.xn--80akiboadj.xn--p1ai/",
    "web": "https://xn--80aagmpqkfnk5o.xn--80akiboadj.xn--p1ai/",
}

COPY = {
    "en": dict(
        file="README.md",
        switch=(("en", True, None), ("ru", False, "README.ru.md")),
        about_more='<a href="docs/about.md">The longer version</a> · <a href="docs/projects.md">project notes</a>',
        work_more=('<a href="https://github.com/samnesvoj/PyLens">PyLens source</a> · '
                   'Open source: <a href="https://github.com/samnesvoj/readme-inspector">readme-inspector</a>, '
                   '<a href="https://github.com/samnesvoj/json-flow">json-flow</a>, '
                   '<a href="https://github.com/samnesvoj/cpp-bench-lab">cpp-bench-lab</a>'),
        stack_more="Open the stack — every logo links to its documentation",
        services_more='Write on Telegram <a href="https://t.me/removed">@removed</a> or by email.',
        activity_more=('Projects, experiments and solutions on GitHub; programming practice on '
                       '<a href="https://www.codewars.com/users/ex-lain">Codewars</a>.'),
        cover_alt="Sonya — software engineer. Backend, AI/ML, full stack.",
    ),
    "ru": dict(
        file="README.ru.md",
        switch=(("en", False, "README.md"), ("ru", True, None)),
        about_more='<a href="docs/about.ru.md">Подробнее обо мне</a> · <a href="docs/projects.md">заметки о проектах</a>',
        work_more=('<a href="https://github.com/samnesvoj/PyLens">Код PyLens</a> · '
                   'Open source: <a href="https://github.com/samnesvoj/readme-inspector">readme-inspector</a>, '
                   '<a href="https://github.com/samnesvoj/json-flow">json-flow</a>, '
                   '<a href="https://github.com/samnesvoj/cpp-bench-lab">cpp-bench-lab</a>'),
        stack_more="Раскрыть стек — каждый логотип ведёт на документацию",
        services_more='Пишите в Telegram <a href="https://t.me/removed">@removed</a> или на почту.',
        activity_more=('На GitHub — проекты, эксперименты и решения задач; на '
                       '<a href="https://www.codewars.com/users/ex-lain">Codewars</a> практикую алгоритмы.'),
        cover_alt="Sonya — software engineer. Backend, AI/ML, full stack.",
    ),
}


def build(loc: str) -> str:
    c, tx = COPY[loc], TX[loc]
    pre = "" if loc == "en" else f"{loc}/"

    def pic(name: str, alt: str, width: int | None = None, shared: bool = False) -> str:
        p = name if shared else f"{pre}{{theme}}/{name}"
        w = f' width="{width}"' if width else ""
        return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}{p.format(theme="dark")}">'
                f'<img src="assets/{p.format(theme="light")}"{w} alt="{alt}"></picture>')

    def link(href: str | None, inner: str) -> str:
        return f'<a href="{href}">{inner}</a>' if href else inner

    def head(key: str) -> str:
        return pic(f"h-{key}.svg", tx["headings"][key], FULL)

    about_alt = " ".join(tx["about"])
    out: list[str] = []
    A = out.append
    A(pic("cover.svg", c["cover_alt"], FULL))
    pills = []
    for code, active, href in c["switch"]:
        name = "English" if code == "en" else "Русский"
        img = pic(f"{{theme}}/lang-{code}{'-active' if active else ''}.svg",
                  f"{name}{' — current' if active else ''}", shared=True)
        pills.append(link(href, img))
    A(f'\n<p align="center">{"&nbsp;".join(pills)}</p>\n')

    A(head("about"))
    A(pic("about.svg", about_alt, FULL))
    A(f"\n<sub>{c['about_more']}</sub>\n")

    A(head("work"))
    name, desc, *_ = tx["projects"]["sonya"]
    A(link(LINKS["sonya"], pic("work-sonya.svg", f"{name} — {desc}", FULL)))
    for key in PROJECT_ORDER[1:]:
        name, desc, *_ = tx["projects"][key]
        A(link(LINKS.get(key), pic(f"work-{key}.svg", f"{name} — {desc}", FULL)))
    A(f"\n<sub>{c['work_more']}</sub>\n")

    A(head("stack"))
    A(pic("stack-card.svg", "; ".join(f"{title}: " + ", ".join(LOGOS[k][0] for k in keys) for _, title, keys, _ in STACK),
          FULL))
    A(f"\n<details>\n<summary><sub>{c['stack_more']}</sub></summary>\n<br>\n")
    for key, title, keys, extra in STACK:
        A(pic(f"g-{key}.svg", f"{title}{' — ' + extra if extra else ''}"))
        A("<p>")
        for k in keys:
            A(f'<a href="{DOCS[k]}"><img src="assets/stack/{k}.svg" width="44" alt="{LOGOS[k][0]}" title="{LOGOS[k][0]}"></a>')
        A("</p>\n")
    A("</details>\n")

    A(head("services"))
    A(pic("services.svg", "; ".join(f"{a}: {d}" for a, d in tx["services"]), FULL))
    A(f"\n<sub>{c['services_more']}</sub>\n")

    A(head("studio"))
    A(pic("studio.svg", "; ".join(f"{a} ({s})" for a, s in tx["studio"]), FULL) + "\n")

    A(head("background"))
    A(pic("background.svg", "; ".join(f"{label}: " + ", ".join(f"{a} {s}".strip() for a, s in items)
                                      for label, items in tx["background"]), FULL) + "\n")

    A(head("activity"))
    A("<p>")
    A(link("https://github.com/samnesvoj", pic("stats.svg", tx["gh_label"], 398)))
    A(link("https://www.codewars.com/users/ex-lain", pic("codewars.svg", "codewars · ex-lain", 398)))
    A("</p>\n")
    A(pic("activity.svg", tx["contrib_total"].format(n="…"), FULL))
    A(f"\n<sub>{c['activity_more']}</sub>\n")

    A(head("contact"))
    A("<p>")
    for key, text, sub, href in CONTACTS:
        A(link(href, pic(f"{{theme}}/contact-{key}.svg", f"{sub}: {text}", shared=True)) + "&nbsp;&nbsp;&nbsp;")
    A("</p>\n")

    A(pic("colophon.svg", tx["thanks"], FULL))
    return "\n".join(out) + "\n"


def main() -> None:
    for loc in COPY:
        (ROOT / COPY[loc]["file"]).write_text(build(loc), encoding="utf-8")
        print(f"  wrote {COPY[loc]['file']}")


if __name__ == "__main__":
    main()
