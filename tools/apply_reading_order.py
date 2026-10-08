"""Apply the reviewed reading_order and prose joins to the s001 review plan.

Usage: python apply_reading_order.py <documents/s001-mec-15099> [--write]

Without --write it only reports what would change.
"""
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
write = "--write" in sys.argv

plan_path = root / "plan.json"
plan = json.loads(plan_path.read_text(encoding="utf-8"))

pages = []
for entry in plan["pages"]:
    p = json.loads((root / entry["file"]).read_text(encoding="utf-8"))
    pages.append((entry, p))

order = []
byid = {}
for entry, p in pages:
    for it in p["items"]:
        if it["kind"] != "omit":
            order.append(it["id"])
            byid[it["id"]] = (entry, p, it)

original = list(order)

# --- relocations: each figure image sits with its caption and outside the prose
MOVES = [
    # p0003-b013 "...(Morin et al.," + p0005-b004 "2010), and the counts..." -> the
    # continuation must directly follow its antecedent, so it moves ahead of the
    # full-page Figure 1 image (p0004) and its caption (p0005-b003).
    (["p0005-b004"], "p0003-b013"),
    # Figure 2 image + caption move below the paragraph whose sentence they interrupt.
    (["p0009-b003", "p0009-b007"], "p0009-b008"),
    # Figure 3 (PSMC plots, cited in 3.5) belongs at the end of section 3.5, which is
    # the last item of page 10 before the 3.6 heading. It cannot sit after p0011-b005
    # because p0011-b005 is itself a continuation of p0010-b013.
    (["p0011-b003", "p0011-b004"], "p0010-b004"),
    # p0013-b004 continues p0011-b008 directly; Figure 4 (image p0012, caption
    # p0013-b003) then follows the 3.8 paragraph that b004 closes.
    (["p0013-b004"], "p0011-b008"),
    (["p0012-b003", "p0013-b003"], "p0013-b004"),
    # Figure 5 image + caption move to the end of section 3.10.
    (["p0013-b011", "p0013-b010"], "p0013-b005"),
]

for ids, anchor in MOVES:
    for i in ids:
        order.remove(i)
    at = order.index(anchor) + 1
    order[at:at] = ids

# --- joins now legal because the antecedent is adjacent prose
JOINS = {
    "p0009-b004": "space",  # "(at posterior probability" + ">0.5) highlighted ..."
    "p0011-b005": "space",  # "inference of recent" + "shared ancestry between ..."
    "p0013-b004": "space",  # "results from PCA" + "(Figure 1c) and D-statistics ..."
    "p0014-b003": "space",  # "The same high" + "latitude populations show ..."
}

# --- validate
indexed = {iid: it for iid, (e, p, it) in byid.items()}
assert len(order) == len(set(order)), "duplicate id in reading_order"
assert set(order) == set(indexed), "reading_order must list every non-omitted item exactly once"

for iid, it in indexed.items():
    j = it.get("join_previous")
    if not j:
        continue
    prev = order[order.index(iid) - 1]
    pk = indexed[prev]["kind"]
    status = "ok" if pk in {"text", "caption"} else "WILL FAIL"
    print(f"  join {iid} ({it['kind']}) <- {prev} ({pk})  [{j}]  {status}")

for iid, j in JOINS.items():
    indexed[iid]["join_previous"] = j

# --- report the new neighbourhood of every relocated item
moved = {i for ids, _ in MOVES for i in ids}
print("\n-- new context --")
for n, iid in enumerate(order):
    if iid not in moved:
        continue
    lo = max(0, n - 2)
    hi = min(len(order), n + 3)
    print(f"  ...")
    for k in range(lo, hi):
        mark = ">>" if order[k] == iid else "  "
        txt = (indexed[order[k]].get("markdown") or "").replace("\n", " ")[:46]
        print(f"  {mark} {order[k]:<14}{indexed[order[k]]['kind']:<9}{txt}")

print(f"\n{len(order)} non-omitted items, {len(original)} before")
if not write:
    print("(dry run; pass --write to apply)")
    raise SystemExit(0)

touched = set()
for iid in JOINS:
    touched.add(byid[iid][0]["file"])
plan["reading_order"] = order

for entry, p in pages:
    if entry["file"] in touched:
        (root / entry["file"]).write_text(
            json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {entry['file']}")
plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("wrote plan.json with reading_order")
