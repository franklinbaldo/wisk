"""Wisk compatibility runtime built on OKF.

The public product/package name is ``wisk``. ``wikiskill`` remains importable
for compatibility with existing consumers during the rename transition.
"""

from wikiskill.live_run import LiveRunWikiSkill as WikiSkill

Wisk = WikiSkill

__version__ = "0.3.0"
__all__ = ["Wisk", "WikiSkill", "__version__"]
