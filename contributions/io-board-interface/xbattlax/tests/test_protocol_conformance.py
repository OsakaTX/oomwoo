import json
import pathlib
import subprocess
import sys
import unittest


CONTRIBUTION_DIR = pathlib.Path(__file__).resolve().parents[1]
CONFORMANCE_DIR = CONTRIBUTION_DIR / "conformance"
TOOLS_DIR = CONTRIBUTION_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from oomwoo_mcu_frame import (  # noqa: E402
    FrameDecodeError,
    MessageType,
    StreamDecoder,
    decode_frame,
)


class ProtocolConformanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (CONFORMANCE_DIR / "protocol_v1.json").read_text(encoding="utf-8")
        )
        cls.golden = json.loads(
            (CONFORMANCE_DIR / "golden_vectors_v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_generated_outputs_are_current(self):
        subprocess.run(
            [sys.executable, str(CONFORMANCE_DIR / "generate_vectors.py"), "--check"],
            check=True,
        )

    def test_manifest_covers_every_message_id(self):
        manifest_ids = {
            message["name"]: message["id"] for message in self.manifest["messages"]
        }
        enum_ids = {message.name: int(message) for message in MessageType}
        self.assertEqual(manifest_ids, enum_ids)

        for message in self.manifest["messages"]:
            if message["payload_status"] == "defined":
                self.assertIn("struct_format", message)
                self.assertTrue(message["samples"])
            else:
                self.assertEqual(message["payload_status"], "open")
                self.assertTrue(message["open_reason"])

    def test_every_vector_round_trips_and_survives_byte_fragmentation(self):
        for vector in self.golden["vectors"]:
            with self.subTest(vector=vector["name"]):
                raw = bytes.fromhex(vector["frame_hex"])
                payload = bytes.fromhex(vector["payload_hex"])
                frame = decode_frame(raw)
                self.assertEqual(frame.message_type, vector["message_type"])
                self.assertEqual(frame.sequence, vector["sequence"])
                self.assertEqual(frame.flags, vector["flags"])
                self.assertEqual(frame.payload, payload)

                decoder = StreamDecoder()
                decoded = []
                for byte in raw:
                    decoded.extend(decoder.feed(bytes([byte])))
                self.assertEqual(decoded, [frame])

    def test_every_vector_rejects_crc_corruption(self):
        for vector in self.golden["vectors"]:
            with self.subTest(vector=vector["name"]):
                raw = bytearray.fromhex(vector["frame_hex"])
                raw[-1] ^= 0x01
                with self.assertRaises(FrameDecodeError):
                    decode_frame(bytes(raw))

    def test_safety_event_vectors_cover_all_current_codes(self):
        event_codes = {
            bytes.fromhex(vector["payload_hex"])[0]
            for vector in self.golden["vectors"]
            if vector["message_name"] == "SAFETY_EVENT"
        }
        self.assertEqual(event_codes, set(range(1, 11)))

    def test_open_payloads_are_explicit_in_generated_output(self):
        open_names = {message["name"] for message in self.golden["open_messages"]}
        self.assertEqual(open_names, {"POWER_TELEMETRY", "MCU_DIAGNOSTIC"})


if __name__ == "__main__":
    unittest.main()
