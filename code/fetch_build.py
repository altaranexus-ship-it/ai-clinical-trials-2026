#!/usr/bin/env python3
"""
K-Dense Science Lab — "The State of AI in Clinical Trials — 2026"
Data pipeline: fetch AI/ML-flagged studies from ClinicalTrials.gov v2 API,
flatten to CSV, compute descriptive market statistics to stats.json.

Zero-dependency (stdlib only). Reproducible: re-run to refresh with live data.
Query provenance: query.intr="artificial intelligence" OR "machine learning"
"""
import json, time, urllib.request, urllib.parse, csv, collections, statistics, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
os.makedirs(DATA, exist_ok=True)

BASE = "https://clinicaltrials.gov/api/v2/studies"
QUERY = '"artificial intelligence" OR "machine learning"'
FIELDS = [
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.startDateStruct",
    "protocolSection.statusModule.completionDateStruct",
    "protocolSection.statusModule.studyFirstPostDateStruct",
    "protocolSection.designModule.studyType",
    "protocolSection.designModule.phases",
    "protocolSection.designModule.enrollmentInfo",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor",
    "protocolSection.conditionsModule.conditions",
    "protocolSection.contactsLocationsModule.locations",
]

def fetch_json(url, tries=4):
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KDenseLab/1.0 (research)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(2 * (a + 1))
    raise RuntimeError(f"fetch failed after {tries}: {last} :: {url[:120]}")

def fetch_all():
    params = {
        "query.intr": QUERY,
        "pageSize": "500",
        "countTotal": "true",
        "fields": "|".join(FIELDS),
    }
    rows, token, total, pages = [], None, None, 0
    while True:
        p = dict(params)
        if token:
            p["pageToken"] = token
        url = BASE + "?" + urllib.parse.urlencode(p)
        data = fetch_json(url)
        total = data.get("totalCount", total)
        rows.extend(data.get("studies", []))
        pages += 1
        token = data.get("nextPageToken")
        print(f"page {pages}: fetched {len(rows)}/{total}", flush=True)
        if not token or pages > 40:
            break
        time.sleep(1)
    return rows, total

def flatten(s):
    ps = s.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    status = ps.get("statusModule", {})
    design = ps.get("designModule", {})
    cond = ps.get("conditionsModule", {})
    spons = ps.get("sponsorCollaboratorsModule", {})
    locm = ps.get("contactsLocationsModule", {})
    locs = locm.get("locations") or []
    countries = sorted({l.get("country") for l in locs if l.get("country")})
    enr = design.get("enrollmentInfo") or {}
    return {
        "nctId": ident.get("nctId"),
        "briefTitle": ident.get("briefTitle"),
        "overallStatus": status.get("overallStatus"),
        "startDate": (status.get("startDateStruct") or {}).get("date"),
        "firstPosted": (status.get("studyFirstPostDateStruct") or {}).get("date"),
        "completionDate": (status.get("completionDateStruct") or {}).get("date"),
        "studyType": design.get("studyType"),
        "phases": "|".join(design.get("phases") or []),
        "enrollment": enr.get("count"),
        "leadSponsor": (spons.get("leadSponsor") or {}).get("name"),
        "sponsorClass": (spons.get("leadSponsor") or {}).get("class"),
        "conditions": " | ".join(cond.get("conditions") or [])[:200],
        "nLocations": len(locs),
        "countries": " | ".join(countries)[:300],
    }

def main():
    studies, total = fetch_all()
    raw_path = os.path.join(DATA, "ai_trials_raw.jsonl")
    with open(raw_path, "w") as f:
        for s in studies:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    flat = [flatten(s) for s in studies]
    csv_path = os.path.join(DATA, "ai_trials_flat.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
        w.writeheader()
        w.writerows(flat)

    # Registry-wide denominator for market-share context
    durl = BASE + "?" + urllib.parse.urlencode({"query.term": "", "pageSize": "1", "countTotal": "true"})
    registry_total = fetch_json(durl).get("totalCount")

    def year_of(d):
        return d[:4] if d else None

    by_year = collections.Counter(y for y in (year_of(r["firstPosted"]) for r in flat) if y)
    status = collections.Counter(r["overallStatus"] for r in flat if r["overallStatus"])
    stype = collections.Counter(r["studyType"] for r in flat if r["studyType"])
    phases = collections.Counter(
        (p if p else "N/A (observational/other)") for r in flat for p in (r["phases"].split("|") if r["phases"] else [""])
    )
    spons = collections.Counter(
        (r["leadSponsor"] or "UNKNOWN").strip() for r in flat
    )
    sclass = collections.Counter(r["sponsorClass"] for r in flat if r["sponsorClass"])
    conds = collections.Counter(
        c.strip().title() for r in flat for c in (r["conditions"].split(" | ") if r["conditions"] else [])
    )
    countries = collections.Counter(
        c for r in flat for c in (r["countries"].split(" | ") if r["countries"] else [])
    )
    enr_vals = [r["enrollment"] for r in flat if isinstance(r["enrollment"], int)]
    interventional = sum(1 for r in flat if r["studyType"] == "INTERVENTIONAL")

    stats = {
        "meta": {
            "source": "ClinicalTrials.gov API v2 (clinicaltrials.gov)",
            "query": {"query.intr": QUERY},
            "fetched_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "studies_matched": len(studies),
            "registry_total_studies": registry_total,
            "pipeline": "fetch_all.py (pagination via pageToken, fields-pruned)",
        },
        "posting_by_year": dict(sorted(by_year.items())),
        "status_distribution": dict(status.most_common()),
        "study_type_distribution": dict(stype.most_common()),
        "phase_distribution": dict(phases.most_common()),
        "sponsor_class_distribution": dict(sclass.most_common()),
        "top15_sponsors": dict(spons.most_common(15)),
        "top15_conditions": dict(conds.most_common(15)),
        "top12_countries": dict(countries.most_common(12)),
        "enrollment": {
            "n_with_value": len(enr_vals),
            "median": int(statistics.median(enr_vals)) if enr_vals else None,
            "mean": round(statistics.mean(enr_vals)) if enr_vals else None,
            "p90": int(sorted(enr_vals)[int(0.9 * len(enr_vals))]) if enr_vals else None,
        },
        "interventional_share_pct": round(100 * interventional / len(flat), 1) if flat else None,
    }
    with open(os.path.join(HERE, "..", "data", "stats.json"), "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(json.dumps(stats["meta"], indent=2))
    print("posting_by_year:", stats["posting_by_year"])
    print("top statuses:", list(stats["status_distribution"].items())[:6])
    print("top sponsors:", list(stats["top15_sponsors"].items())[:5])
    print("top conditions:", list(stats["top15_conditions"].items())[:5])
    print("OK — wrote data/ai_trials_raw.jsonl, data/ai_trials_flat.csv, analysis/stats.json")

if __name__ == "__main__":
    sys.exit(main())
