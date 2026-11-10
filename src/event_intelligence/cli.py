import argparse, json
from pathlib import Path
from .pipeline import run_pipeline, init_store

def main():
    p = argparse.ArgumentParser(prog="event-intelligence")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    r = sub.add_parser("run")
    r.add_argument("--input", required=True)
    r.add_argument("--project-dir", default=".")
    args = p.parse_args()
    if args.command == "init":
        init_store(Path("."))
        print("Initialized database/event_intelligence.sqlite3")
    else:
        result = run_pipeline(Path(args.input), Path(args.project_dir))
        print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
