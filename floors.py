"""Per-side mask floor: a slow random walk that makes the sides people spin
on erode over the day (docs/04-mask.md, docs/02-quantum-open.md Q5/Q8).

Decision made here, not silently: direction comes from the discarded quantum
draw (the suggestion in Q5) — those bits are already paid for and otherwise
thrown away. Step size is 0.02 (the suggested default, also config.yaml).
Per-side, not global (Q8's suggestion) — so the record is of where the room
actually looked, not a uniform fade. Aja/Bogdan can override either choice;
noted in ROADMAP.md as an open decision made, not closed.
"""
import json
from pathlib import Path

FLOORS_PATH = Path("state/floors.json")
STEP = 0.02


def load_floors() -> dict:
    if FLOORS_PATH.exists():
        return json.loads(FLOORS_PATH.read_text())
    return {str(n): 0.0 for n in range(1, 13)}


def save_floors(floors: dict):
    FLOORS_PATH.parent.mkdir(exist_ok=True)
    FLOORS_PATH.write_text(json.dumps(floors, indent=2))


def reflect(x: float) -> float:
    """Keeps the walk off the walls. A clamped walk parks at 0 or 1 and stays
    there, which is the one state we do not want."""
    if x < 0.0:
        x = -x
    if x > 1.0:
        x = 2.0 - x
    return x


def walk_step(discarded_bits: list[int], accepted_bits: list[int], step: float = STEP) -> float:
    """Direction from the bits we already bought. Falls back to the parity
    of the accepted draw when nothing was discarded (draw accepted first try)."""
    src = discarded_bits if discarded_bits else accepted_bits
    up = sum(src) * 2 > len(src)
    return step if up else -step


def step_floor(face: int, direction: float) -> float:
    floors = load_floors()
    floors[str(face)] = reflect(floors[str(face)] + direction)
    save_floors(floors)
    return floors[str(face)]


def get_floor(face: int) -> float:
    return load_floors().get(str(face), 0.0)
