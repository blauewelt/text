#!/usr/bin/env python3
"""Build canzoni_it_de.html from the Italian lyrics PDF generator script.

The song data lives in the `songs = [...]` list of lyrics_pdf_generator.py
(the script that makes Canzoni_Italiane_IT_DE_v3.pdf). This tool reads that
list without running the script (no ReportLab needed, standard library only)
and writes a web page in the same style as musicas_pt_de.html.

Usage (from the repo root):
    python3 tools/build_canzoni.py path/to/lyrics_pdf_generator.py

Optional:
    --out canzoni_it_de.html   output file (default: canzoni_it_de.html next to this repo's index.html)
    --spotify URL              add a "Playlist auf Spotify öffnen" button

Data format expected in `songs`:
    ("__SECTION__", "Title", "Subtitle")                       section divider
    (title, credits, "Italiano", "Deutsch", stanzas)          song
      stanzas = [[(italian_line, german_line), ...], ...]
      credits may contain "\\n" for a second line.
"""

import argparse
import ast
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load_songs(script_path):
    """Return the `songs` list from the generator script, parsed as a literal."""
    source = Path(script_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "songs" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    sys.exit(f"No `songs = [...]` list found in {script_path}")


def group(songs):
    """Split the flat list into [(section_title, section_sub, [song, ...]), ...]."""
    sections, seen = [], set()
    current = None
    for item in songs:
        if item[0] == "__SECTION__":
            sub = item[2] if len(item) > 2 else ""
            current = (item[1], sub, [])
            sections.append(current)
            continue
        title = item[0]
        if title in seen:
            print(f"warning: '{title}' appears more than once — skipping the repeat", file=sys.stderr)
            continue
        seen.add(title)
        if current is None:
            current = ("", "", [])
            sections.append(current)
        current[2].append(item)
    return [s for s in sections if s[2]]


def e(text):
    return html.escape(text, quote=False)


def dialect_of(credits):
    m = re.search(r"dialetto\s+(\w+)", credits)
    if not m:
        return None
    names = {"napoletano": "Neapolitanisch", "romanesco": "Römisch"}
    return names.get(m.group(1).lower(), m.group(1).capitalize())


def artist_of(credits):
    first = credits.split("\n")[0]
    return first.split("·")[0].strip()


CSS = """
:root{--ink:#1a1a2e;--accent:#3D3D6B;--de:#6b6b78;--rule:#e2e2ea;--band:#F2F2F8;--dia:#8a5a2b}
*{box-sizing:border-box;scroll-behavior:smooth}
.song,.section{scroll-margin-top:92px}
body{margin:0;padding:20px 16px 64px;font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;font-size:17px;line-height:1.5;color:var(--ink);background:#fff;max-width:680px;margin-inline:auto;-webkit-text-size-adjust:100%}
h1{font-size:1.75rem;text-align:center;color:var(--accent);font-style:italic;margin:.2em 0 .1em}
.sub{text-align:center;color:var(--de);font-style:italic;font-size:.9rem;margin-bottom:1.6em}
.note{background:var(--band);border-left:3px solid var(--accent);padding:12px 14px;font-size:.88rem;line-height:1.55;margin:0 0 1.5em;border-radius:0 4px 4px 0}
.note strong{color:var(--accent)}
.section{text-align:center;margin:3.2em 0 2.4em}
.section-title{font-size:1.55rem;font-weight:700;color:var(--accent);margin:0}
.section-sub{font-style:italic;color:var(--de);font-size:.95rem;margin:.2em 0 0}
.song{margin:0 0 3em}
.song h2{font-size:1.3rem;color:var(--accent);font-style:italic;margin:0 0 .15em;line-height:1.25}
.credit{color:var(--de);font-style:italic;font-size:.85rem;margin:0 0 .7em}
.accentline{height:1.5px;background:var(--accent);border:0;margin:0 0 .9em}
.chips{margin:0 0 .9em}
.chip{display:inline-block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:.68rem;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:3px;margin:0 5px 5px 0;background:var(--band);color:var(--accent);white-space:nowrap}
.chip.dia{background:#f6ece0;color:var(--dia)}
.stanza{margin:0 0 1.6em}
.pair{margin:0 0 .55em}
.pair:last-child{margin-bottom:0}
.it{display:block}
.de{display:block;font-style:italic;color:var(--de);font-size:.94em}
.divider{text-align:center;color:var(--de);margin:3em 0;font-size:1.1rem;letter-spacing:.6em}
table.overview{width:100%;border-collapse:collapse;font-size:.8rem;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
table.overview th{text-align:left;background:var(--accent);color:#fff;padding:7px 8px;font-size:.7rem;letter-spacing:.04em;text-transform:uppercase;font-weight:600}
table.overview td{padding:7px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
table.overview tr:nth-child(even) td{background:var(--band)}
table.overview a{color:inherit;text-decoration:none}
.footer{margin-top:3em;padding-top:1.2em;border-top:1px solid var(--rule);font-size:.78rem;color:var(--de);font-style:italic;line-height:1.6}
.jumpnav{position:sticky;top:0;z-index:100;background:#fff;margin:0 -16px 2.2em;padding:12px 16px 12px;border-bottom:1px solid var(--rule);box-shadow:0 2px 6px rgba(26,26,46,.06);overflow-x:auto;-webkit-overflow-scrolling:touch;white-space:nowrap;scrollbar-width:none}
.jumpnav::-webkit-scrollbar{display:none}
.jumpnav a{display:inline-block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:.72rem;letter-spacing:.02em;padding:6px 11px;border-radius:4px;margin:0 6px 0 0;background:var(--band);color:var(--accent);text-decoration:none;white-space:nowrap;transition:background .15s,color .15s}
.jumpnav a.sec{background:var(--accent);color:#fff}
.jumpnav a:last-child{margin-right:16px}
.jumpnav a:active{background:var(--accent);color:#fff}
.jumpnav-label{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;color:var(--de);display:block;margin-bottom:7px}
.plink{text-align:center;margin:0 0 1.6em}
.plink a{display:inline-block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:.8rem;letter-spacing:.02em;padding:9px 18px;border-radius:20px;background:#1DB954;color:#fff;text-decoration:none;font-weight:600}
"""


def render(sections, spotify=None):
    n_songs = sum(len(s[2]) for s in sections)
    out = []
    w = out.append
    w('<!DOCTYPE html>\n<html lang="de">\n<head><meta charset="UTF-8">'
      '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
      '<title>Canzoni Italiane · IT–DE</title>\n<style>' + CSS + '</style></head><body>\n')
    w('<h1>Canzoni Italiane</h1>\n')
    w(f'<p class="sub">{n_songs} Titel · Texte mit Übersetzung · IT → DE</p>\n')
    if spotify:
        w(f'<p class="plink"><a href="{html.escape(spotify)}" target="_blank" rel="noopener">'
          'Playlist auf Spotify öffnen</a></p>\n')
    w('<div class="note"><strong>Zum Lesen:</strong> Italienisch oben, deutsche Übersetzung kursiv und grau '
      'darunter. Die Übersetzung ist bewusst wörtlich, damit man die italienischen Wörter wiederfindet. '
      'Dialekttitel (Neapolitanisch, Römisch) sind markiert.</div>\n\n')

    # Jump navigation: section chips (dark) followed by their numbered songs
    nav = ['<nav class="jumpnav"><span class="jumpnav-label">Direkt zum Song</span>']
    num = 0
    for si, (stitle, _sub, items) in enumerate(sections, 1):
        if stitle:
            nav.append(f'<a class="sec" href="#sec{si}">{e(stitle)}</a>')
        for song in items:
            num += 1
            nav.append(f'<a href="#s{num}">{num} {e(song[0])}</a>')
    nav.append('</nav>\n')
    w(''.join(nav))

    num = 0
    rows = []
    for si, (stitle, ssub, items) in enumerate(sections, 1):
        if stitle:
            w(f'\n<div class="section" id="sec{si}"><p class="section-title">{e(stitle)}</p>')
            if ssub:
                w(f'<p class="section-sub">{e(ssub)}</p>')
            w('</div>\n')
        for title, credits, _h_it, _h_de, stanzas in items:
            num += 1
            w(f'\n<!-- ═══ {num}. {e(title)} ═══ -->\n<div class="song" id="s{num}">\n')
            w(f'  <h2>{num} · {e(title)}</h2>\n')
            credit_lines = [ln for ln in credits.split("\n") if not re.match(r"\(testo in dialetto", ln)]
            w('  <p class="credit">' + '<br>'.join(e(ln) for ln in credit_lines) + '</p>\n')
            w('  <hr class="accentline">\n')
            chips = []
            dia = dialect_of(credits)
            if dia:
                chips.append(f'<span class="chip dia">Dialekt · {e(dia)}</span>')
            if ssub:
                chips.append(f'<span class="chip">{e(ssub)}</span>')
            if chips:
                w('  <div class="chips">\n    ' + '\n    '.join(chips) + '\n  </div>\n')
            for stanza in stanzas:
                w('  <div class="stanza">\n')
                for it_line, de_line in stanza:
                    w(f'    <div class="pair"><span class="it" lang="it">{e(it_line)}</span>\n'
                      f'    <span class="de">{e(de_line)}</span></div>\n')
                w('  </div>\n')
            w('</div>\n')
            rows.append(f'<tr><td>{num}</td><td><a href="#s{num}">{e(title)}</a></td>'
                        f'<td>{e(artist_of(credits))}</td><td>{e(stitle)}</td></tr>')

    w('\n<div class="divider">· · ·</div>\n\n<table class="overview">\n'
      '<tr><th>#</th><th>Titel</th><th>Interpret</th><th>Abschnitt</th></tr>\n')
    w('\n'.join(rows) + '\n</table>\n\n')
    w('<p class="footer">Erstellt für Chris · Übersetzungsprinzip: wörtlich vor poetisch, grammatisch korrekt. '
      'Empfehlungen von Andrea und Mauro.</p>\n')
    w('<p class="footer" style="margin-top:.8em;padding-top:0;border-top:0">'
      '<a href="./" style="color:inherit">← Weitere Texte</a></p>\n</body></html>\n')
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="path to lyrics_pdf_generator.py")
    ap.add_argument("--out", default=str(REPO / "canzoni_it_de.html"))
    ap.add_argument("--spotify", help="optional Spotify playlist URL")
    args = ap.parse_args()

    sections = group(load_songs(args.script))
    page = render(sections, args.spotify)
    Path(args.out).write_text(page, encoding="utf-8")
    n = sum(len(s[2]) for s in sections)
    print(f"wrote {args.out}: {len(sections)} sections, {n} songs")


if __name__ == "__main__":
    main()
