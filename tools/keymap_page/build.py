#!/usr/bin/env python3
"""FrostOrtho.keymap を読んで、閲覧・変更希望の記入ができる HTML ページを生成する。

使い方:  python3 tools/keymap_page/build.py <出力先.html>
"""
import json, re, subprocess, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEYMAP = ROOT / "config" / "FrostOrtho.keymap"
TEMPLATE = pathlib.Path(__file__).with_name("template.html")

LAYER_META = [
    ("デフォルト", "JIS配列。通常の文字入力。"),
    ("ファンクション", "Enter長押し。F1〜F12、Del、Esc。"),
    ("数字・記号", "Space長押し。左手がテンキー、右手が記号。"),
    ("矢印", "かな長押し。左手に矢印・Home/End。"),
    ("Bluetooth", "F10長押し。接続先の切替、DYA Studio解除、ブートローダー。"),
    ("縦スクロール", "「-」長押し。ボールで縦スクロール。overlay側でレイヤー番号5が固定。"),
    ("マウス", "ボールを動かすと自動で入る（AML）。U/I/Oがクリック。overlay側で番号6が固定。"),
    ("マクロ・横スクロール", "「/」または英数の長押し。ボールで横スクロール。overlay側で番号7が固定。"),
    ("日本語モード", "かなを押すとON、英数を押すとOFFになる目印のレイヤー。キーは全部透過で、単独では何もしない。"),
    ("日本語モードの記号", "Space長押し中に日本語モードなら自動で重なる。? と ! を半角で出す（英数→記号→かな を自動送信）。"),
]
AML_KEEP = [6, 7, 8, 20, 30, 32]  # FrostOrtho_R.overlay の excluded-positions

def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)

def split_bindings(body):
    out = []
    for piece in body.split("&"):
        piece = " ".join(piece.split())
        if piece:
            out.append("&" + piece)
    return out

def parse(text):
    text = strip_comments(text)
    km = text[text.index("keymap {"):]
    layers = []
    for m in re.finditer(r"(\w+)\s*\{\s*bindings\s*=\s*<(.*?)>\s*;(.*?)\}\s*;", km, flags=re.S):
        name, body, rest = m.group(1), m.group(2), m.group(3)
        sm = re.search(r"sensor-bindings\s*=\s*<(.*?)>", rest, flags=re.S)
        layers.append({
            "name": name,
            "bindings": split_bindings(body),
            "sensor": split_bindings(sm.group(1)) if sm else [],
        })
    macros = re.findall(r"^\s*(\w+):\s*\w+\s*\{\s*\n\s*compatible\s*=\s*\"zmk,behavior-macro", text, flags=re.M)
    behaviors = re.findall(r"^\s*(\w+):\s*\w+\s*\{\s*\n\s*compatible\s*=\s*\"zmk,behavior-(?!macro)", text, flags=re.M)
    return layers, macros, behaviors

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def main(out):
    layers, macros, behaviors = parse(KEYMAP.read_text())
    for i, l in enumerate(layers):
        assert len(l["bindings"]) == 41, f"layer {i} ({l['name']}) has {len(l['bindings'])} bindings"
        l["label"], l["desc"] = LAYER_META[i] if i < len(LAYER_META) else (l["name"], "")
    data = {
        "keyboard": "FrostOrtho",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": git("rev-parse", "--short", "HEAD"),
        "generated": datetime.date.today().isoformat(),
        "layers": layers,
        "macros": macros,
        "behaviors": behaviors,
        "amlKeep": AML_KEEP,
    }
    html = TEMPLATE.read_text().replace("__KEYMAP_JSON__", json.dumps(data, ensure_ascii=False))
    pathlib.Path(out).write_text(html)
    print(f"wrote {out}: {len(layers)} layers, macros={macros}, behaviors={behaviors}, commit={data['commit']}")

if __name__ == "__main__":
    main(sys.argv[1])
