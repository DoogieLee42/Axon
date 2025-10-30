"""
The legacy ETL demo exposed standalone models in the Django admin. In the
integrated setup those models are provided by `db.master_files`, which already
registers its admin views. This module remains so Django's autodiscovery does
not fail, but it intentionally performs no registrations.
"""
