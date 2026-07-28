# Side Brush Channel Refinement

Status: proposal. Resolves `HW-SW-005` (side brush quantity ambiguity) and updates
the serial contract from a single side-brush field to dual-channel control.

## Background

The [oomwoo-io-board SPEC.md GPIO list](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
shows **two independent PWM outputs**:

| SPEC # | Signal | Purpose |
|--------|--------|---------|
| 39 | Side brush motor **right** PWM | Drives right side brush |
| 40 | Side brush motor **left** PWM | Drives left side brush |

And **two independent current sense inputs**:

| SPEC # | Signal | Purpose |
|--------|--------|---------|
| 28 | Side brush left front motor sense | Overcurrent / stall detection |
| 29 | Side brush right front motor sense | Overcurrent / stall detection |

The current draft `CLEANING_MOTORS_SET` payload (0x0102) has only one `side_brush_pct`
field, which cannot address two independently driven brushes.

## Proposed payload change

### Current (0x0102)

```
offset  size  field
0       1     main_brush_pct   (0-100)
1       1     side_brush_pct   (0-100)
2       1     fan_pct          (0-100)
3       1     pump_pct         (0-100)
Total: 4 bytes
```

### Proposed (0x0102, v2)

```
offset  size  field
0       1     main_brush_pct          (0-100)
1       1     side_brush_left_pct     (0-100)
2       1     side_brush_right_pct    (0-100)
3       1     fan_pct                 (0-100)
4       1     pump_pct                (0-100)
Total: 5 bytes
```

### Migration strategy

The protocol `version` field in the frame header already allows negotiating the
payload format. The sequence is:

1. The MCU reports its protocol version in `MCU_HELLO` (0x8000).
2. The bridge detects version ≥ 2 and sends the 5-byte payload.
3. Version-1 MCU firmware receives a 5-byte payload with `payload_len=5` and either
   rejects with NACK or ignores byte[4]. The bridge falls back to sending the 4-byte
   format, mapping `side_brush_left_pct` to `side_brush_pct` and setting
   `side_brush_right_pct` to 0.

### ROS2 topic mapping

| ROS2 topic | Existing | Change |
|-----------|----------|--------|
| `/oomwoo/cleaning/side_brush_pct` | UInt8 | Split into `side_brush_left_pct` + `side_brush_right_pct` (two UInt8 topics, or a combined message) |

Option A (simple): Publish two separate UInt8 topics:
- `/oomwoo/cleaning/side_brush_left_pct`
- `/oomwoo/cleaning/side_brush_right_pct`

Option B (cleaner): Define a placeholder combined message in the future `oomwoo_msgs`
package:
```
uint8 side_brush_left_pct
uint8 side_brush_right_pct
```

Recommendation: start with Option A for MVP. The topics are boring, discoverable,
and trivially testable. Migrate to Option B when custom messages are worth freezing.

### Impact on the reference codec

The `pack_cleaning_motors()` function in `tools/oomwoo_mcu_frame.py` needs to change
signature:

```python
# Current
def pack_cleaning_motors(
    main_brush_pct: int,
    side_brush_pct: int,
    fan_pct: int,
    pump_pct: int = 0,
) -> bytes:

# Proposed (dual-channel)
def pack_cleaning_motors(
    main_brush_pct: int,
    side_brush_left_pct: int,
    side_brush_right_pct: int,
    fan_pct: int,
    pump_pct: int = 0,
    *,
    version: int = 2,
) -> bytes:
```

For backward-compatible testing, the function can accept an optional `version`
parameter: version=1 emits the old 4-byte format, version=2 emits the new 5-byte
format.

### Safety impact

Both side brush channels remain under MCU safety authority. The `SAFETY_EVENT`
"BRUSH_OVERCURRENT" should carry a `detail` byte indicating which brush channel
tripped:

| `detail` | Meaning |
|----------|---------|
| 0 | Main brush |
| 1 | Side brush left |
| 2 | Side brush right |
| 3 | Fan |

This way a `SAFETY_EVENT(event=7, active=1, detail=1)` means "side brush left
overcurrent, stop that channel only."

## Decision needed

| Question | Proposed answer |
|----------|----------------|
| Does v1 have one physical side brush or two? | SPEC GPIO list shows two PWM channels (GPIO 39, 40), confirming two independently driven side brushes for v1. |
| Should the payload grow immediately? | Yes, before firmware is written against the v1 format. Adding a byte now is free; retrofitting it later breaks the contract. |
