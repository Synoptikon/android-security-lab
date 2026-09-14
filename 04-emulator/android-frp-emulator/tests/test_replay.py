import json

from scenario import run_scenario


def test_normal_scenario_replay_is_deterministic(tmp_path):
    first = run_scenario("normal", "REPLAY-TOKEN")
    second = run_scenario("normal", "REPLAY-TOKEN")
    assert first.to_dict() == second.to_dict()
    path = tmp_path / "replay.json"
    path.write_text(json.dumps(first.to_dict(), sort_keys=True))
    assert json.loads(path.read_text()) == first.to_dict()
