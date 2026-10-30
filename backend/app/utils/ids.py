import uuid


def generate_id(prefix: str = "") -> str:
    """
    Generates a unique identifier with an optional semantic prefix.
    Example: generate_id("elec") -> "elec_4f7e1b9a2c3d4e5f"
    """
    uid = uuid.uuid4().hex[:16]
    return f"{prefix}_{uid}" if prefix else uid
