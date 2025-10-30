from datetime import datetime
from pathlib import Path

from .claim_dto import Claim


def _fmt_number(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def render_claim(claim: Claim) -> str:
    head = (
        f"H|{claim.provider_id}|{claim.patient_rid}|"
        f"{claim.visit_date.isoformat()}|{claim.primary_dx}|{','.join(claim.sub_dx)}"
    )

    body_lines = []

    for line in claim.lines:
        body_lines.append(
            "|".join(
                [
                    "L",
                    line.line_type,
                    line.code,
                    _fmt_number(line.qty),
                    _fmt_number(line.days),
                    _fmt_number(line.amount),
                ]
            )
        )

    tail = f"T|{len(claim.lines)}"
    sections = [head]
    if body_lines:
        sections.append("\n".join(body_lines))
    sections.append(tail)
    return "\n".join(sections)


def render_file(claims: list[Claim]) -> str:
    return "\n---\n".join([render_claim(claim) for claim in claims])


def write_claim_to_file(claim: Claim, out_dir: str | Path) -> Path:
    """
    Helper that saves a single-claim SAM file under the given directory.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    fname = f"SAM_{claim.patient_rid}_{claim.visit_date.isoformat()}_{ts}.sam"
    path = out_dir / fname
    path.write_text(render_claim(claim), encoding="utf-8")
    return path
