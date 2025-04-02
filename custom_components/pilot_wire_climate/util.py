from .const import VALUES_MAPPING


def get_value_key(input_value: str) -> str:
    """
    Returns the key corresponding to the given input_value
    in the VALUES_MAPPING dictionary by directly comparing
    the value without normalization.
    """
    for key, alternatives in VALUES_MAPPING.items():
        if input_value in alternatives:
            return key
    return None
