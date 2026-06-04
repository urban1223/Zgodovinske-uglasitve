import re
from pathlib import Path

ROOT = Path(__file__).parent
SKIP = {"aron.html", "index.html"}

KEYBOARD_CSS = """        /* POPRAVLJENO: Dodan box-sizing za celotno mrezo in gumbe, da ostanejo znotraj okvira */
        .keyboard { 
            display: grid; 
            grid-template-columns: repeat(6, 1fr); 
            gap: 10px; 
            margin-top: 10px; 
            width: 100%; 
            box-sizing: border-box; 
        }
        .key { 
            background: #141b29; 
            border: 1px solid #334; 
            padding: 22px 0; 
            border-radius: 12px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold; 
            color: #aaa; 
            transition: 0.1s; 
            box-sizing: border-box; 
            width: 100%;
        }
        .key.playing { background: var(--amber); color: #000; border-color: var(--amber); box-shadow: 0 0 15px var(--amber); }

        .oct-ctrl { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 11px; margin-top: 8px; opacity: 0.7; user-select: none; }
        .oct-arrow { padding: 4px 6px; cursor: pointer; transition: color 0.1s; font-size: 12px; }
        .oct-arrow:hover { color: var(--amber); }
        .key.playing .oct-arrow:hover { color: #000; }

        @media (max-width: 500px) {
            .panel { padding: 20px 12px; }
            .keyboard { gap: 6px; }
            .key { padding: 18px 0; font-size: 15px; }
            .oct-ctrl { gap: 4px; font-size: 10px; }
            .oct-arrow { padding: 4px; }
        }"""

CHANGE_NOTE_OCTAVE = """
function changeNoteOctave(idx, dir, event) {
    if (event) event.stopPropagation();
    noteOctaves[idx] = Math.max(1, Math.min(6, noteOctaves[idx] + dir));
    
    document.getElementById(`oct-val-${idx}`).innerText = noteOctaves[idx];
    
    if (activeOscs[idx]) {
        activeOscs[idx].osc.frequency.setTargetAtTime(getFreq(idx), audioCtx.currentTime, 0.03);
    }
}
"""

RENDER_KEYBOARD = """
function renderKeyboard() {
    const kb = document.getElementById('kb');
    kb.innerHTML = '';
    noteNames.forEach((name, i) => {
        const btn = document.createElement('button');
        btn.className = 'key' + (activeOscs[i] ? ' playing' : '');
        btn.id = 'key-' + i;
        btn.onclick = () => toggleTone(i);
        
        btn.innerHTML = `
            <div>${name}</div>
            <div class="oct-ctrl">
                <span class="oct-arrow" onclick="changeNoteOctave(${i}, -1, event)">▼</span>
                <span id="oct-val-${i}" style="font-family: monospace; font-weight: bold;">${noteOctaves[i]}</span>
                <span class="oct-arrow" onclick="changeNoteOctave(${i}, 1, event)">▲</span>
            </div>
        `;
        kb.appendChild(btn);
    });
}
"""


