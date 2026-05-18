"""Deep-merge helper for customization config patching."""

from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge patch into base.

    Rules:
    - dict + dict: recurse key by key (patch wins on conflict).
    - Any other value in patch (incl. lists): replaces the value in base.
    - None in patch keeps the value (use a sentinel or pop the key out
      of patch beforehand if you want a key removed).

    Base and patch are not mutated. A new dict is returned.
    """
    result = deepcopy(base)
    for key, patch_value in patch.items():
        base_value = result.get(key)
        if isinstance(base_value, dict) and isinstance(patch_value, dict):
            result[key] = deep_merge(base_value, patch_value)
        else:
            result[key] = deepcopy(patch_value)
    return result
