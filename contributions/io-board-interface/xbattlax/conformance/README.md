# CPU/MCU Protocol Conformance Kit

This directory turns the protocol-v1 message catalog into reusable test data for
the Python reference, MCU firmware, and ROS2 bridge implementations.

| File | Purpose |
|---|---|
| `protocol_v1.json` | Machine-readable message IDs, payload status, layouts, and sample values. |
| `golden_vectors_v1.json` | Generated language-neutral payload and complete-frame vectors. |
| `golden_vectors_v1.h` | Git-ignored build output containing the same vectors for C11/C++17 tests. |
| `generate_vectors.py` | Regenerates both outputs through the Python reference encoder. |
| `verify_vectors.c` | Validates every generated frame, payload, header field, and CRC; compiles as C11 and C++17. |

`POWER_TELEMETRY` and `MCU_DIAGNOSTIC` remain in the manifest with
`payload_status: open`. A message must have either generated vectors or a written
reason why its payload is not frozen; silently omitting a message fails the Python
coverage test.

Generate the C header or check the committed language-neutral output:

```bash
python3 contributions/io-board-interface/xbattlax/conformance/generate_vectors.py
python3 contributions/io-board-interface/xbattlax/conformance/generate_vectors.py --check
```

Compile the language consumers:

```bash
cc -std=c11 -Wall -Wextra -Werror -pedantic \
  contributions/io-board-interface/xbattlax/conformance/verify_vectors.c \
  -o /tmp/oomwoo-vectors-c
c++ -x c++ -std=c++17 -Wall -Wextra -Werror -pedantic \
  contributions/io-board-interface/xbattlax/conformance/verify_vectors.c \
  -o /tmp/oomwoo-vectors-cpp
/tmp/oomwoo-vectors-c
/tmp/oomwoo-vectors-cpp
```

Firmware and bridge repositories should consume `golden_vectors_v1.json` or the
generated header in their own CI. This kit validates the contract representation;
it does not replace implementation-specific decoder, timeout, or hardware tests.
