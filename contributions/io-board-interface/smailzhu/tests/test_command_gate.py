"""Tests for the CPU->MCU command-gate reference oracle.

The corpus in ``command_gate_vectors_v1.json`` carries hand-authored expected
outcomes (derived from the firmware rules, not from ``validate_command``). These
tests assert the oracle reproduces those outcomes, plus schema/coverage/drift
guards.
"""

import json
import pathlib
import subprocess
import sys
import unittest


SMAILZHU_DIR = pathlib.Path(__file__).resolve().parents[1]
IO_BOARD_DIR = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SMAILZHU_DIR / "tools"))

from oomwoo_command_gate import (  # noqa: E402
    GateResult,
    _MESSAGES,
    validate_command,
)

VECTORS_PATH = SMAILZHU_DIR / "conformance" / "command_gate_vectors_v1.json"
GENERATOR = SMAILZHU_DIR / "conformance" / "generate_gate_vectors.py"
CONTRACT_MANIFEST = IO_BOARD_DIR / "xbattlax" / "conformance" / "protocol_v1.json"

REASON_NAMES = {r.name for r in GateResult}


def load_vectors():
    return json.loads(VECTORS_PATH.read_text())["vectors"]


class CommandGateVectorTest(unittest.TestCase):
    def test_oracle_matches_authored_outcomes(self):
        for v in load_vectors():
            got, detail = validate_command(
                v["message_type"], v["version"], bytes.fromhex(v["payload_hex"])
            )
            ctx = f"{v['name']} -> {got.name} ({detail})"
            self.assertEqual(got.name, v["reason"], msg=ctx)
            self.assertEqual(got == GateResult.OK, v["expect"] == "OK", msg=ctx)


class CorpusSchemaTest(unittest.TestCase):
    def setUp(self):
        self.vectors = load_vectors()

    def test_schema_is_self_consistent(self):
        names = set()
        for v in self.vectors:
            for key in ("name", "message_type", "version", "payload_hex", "expect", "reason"):
                self.assertIn(key, v, msg=f"vector missing {key}: {v}")
            self.assertNotIn(v["name"], names, msg=f"duplicate name {v['name']}")
            names.add(v["name"])
            self.assertIn(v["expect"], ("OK", "REJECT"), msg=v["name"])
            self.assertIn(v["reason"], REASON_NAMES, msg=v["name"])
            # expect and reason must agree.
            self.assertEqual(v["expect"] == "OK", v["reason"] == "OK", msg=v["name"])
            bytes.fromhex(v["payload_hex"])  # must be valid hex

    def test_every_command_has_an_accepted_vector(self):
        ok_ids = {v["message_type"] for v in self.vectors if v["expect"] == "OK"}
        for name, (mid, direction, _fmt) in _MESSAGES.items():
            if direction in ("cpu_to_mcu", "both"):
                self.assertIn(mid, ok_ids, msg=f"no accepted vector for {name}")

    def test_each_reason_code_is_exercised(self):
        seen = {v["reason"] for v in self.vectors}
        for reason in ("OK", "BAD_VERSION", "UNKNOWN_TYPE", "WRONG_DIRECTION",
                       "WRONG_PAYLOAD_LENGTH", "VALUE_OUT_OF_RANGE"):
            self.assertIn(reason, seen, msg=f"no vector exercises {reason}")


class CorpusFreshnessTest(unittest.TestCase):
    def test_committed_json_is_current(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)


class ContractDriftTest(unittest.TestCase):
    """Guard: our restated message table must match the contract manifest.

    Skips when the manifest is absent (keeps this contribution self-contained).
    """

    def test_table_matches_contract_manifest(self):
        if not CONTRACT_MANIFEST.exists():
            self.skipTest(f"contract manifest not present at {CONTRACT_MANIFEST}")
        manifest = json.loads(CONTRACT_MANIFEST.read_text())
        by_name = {m["name"]: m for m in manifest["messages"]}
        # Name sets must be EQUAL, so a newly added manifest message cannot slip
        # past the oracle (and its coverage) unnoticed.
        self.assertEqual(
            set(_MESSAGES), set(by_name),
            msg="oracle table and contract manifest disagree on the message set",
        )
        for name, (mid, direction, fmt) in _MESSAGES.items():
            entry = by_name[name]
            self.assertEqual(entry["id"], mid, msg=f"{name} id")
            self.assertEqual(entry["direction"], direction, msg=f"{name} direction")
            if fmt is not None:
                # Compare the exact layout, not just its length, so a same-length
                # field reorder is still caught.
                self.assertEqual(fmt, entry.get("struct_format"), msg=f"{name} struct_format")


if __name__ == "__main__":
    unittest.main()
