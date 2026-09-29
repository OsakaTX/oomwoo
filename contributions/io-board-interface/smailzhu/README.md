# CPU→MCU command-gate reference oracle

A host-side, executable spec of how the STM32 I/O board's ingress gate decides
whether to **accept or reject** a CPU→MCU command frame.

The firmware fail-closes on every command: wrong wire version, unknown message
id, an MCU→CPU message sent as a command, wrong payload length, or an
out-of-range field. That gate is authoritative in firmware
(`oomwoo_cpu_ingress_validate_frame`). This contribution restates the *same
decision rules* in Python and pins them down with a language-neutral
accept/reject corpus.

## Why

- The firmware's gate rules and the written contract can drift silently.
- This corpus makes the gate decisions **explicit, versioned, and testable**.
- It is language-neutral on purpose: the firmware repo can later consume the
  same JSON so the C gate is checked against the identical cases (proposed as a
  follow-up — see below).

## What's here

| File | Purpose |
|------|---------|
| `tools/oomwoo_command_gate.py` | `validate_command(message_type, version, payload) → (GateResult, detail)` |
| `conformance/command_gate_vectors_v1.json` | accept/reject corpus, hand-authored expected outcomes |
| `conformance/generate_gate_vectors.py` | regenerates the corpus; `--check` fails if stale |
| `tests/test_command_gate.py` | asserts the oracle matches the corpus, plus schema/coverage/drift guards |

## Scope

- **Covers:** the semantic command gate — version, known type, direction,
  payload length, field-value ranges — on an already-decoded frame.
- **Does NOT cover:** wire framing, magic, or CRC. That is the `StreamDecoder`'s
  job (see `../xbattlax/`). This is a reference oracle, not the safety gate.

## Design choices

- **Decoupled.** The message table (id, direction, `struct_format`) is restated
  from the contract manifest `protocol_v1.json` (wire v1). Nothing imports
  another contributor's codec at runtime. A test drift-checks the table against
  the committed manifest, and skips if it isn't present.
- **No circular fixtures.** Expected outcomes in the JSON are authored by hand
  from the firmware rules — never computed by `validate_command`. The test then
  checks the oracle against outcomes it did not produce.
- **Raw payloads.** Illegal values (that normal encoders refuse to build) are
  expressed as raw bytes so every rejection path is representable.

## Reason codes

`OK`, `BAD_VERSION`, `UNKNOWN_TYPE`, `WRONG_DIRECTION`, `WRONG_PAYLOAD_LENGTH`,
`VALUE_OUT_OF_RANGE` — the applicable subset of the firmware's
`oomwoo_cpu_ingress_result_t`. Gate precedence matches firmware:
**version → known type → direction → payload length → field values.**

## Run

```bash
cd contributions/io-board-interface/smailzhu
python3 -m unittest discover -s tests -p 'test_*.py'
python3 conformance/generate_gate_vectors.py --check
```

## Proposed follow-up (firmware repo)

A small consumer in `makerspet/oomwoo-firmware` that runs this same JSON corpus
against `oomwoo_cpu_ingress_validate_frame` and asserts the C result matches
each vector's `reason`. That is what actually enforces cross-repo agreement;
this PR ships the oracle and corpus that make it possible.
