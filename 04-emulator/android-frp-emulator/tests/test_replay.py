import json
from dataclasses import asdict

from scenario import run_scenario


def test_normal_scenario_replay_is_deterministic(tmp_path):
    first = asdict(run_scenario("normal", "REPLAY-TOKEN"))
    second = asdict(run_scenario("normal", "REPLAY-TOKEN"))
    first_json = json.dumps(first, sort_keys=True)
    second_json = json.dumps(second, sort_keys=True)
    assert first_json == second_json

    path = tmp_path / "replay.json"
    path.write_text(first_json)
    restored = json.loads(path.read_text())
    assert restored == json.loads(second_json)
    assert restored["invariant_errors"] == []
