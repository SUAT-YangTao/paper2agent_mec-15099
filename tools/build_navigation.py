"""Add the navigation index to bundle.json, pulling heading text verbatim from the
review plan so the strings cannot drift from the document.

The index is exhaustive: every heading item in the plan is listed unless it is in
SKIP (page furniture and the duplicated title), and every listed heading must have
a purpose, so adding a heading to the plan without describing it is a hard error.

Usage: python build_navigation.py <work-dir> [--write]
"""
import json
import pathlib
import sys

work = pathlib.Path(sys.argv[1])
write = "--write" in sys.argv

# purpose keyed by item id; heading text is read from the page files, never typed here
PURPOSE = {
    "s001-mec-15099": {
        "p0002-b004": "Corresponding author, address and contact details",
        "p0002-b006": "Grant and award numbers supporting the study",
        "p0002-b008": "Study aims, genome data set scope and the paper's main conclusions",
        "p0002-b012": "Ecotype background, prior evidence for admixture, and the questions addressed",
        "p0003-b005": "Experimental and analytical methods, sections 2.1 to 2.8",
        "p0003-b006": "Which individuals and ecotypes were sequenced, and at what coverage",
        "p0003-b008": "Sample preparation, read mapping, filtering and the index-swapping assessment",
        "p0005-b007": "pcangsd on genotype likelihoods: SNP filters, the 225,281 SNPs analysed, and which components are significant",
        "p0005-b009": "ngsadmix assignment with K from 1 to 10, five runs per K, and the filters behind the 290,309 sites",
        "p0005-b006": "ngsDist pairwise distances, block-bootstrap support, and the FastME tree",
        "p0005-b012": "Construction of the pseudo-diploid X-chromosome PSMC analyses",
        "p0006-b004": "Definitions and equations for the D, f3, f4 and f4-ratio statistics",
        "p0007-b003": "HMM screen for private-allele tracts in 1 kb windows",
        "p0007-b007": "Reported findings, organised by analysis",
        "p0007-b010": "The 26 newly sequenced individuals at mean 5x coverage, and how they combine with published data sets",
        "p0007-b012": "PCA results separating the Antarctic types and the resident ecotype",
        "p0007-b015": "Assignment and admixture results supporting the PCA inference",
        "p0008-b005": "Private-allele tract screen and the signals attributed to an ancient ghost population",
        "p0009-b005": "Pseudodiploid coalescence plots and inferred split timing",
        "p0010-b005": "Comparison of mitochondrial and nuclear tree topologies",
        "p0010-b007": "D-statistic tests among the Antarctic types B1, B2 and C",
        "p0010-b011": "D-statistic tests between the Pacific resident and transient ecotypes",
        "p0011-b006": "F-statistic evidence for admixture between transient and resident lineages",
        "p0013-b006": "F-statistic evidence that drift exceeds admixture in the Antarctic types",
        "p0013-b008": "Interpretation of archaic tracts, founder effects and glacial-cycle vicariance",
        "p0015-b005": "Contributors, sample providers and funding acknowledged by the authors",
        "p0015-b008": "Which authors performed which parts of the work",
        "p0015-b010": "Where the sequencing data and alignments are archived",
        "p0015-b012": "ORCID identifiers for the authors",
        "p0015-b018": "Full reference list for the main article",
        "p0018-b029": "Pointers to the supplementary figures and table",
    },
    "s002-mec-15099-sm": {
        "p0001-b004": "List of the supplementary figures and table",
        "p0018-b001": "Works cited in the supplement",
    },
}

# page furniture and the title, which is repeated as both a banner and a heading
SKIP = {
    "s001-mec-15099": {"p0001-b002", "p0001-b004"},
    "s002-mec-15099-sm": {"p0001-b001", "p0001-b002"},
}

FILE = {"s001-mec-15099": "references/paper.md", "s002-mec-15099-sm": "references/supplement.md"}

navigation = []
for sid, purpose_map in PURPOSE.items():
    doc = work / "documents" / sid
    plan = json.loads((doc / "plan.json").read_text(encoding="utf-8"))
    items = {}
    for entry in plan["pages"]:
        page = json.loads((doc / entry["file"]).read_text(encoding="utf-8"))
        for item in page["items"]:
            items[item["id"]] = item
    order = plan.get("reading_order") or [i for i in items if items[i]["kind"] != "omit"]

    seen = set()
    for item_id in order:
        item = items[item_id]
        if item["kind"] != "heading" or item_id in SKIP[sid]:
            continue
        if item_id not in purpose_map:
            raise SystemExit(f"heading {item_id} in {sid} has no purpose; describe it or add it to SKIP")
        seen.add(item_id)
        navigation.append(
            {
                "file": FILE[sid],
                "heading": item["markdown"].lstrip("#").strip(),
                "purpose": purpose_map[item_id],
            }
        )
    missing = set(purpose_map) - seen
    if missing:
        raise SystemExit(f"purpose entries with no heading in {sid}: {sorted(missing)}")

bundle_path = work / "bundle.json"
bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
bundle["navigation"] = navigation

for row in navigation:
    print(f"  {row['file']:<26}{row['heading'][:78]}")

if write:
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote bundle.json with {len(navigation)} navigation rows")
else:
    print(f"(dry run: {len(navigation)} rows)")
