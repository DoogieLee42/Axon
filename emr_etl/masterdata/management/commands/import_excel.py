from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import router, transaction

from db.master_files.models import MasterItem, MasterUpload

from ...services.excel_loader import (
    map_diagnosis,
    map_drug,
    map_procedure,
    map_procedure_hira_2025,
    read_excel,
)

CATEGORY_BY_KIND = {
    "diagnosis": "DX",
    "procedure": "ACT",
    "drug": "DRG",
}


class Command(BaseCommand):
    """
    Excel/xlsb 파일을 읽어 `db.master_files.MasterItem` 테이블을 갱신합니다.

    사용 예:
      python manage.py import_excel --type diagnosis --file ~/KCD_202410.xlsb
      python manage.py import_excel --type procedure --file "C:\\path\\HIRA_PROC_2025.xlsx"
      python manage.py import_excel --type drug --file ~/HIRA_DRUG_2025.xlsx
    """

    help = "Import master codes from Excel/xlsb into the master_files database."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to Excel/xlsb file")
        parser.add_argument(
            "--type",
            required=True,
            choices=sorted(CATEGORY_BY_KIND.keys()),
            help="Type of master data to import",
        )
        parser.add_argument(
            "--sheet", default=0, help="Sheet name or index (default: 0)"
        )

    def handle(self, *args, **opts):
        file_path = Path(opts["file"]).expanduser()
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        kind = opts["type"]
        category = CATEGORY_BY_KIND[kind]

        sheet_arg = opts["sheet"]
        try:
            sheet = int(sheet_arg)
        except (TypeError, ValueError):
            sheet = sheet_arg

        df = read_excel(str(file_path), sheet)

        if kind == "diagnosis":
            rows = map_diagnosis(df)
        elif kind == "procedure":
            if "HIRA_PROC" in file_path.name.upper() or "수가코드" in df.columns:
                rows = map_procedure_hira_2025(df)
            else:
                rows = map_procedure(df)
        elif kind == "drug":
            rows = map_drug(df)
        else:
            raise CommandError(f"Unsupported type: {kind}")

        if not rows:
            self.stdout.write(self.style.WARNING("No rows were detected in the file."))
            return

        db_alias = router.db_for_write(MasterItem)
        inserted = updated = 0
        upload = None

        with transaction.atomic(using=db_alias):
            upload = MasterUpload.objects.using(db_alias).create(
                filename=file_path.name,
                filetype=file_path.suffix.lstrip(".").lower() or "xlsx",
                total_rows=0,
                notes="",
            )

            master_model = MasterItem.objects.using(db_alias)

            for row in rows:
                row_category = category
                raw_fields = dict(row.raw_fields)
                raw_fields.setdefault("_source_file", file_path.name)
                raw_fields.setdefault("_source_type", kind)

                defaults = {
                    "name": row.name,
                    "price": row.price,
                    "unit": row.unit,
                    "raw_fields": raw_fields,
                }
                _, created = master_model.update_or_create(
                    code=row.code,
                    category=row_category,
                    defaults=defaults,
                )
                if created:
                    inserted += 1
                else:
                    updated += 1

            upload.total_rows = len(rows)
            upload.notes = f"inserted={inserted}, updated={updated}"
            upload.save(update_fields=["total_rows", "notes"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(rows)} rows for '{kind}' "
                f"(inserted={inserted}, updated={updated}) from {file_path}"
            )
        )
