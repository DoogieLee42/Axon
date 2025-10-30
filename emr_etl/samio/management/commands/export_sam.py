from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ...services.collector import collect_claim_for_note, collect_claims
from ...services.renderer_sam import render_file


class Command(BaseCommand):
    help = "Export SAM-like files for a date range or a single clinical note."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="date_from", help="Start date (YYYY-MM-DD)")
        parser.add_argument("--to", dest="date_to", help="End date (YYYY-MM-DD)")
        parser.add_argument("--note", dest="note_id", type=int, help="Export a single ClinicalNote ID")
        parser.add_argument("--out", dest="out_path", required=True, help="Output SAM file path")

    def handle(self, *args, **opts):
        out_path = Path(opts["out_path"]).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        note_id = opts.get("note_id")
        if note_id:
            claim = collect_claim_for_note(note_id)
            if not claim:
                raise CommandError(f"ClinicalNote #{note_id} was not found.")
            content = render_file([claim])
            out_path.write_text(content, encoding="utf-8")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Exported ClinicalNote #{note_id} to {out_path}"
                )
            )
            return

        date_from = opts.get("date_from")
        date_to = opts.get("date_to")
        if not date_from or not date_to:
            raise CommandError("--from/--to or --note must be provided")

        claims = collect_claims(date_from, date_to)
        if not claims:
            self.stdout.write(self.style.WARNING("No claims were found for the given range."))
        content = render_file(claims)
        out_path.write_text(content, encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(f"Exported {len(claims)} claims to {out_path}")
        )
