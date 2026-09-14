import json
from dataclasses import asdict

from scenario import run_scenario


def test_normal_scenario_replay_is_deterministic(tmp_path):
    first = asdict(run_scenario("normal", "REPLAY-TOKEN"))
    second = asdict(run_scenario("normal", "REPLAY-TOKEN"))
    assert first == second
    path = tmp_path / "replay.json"
    path.write_text(json.dumps(first, sort_keys=True))
    assert json.loads(path.read_text()) == first
