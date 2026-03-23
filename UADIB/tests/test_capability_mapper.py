from core.capability_mapper import CapabilityMapper
from core.models import DroneProfile


def test_capability_mapping_camera() -> None:
    mapper = CapabilityMapper()
    profile = DroneProfile(
        drone_model="Test",
        flight_controller="FC",
        firmware="1.0",
        sensors=["IMU", "GPS"],
        motors=4,
        camera=True,
        lidar=False,
        gps_modules=1,
        battery_cells=4,
    )
    caps = mapper.map(profile)
    assert caps.camera_control
    assert caps.navigation
