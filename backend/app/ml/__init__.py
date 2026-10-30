"""ML engine package for threat classification."""

# Canonical feature schema shared by training and inference.
FEATURE_COLUMNS = [
    "duration",
    "packet_count",
    "bytes_sent",
    "bytes_recv",
    "bytes_total",
    "bytes_per_packet",
    "bytes_ratio",
    "src_port",
    "dst_port",
    "protocol_encoded",
    "is_icmp",
    "packets_per_second",
    "bytes_per_second",
]

# ML target classes (must match ThreatType constants).
CLASS_LABELS = ["normal", "port_scan", "brute_force", "ddos", "abnormal"]

# Map a numeric label index back to a string.
LABEL_TO_STR = {i: name for i, name in enumerate(CLASS_LABELS)}
STR_TO_LABEL = {name: i for i, name in enumerate(CLASS_LABELS)}