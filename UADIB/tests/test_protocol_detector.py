from core.models import ProtocolType
from core.protocol_detector import ProtocolDetector


def test_detect_mavlink_prefix() -> None:
    d = ProtocolDetector()
    endpoint = d.detect("mavlink://udp:127.0.0.1:14550")
    assert endpoint.protocol == ProtocolType.MAVLINK
    assert endpoint.confidence >= 0.9


def test_detect_ros2_prefix() -> None:
    d = ProtocolDetector()
    endpoint = d.detect("ros2://topic/drone")
    assert endpoint.protocol == ProtocolType.ROS2