def patch_css(text):
    text = re.sub(r"\s*\.synth-controls\s*\{[^}]*\}\s*", "\n", text, flags=re.DOTALL)
    text = re.sub(r"\s*\.octave-btn\s*\{[^}]*\}\s*", "\n", text, flags=re.DOTALL)
    text = re.sub(r"\s*#octave-label\s*\{[^}]*\}\s*", "\n", text, flags=re.DOTALL)
    text = re.sub(
        r"\s*\.keyboard\s*\{[^}]*\}\s*\.key\s*\{[^}]*\}\s*\.key\.playing\s*\{[^}]*\}\s*",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\s*@media\s*\(max-width:\s*500px\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*",
        "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    return text.replace("    </style>", KEYBOARD_CSS + "\n    </style>", 1)


def patch_html(text):
    return re.sub(
        r'\s*<div class="synth-controls">.*?</div>\s*',
        "\n\n    ",
        text,
        flags=re.DOTALL,
    )


def insert_change_note_octave(text):
    if "function changeNoteOctave" in text:
        return text
    return re.sub(
        r"(function updateAll\(\)\s*\{.*?\n\})\s*",
        r"\1\n" + CHANGE_NOTE_OCTAVE + "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )


def patch_js_standard(text):
    text = re.sub(
        r"let currentOctave = \d+;",
        "let noteOctaves = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3];",
        text,
    )
    text = re.sub(
        r"function changeOctave\([^)]*\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"function renderKeyboard\(\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*",
        RENDER_KEYBOARD + "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = insert_change_note_octave(text)
    text = re.sub(
        r"Math\.pow\(2,\s*currentOctave\s*-\s*3\)",
        "Math.pow(2, noteOctaves[idx] - 3)",
        text,
    )
    if "function getFreq(idx)" in text:
        text = re.sub(
            r"function getFreq\(idx\)\s*\{[^\}]+\}",
            "function getFreq(idx) {\n    return currentTargets[idx] * Math.pow(2, noteOctaves[idx] - 3);\n}",
            text,
            count=1,
        )
    else:
        text = re.sub(
            r"(function toggleTone\(idx\)\s*\{)",
            "function getFreq(idx) {\n    return currentTargets[idx] * Math.pow(2, noteOctaves[idx] - 3);\n}\n\n\\1",
            text,
            count=1,
        )
    return text


def patch_js_just(text):
    text = patch_js_standard(text)
    return re.sub(
        r"function getFreq\(idx\)\s*\{[^\}]+\}",
        "function getFreq(idx) {\n    return baseC * ratios[idx] * Math.pow(2, noteOctaves[idx] - 3);\n}",
        text,
        count=1,
    )


def patch_js_valotti_werk(text):
    text = re.sub(
        r"let currentOctave = \d+;",
        "let noteOctaves = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3];",
        text,
    )
    text = re.sub(r"function changeOctave\([^)]*\)\s*\{[^}]*\}\s*", "", text, flags=re.DOTALL)
    text = re.sub(
        r"function renderKeyboard\(\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*",
        RENDER_KEYBOARD + "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    if "function getFreq(idx)" not in text:
        text = re.sub(
            r"(function updateAll\(\)\s*\{)",
            "function getFreq(idx) {\n    return getNoteFrequencies()[idx] * Math.pow(2, noteOctaves[idx] - 3);\n}\n\n\\1",
            text,
            count=1,
        )
    text = insert_change_note_octave(text)
    text = re.sub(
        r"let targetFreq = freqs\[idx\] \* Math\.pow\(2, currentOctave - 3\);",
        "let targetFreq = getFreq(idx);",
        text,
    )
    text = re.sub(
        r"activeOscs\[idx\]\.osc\.frequency\.setTargetAtTime\(freqs\[idx\] \* Math\.pow\(2, currentOctave - 3\),",
        "activeOscs[idx].osc.frequency.setTargetAtTime(getFreq(idx),",
        text,
    )
    text = re.sub(
        r"osc\.frequency\.setValueAtTime\(freqs\[idx\] \* Math\.pow\(2, currentOctave - 3\),",
        "osc.frequency.setValueAtTime(getFreq(idx),",
        text,
    )
    return text


def patch_js_rameau(text):
    text = re.sub(
        r"let currentOctave = \d+;",
        "let noteOctaves = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3];",
        text,
    )
    text = re.sub(r"function changeOctave\([^)]*\)\s*\{[^}]*\}\s*", "", text, flags=re.DOTALL)
    text = re.sub(
        r"function renderKeyboard\(\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*",
        RENDER_KEYBOARD + "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"function getNoteFrequencies\(\)\s*\{[^\}]+\}",
        """function getNoteFrequencies() {
    const aRef = parseFloat(document.getElementById('a-ref').value) || 415;
    const ratio = aRef / 830.0;
    return rameauHzBase.map((f, i) => f * ratio * Math.pow(2, noteOctaves[i] - 3));
}""",
        text,
        count=1,
    )
    if "function changeNoteOctave" not in text:
        text = re.sub(
            r"(function getNoteFrequencies\(\)\s*\{.*?\n\})\s*",
            r"\1\n" + CHANGE_NOTE_OCTAVE + "\n",
            text,
            count=1,
            flags=re.DOTALL,
        )
    if "function getFreq(idx)" not in text:
        text = re.sub(
            r"(function toggleTone\(idx\)\s*\{)",
            "function getFreq(idx) {\n    return getNoteFrequencies()[idx];\n}\n\n\\1",
            text,
            count=1,
        )
    text = re.sub(
        r"const freqs = getNoteFrequencies\(\);\s*\n\s*const wave =",
        "const wave =",
        text,
    )
    text = re.sub(
        r"osc\.frequency\.setValueAtTime\(freqs\[idx\],",
        "osc.frequency.setValueAtTime(getFreq(idx),",
        text,
    )
    text = re.sub(
        r"activeOscs\[idx\]\.osc\.frequency\.setTargetAtTime\(freqs\[idx\],",
        "activeOscs[idx].osc.frequency.setTargetAtTime(getFreq(idx),",
        text,
    )
    return text


def main():
    for path in sorted(ROOT.glob("*.html")):
        if path.name in SKIP:
            continue
        text = path.read_text(encoding="utf-8")
        text = patch_css(patch_html(text))
        if path.name == "just.html":
            text = patch_js_just(text)
        elif path.name in ("valotti.html", "werkmeister.html"):
            text = patch_js_valotti_werk(text)
        elif path.name == "rameau.html":
            text = patch_js_rameau(text)
        else:
            text = patch_js_standard(text)
        path.write_text(text, encoding="utf-8")
        print("OK", path.name)


if __name__ == "__main__":
    main()
