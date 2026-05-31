"""Managed ProofSignal runtime orchestration.

This package belongs to the public Spec layer. It only verifies and invokes the
private runtime through the documented public CLI JSON contract.
"""

from .resolver import ensure_core_runtime

__all__ = ["ensure_core_runtime"]

