import os
import math
import requests

TOKEN = os.environ.get('GITHUB_TOKEN', '')
USERNAME = 'c3t4r4'
MAX_LANGS = 8
COLS = 2

DRACULA = {
    'bg': '#282a36',
    'current_line': '#44475a',
    'foreground': '#f8f8f2',
    'comment': '#6272a4',
    'purple': '#bd93f9',
    'cyan': '#8be9fd',
    'green': '#50fa7b',
    'orange': '#ffb86c',
    'pink': '#ff79c6',
    'red': '#ff5555',
    'yellow': '#f1fa8c',
}

LANG_COLORS = [
    DRACULA['purple'],
    DRACULA['cyan'],
    DRACULA['green'],
    DRACULA['orange'],
    DRACULA['pink'],
    DRACULA['red'],
    DRACULA['yellow'],
    DRACULA['comment'],
]

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'X-GitHub-Api-Version': '2022-11-28',
}

FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif"


def fetch_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f'https://api.github.com/users/{USERNAME}/repos',
            headers=HEADERS,
            params={'per_page': 100, 'page': page},
            timeout=30,
        )
        data = r.json()
        if not data or isinstance(data, dict):
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_languages(repos):
    lang_bytes = {}
    for repo in repos:
        if repo.get('fork', True):
            continue
        try:
            r = requests.get(repo['languages_url'], headers=HEADERS, timeout=10)
            for lang, count in r.json().items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + count
        except Exception:
            pass
    return lang_bytes


def generate_svg(lang_pcts):
    W = 400
    PAD = 20
    ROW_H = 26
    DOT_R = 6
    rows = math.ceil(len(lang_pcts) / COLS)
    H = 52 + rows * ROW_H + PAD
    col_w = (W - PAD * 2) // COLS

    items = []
    for i, (lang, pct) in enumerate(lang_pcts):
        col = i % COLS
        row = i // COLS
        cx = PAD + col * col_w + DOT_R
        cy = 56 + row * ROW_H
        color = LANG_COLORS[i % len(LANG_COLORS)]
        items.append(f'  <circle cx="{cx}" cy="{cy}" r="{DOT_R}" fill="{color}"/>')
        items.append(
            f'  <text x="{cx + DOT_R + 8}" y="{cy + 5}" '
            f'fill="{DRACULA["foreground"]}" font-size="12" font-family="{FONT}">'
            f'{lang} {pct:.2f}%</text>'
        )

    return (
        f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <rect width="{W}" height="{H}" rx="10" fill="{DRACULA["bg"]}"/>\n'
        f'  <text x="{PAD}" y="32" fill="{DRACULA["pink"]}" font-size="16" '
        f'font-weight="bold" font-family="{FONT}">Most Used Languages</text>\n'
        f'  <rect x="{PAD}" y="40" width="{W - PAD * 2}" height="1" fill="{DRACULA["current_line"]}"/>\n'
        + '\n'.join(items)
        + '\n</svg>'
    )


repos = fetch_repos()
lang_bytes = fetch_languages(repos)

if not lang_bytes:
    print('No language data found')
    raise SystemExit(1)

total = sum(lang_bytes.values())
top = sorted(lang_bytes.items(), key=lambda x: -x[1])[:MAX_LANGS]
lang_pcts = [(lang, count / total * 100) for lang, count in top]

svg = generate_svg(lang_pcts)

os.makedirs('assets', exist_ok=True)
with open('assets/github-langs.svg', 'w', encoding='utf-8') as f:
    f.write(svg)

print(f'Generated SVG: {len(lang_pcts)} languages, {total:,} bytes total')
