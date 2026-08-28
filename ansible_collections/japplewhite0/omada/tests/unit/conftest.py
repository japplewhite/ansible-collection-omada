import os
import sys

# Running under plain pytest (not `ansible-test units`), so the
# `ansible_collections.japplewhite0.omada` namespace package used by every
# module/module_utils import isn't on sys.path automatically. Add the
# project's `ansible_collections/` root so those imports resolve.
# Needs the *parent* of ansible_collections/ on sys.path, not that directory
# itself - `import ansible_collections...` resolves relative to its parent.
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
