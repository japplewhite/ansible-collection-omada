import os
import sys

# Running under plain pytest (not `ansible-test units`), so the
# `ansible_collections.applewhiteit.omada` namespace package used by every
# module/module_utils import isn't on sys.path automatically. Add the
# project's `ansible_collections/` root so those imports resolve.
_COLLECTIONS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _COLLECTIONS_ROOT not in sys.path:
    sys.path.insert(0, _COLLECTIONS_ROOT)
