import json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def init_store(base):
    db = base / "database" / "event_intelligence.sqlite3"
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY, title TEXT, event_type TEXT, domain TEXT, event_time TEXT, verification_status TEXT, payload_json TEXT);
        CREATE TABLE IF NOT EXISTS sources(source_record_id TEXT PRIMARY KEY, event_id TEXT, source_id TEXT, source_role TEXT, url TEXT, published_at TEXT, fetched_at TEXT, available_at TEXT, evidence_note TEXT);
        CREATE TABLE IF NOT EXISTS signals(signal_id TEXT PRIMARY KEY, event_id TEXT, ticker TEXT, score INTEGER, signal_level TEXT, blockers_json TEXT);
        CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, started_at TEXT, input_path TEXT, event_count INTEGER, signal_count INTEGER, status TEXT);
        """)
    return db

def _stable_id(*parts):
    return hashlib.sha256("|".join(str(x or "") for x in parts).encode()).hexdigest()[:20]

def _normalize(records):
    merged = {}
    for raw in records:
        ticker = raw.get("subject_ticker") or ",".join(sorted(raw.get("candidate_tickers", [])))
        key = (raw["event_type"], ticker, raw.get("event_time"))
        if key not in merged:
            item = dict(raw)
            item["event_id"] = "evt_" + _stable_id(*key)
            item["source_records"] = []
            merged[key] = item
        merged[key]["source_records"].append({"source": raw["source"], "published_at": raw.get("published_at"), "fetched_at": raw.get("fetched_at"), "available_at": raw.get("available_at")})
        # Conflicting verification states remain conservative.
        statuses = {merged[key]["verification_status"], raw["verification_status"]}
        if "CONFLICTED" in statuses:
            merged[key]["verification_status"] = "CONFLICTED"
        elif statuses == {"VERIFIED"}:
            merged[key]["verification_status"] = "VERIFIED"
        elif "PARTIALLY_VERIFIED" in statuses:
            merged[key]["verification_status"] = "PARTIALLY_VERIFIED"
        else:
            merged[key]["verification_status"] = "PENDING"
    return list(merged.values())

def _link_tickers(event, watchlist):
    if event.get("subject_ticker"):
        candidates = [event["subject_ticker"]]
    else:
        candidates = event.get("candidate_tickers", [])
    return sorted(set(t for t in candidates if t in watchlist))

def _score(event, ticker, policy):
    weights = policy["weights"]
    exposure = 30 if ticker == event.get("subject_ticker") else (20 if ticker in event.get("candidate_tickers", []) else 0)
    materiality = max(0, min(5, int(event.get("materiality", 0)))) * 20
    evidence = {"VERIFIED":100,"PARTIALLY_VERIFIED":50,"PENDING":20,"CONFLICTED":0}.get(event["verification_status"],0)
    timing = 100 if event.get("event_time") else 0
    change = max(0, min(5, int(event.get("change_score",0)))) * 20
    raw = (exposure*weights["exposure"] + materiality*weights["materiality"] + evidence*weights["evidence"] + timing*weights["timing"] + change*weights["change"]) / sum(weights.values())
    blockers = []
    if event["verification_status"] != "VERIFIED":
        blockers.append("VERIFICATION_NOT_PASSED")
    if event.get("consensus_status") != "AVAILABLE":
        blockers.append("CONSENSUS_UNAVAILABLE")
    if event.get("event_type") == "EARNINGS" and ticker != event.get("subject_ticker"):
        blockers.append("ISSUER_TICKER_MISMATCH")
    if blockers:
        level = "CANDIDATE"
    elif raw >= policy["thresholds"]["actionable_alert"]:
        level = "ACTIONABLE_ALERT"
    elif raw >= policy["thresholds"]["watchlist_signal"]:
        level = "WATCHLIST_SIGNAL"
    else:
        level = "CANDIDATE"
    return round(raw), level, blockers, {"exposure":exposure,"materiality":materiality,"evidence":evidence,"timing":timing,"change":change}

def _render(events, signals, run_id):
    lines = [f"# Event Intelligence Brief — {run_id}", "", "> MVP screening output. Scores are priority scores, not probabilities, expected returns or trading instructions.", ""]
    if not signals:
        lines.append("No watchlist-linked signals.")
    for s in signals:
        e = next(x for x in events if x["event_id"] == s["event_id"])
        lines += [f"## {e['title']} — {s['ticker']}", f"- Event: `{e['event_type']}` / `{e['domain']}`",
                  f"- Time: `{e.get('event_time') or 'UNKNOWN'}`",
                  f"- Verification: **{e['verification_status']}**",
                  f"- Signal: **{s['signal_level']}** (screening score {s['score']}/100)",
                  f"- Blockers: {', '.join(s['blockers']) if s['blockers'] else 'None'}",
                  f"- Evidence: {e['source_records'][0]['source'].get('url','NOT_PROVIDED')}", ""]
    lines += ["## Data limitations", "- Consensus values are unavailable unless explicitly supplied.", "- Historical impact is not computed in this MVP; status is `INSUFFICIENT_EVIDENCE`.", "- Fixture input is synthetic and not a live market feed."]
    return "\n".join(lines) + "\n"

def run_pipeline(input_path, base):
    base = Path(base)
    raw = _load_json(input_path)
    if not isinstance(raw, list):
        raise ValueError("Input must be a JSON array of event records")
    run_id = "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + _stable_id(input_path)
    started = datetime.now(timezone.utc).isoformat()
    raw_dir, curated_dir, report_dir, runs_dir = [base / p for p in ("data/raw","data/curated","reports/daily","runs")]
    for d in (raw_dir,curated_dir,report_dir,runs_dir): d.mkdir(parents=True,exist_ok=True)
    (raw_dir/f"{run_id}.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding="utf-8")
    events = _normalize(raw)
    watchlist = set(_load_json(base/"config/watchlist.json")["tickers"])
    policy = _load_json(base/"config/policy.json")
    signals=[]
    for e in events:
        for ticker in _link_tickers(e,watchlist):
            score,level,blockers,components = _score(e,ticker,policy)
            signals.append({"signal_id":"sig_"+_stable_id(e["event_id"],ticker),"event_id":e["event_id"],"ticker":ticker,"score":score,"signal_level":level,"blockers":blockers,"score_components":components,"historical_impact_status":"INSUFFICIENT_EVIDENCE"})
    curated={"run_id":run_id,"events":events,"signals":signals}
    (curated_dir/f"{run_id}.json").write_text(json.dumps(curated,ensure_ascii=False,indent=2),encoding="utf-8")
    report = _render(events,signals,run_id)
    (report_dir/f"{run_id}.md").write_text(report,encoding="utf-8")
    db=init_store(base)
    with sqlite3.connect(db) as c:
        for e in events:
            c.execute("INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?)",(e["event_id"],e["title"],e["event_type"],e["domain"],e.get("event_time"),e["verification_status"],json.dumps(e,ensure_ascii=False)))
            for i,src in enumerate(e["source_records"]):
                sid="src_"+_stable_id(e["event_id"],src["source"].get("source_id"),src["source"].get("url"))
                c.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?,?,?,?)",(sid,e["event_id"],src["source"].get("source_id"),src["source"].get("source_role"),src["source"].get("url"),src.get("published_at"),src.get("fetched_at"),src.get("available_at"),src["source"].get("evidence_note")))
        for s in signals:
            c.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?)",(s["signal_id"],s["event_id"],s["ticker"],s["score"],s["signal_level"],json.dumps(s["blockers"])))
        c.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?,?,?,?)",(run_id,started,str(input_path),len(events),len(signals),"COMPLETED"))
    manifest={"run_id":run_id,"started_at":started,"input_path":str(input_path),"event_count":len(events),"signal_count":len(signals),"status":"COMPLETED","artifacts":[str(raw_dir/f"{run_id}.json"),str(curated_dir/f"{run_id}.json"),str(report_dir/f"{run_id}.md")]}
    (runs_dir/f"{run_id}.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return manifest
