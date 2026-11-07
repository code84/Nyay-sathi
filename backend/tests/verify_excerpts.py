"""Check that every quoted fragment under '## Excerpt' in a library item really
appears in that item's source PDF. Run:  python tests/verify_excerpts.py [library_dir]
Needs: pip install pypdf. A fragment must not cross a PDF page break."""
import re, sys, pathlib
from pypdf import PdfReader

def norm(t):
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    t = t.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", "", t).lower()

def pdf_text(path, cache={}):
    if path not in cache:
        cache[path] = norm(" ".join((p.extract_text() or "") for p in PdfReader(path).pages))
    return cache[path]

def main(lib="library"):
    lib = pathlib.Path(lib); bad = 0; total = 0
    for f in sorted(lib.rglob("*.md")):
        txt = f.read_text(encoding="utf-8")
        m = re.search(r"^source_pdf:\s*(\S+)", txt, re.M)
        sec = re.search(r"## Excerpt.*?\n(.*?)(?=\n## )", txt, re.S)
        if not m or not sec:
            continue
        pdf = lib.parent / m.group(1)
        if not pdf.exists():
            print(f"{f.name}: PDF missing: {pdf}"); bad += 1; continue
        body = pdf_text(str(pdf))
        for frag in re.findall(r'"([^"]+)"', sec.group(1)):
            total += 1
            if norm(frag) not in body:
                bad += 1; print(f"FAIL {f.name}: {frag[:90]}...")
    print(f"checked {total} fragments, {bad} failures")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main(*sys.argv[1:2])
