"""Wisk public package.

Wisk is the public product/package name. The legacy ``wikiskill`` package remains
available temporarily for compatibility with existing consumers.
"""

from wikiskill import WikiSkill, __version__

Wisk = WikiSkill

__all__ = ["Wisk", "WikiSkill", "__version__"]
