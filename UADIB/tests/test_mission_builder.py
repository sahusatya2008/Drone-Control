from core.mission_builder import MissionBuilder, Waypoint


def test_simulation_has_distance() -> None:
    builder = MissionBuilder()
    points = [
        Waypoint(lat=12.9716, lon=77.5946, alt=10),
        Waypoint(lat=12.9720, lon=77.6000, alt=20),
    ]
    sim = builder.simulate(points)
    assert sim["distance_m"] > 0
    assert sim["eta_s"] > 0
