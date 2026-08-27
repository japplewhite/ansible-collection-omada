"""Standard AnsibleModule test harness (set_module_args / exit_json / fail_json capture).

This is the conventional pattern used across Ansible collections to unit-test
modules without going through the real CLI argument parsing or process exit.
"""
import json

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


def set_module_args(args):
    """Serialize module args as if passed on the CLI."""
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)
    # ansible-core >= 2.19 requires a serialization profile alongside the args.
    basic._ANSIBLE_PROFILE = "legacy"


class AnsibleExitJson(Exception):
    """Raised in place of AnsibleModule.exit_json to stop execution and capture output."""


class AnsibleFailJson(Exception):
    """Raised in place of AnsibleModule.fail_json to stop execution and capture output."""


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs.setdefault("failed", True)
    raise AnsibleFailJson(kwargs)
