import json, tempfile, unittest
from pathlib import Path
from src.event_intelligence.pipeline import _normalize, _score, run_pipeline

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.records=json.loads(Path("fixtures/events.json").read_text())
    def test_dedup_preserves_source_records(self):
        events=_normalize(self.records)
        self.assertEqual(len(events),2)
        nvda=next(e for e in events if e["event_type"]=="EARNINGS")
        self.assertEqual(len(nvda["source_records"]),2)
        self.assertIn("published_at", nvda["source_records"][0])
    def test_pending_event_is_not_alert(self):
        policy=json.loads(Path("config/policy.json").read_text())
        score,level,blockers,_=_score(self.records[0],"MSFT",policy)
        self.assertEqual(level,"CANDIDATE")
        self.assertIn("VERIFICATION_NOT_PASSED",blockers)
    def test_fixture_pipeline_writes_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for d in ["config","fixtures"]: (base/d).mkdir()
            for f in ["watchlist.json","policy.json"]: (base/"config"/f).write_text(Path("config"/Path(f)).read_text())
            (base/"fixtures"/"events.json").write_text(Path("fixtures/events.json").read_text())
            result=run_pipeline(base/"fixtures"/"events.json",base)
            self.assertEqual(result["status"],"COMPLETED")
            self.assertGreater(result["event_count"],0)
            self.assertTrue((base/"database"/"event_intelligence.sqlite3").exists())

if __name__=="__main__": unittest.main()
