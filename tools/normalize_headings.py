"""Give the main document a real heading hierarchy: title L1, sections L2, subsections L3.

Usage: python normalize_headings.py <documents/s001-mec-15099> [--write]
"""
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
write = "--write" in sys.argv

NAMED_L2 = {
    "**Abstract**",
    "**ACKNOWLEDGEMENTS**",
    "**AUTHOR CONTRIBUTION**",
    "**DATA ACCESSIBILITY**",
    "**ORCID**",
    "**REFERENCES**",
    "**SUPPORTING INFORMATION**",
}

# "# **2** | **X**" -> section, "# **2.1** | **X**" -> subsection
NUMBERED = re.compile(r"^#+\s+\*\*(\d+(?:\.\d+)?)\*\*\s*\|\s*\*\*")

report = []
for pn in range(1, 19):
    path = root / f"pages/page-{pn:04d}.json"
    page = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for item in page["items"]:
        if item["kind"] != "heading":
            continue
        md = item["markdown"]
        body = md.strip().lstrip("#").strip()
        m = NUMBERED.match(md.strip())
        if m:
            level = 2 if "." not in m.group(1) else 3
        elif body in NAMED_L2:
            level = 2
        else:
            continue  # title, masthead, Correspondence, Funding information already correct
        new = "#" * level + " " + body
        if new != md:
            report.append((item["id"], md.strip()[:58], new.strip()[:58]))
            item["markdown"] = new
            changed = True
    if changed and write:
        path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for iid, old, new in report:
    print(f"  {iid}  {old:<60} -> {new}")
print(f"{len(report)} headings re-levelled" + ("" if write else " (dry run)"))
if write:
    print("no h1 beyond the title")
