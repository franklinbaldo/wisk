"""Wisk compatibility runtime built on OKF.

The public product/package name is ``wisk``. ``wisk`` remains importable
for compatibility with existing consumers during the rename transition.
"""

from wisk.live_run import LiveRunWisk as Wisk

Wisk = Wisk

__version__ = "0.3.2"
__all__ = ["Wisk", "Wisk", "__version__"]
