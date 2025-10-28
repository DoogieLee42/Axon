class BaseDBRouter:
    """Common helpers for routing app models to dedicated databases."""
    app_labels=set()
    db_name=None

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.app_labels:
            return self.db_name
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.app_labels:
            return self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in self.app_labels or obj2._meta.app_label in self.app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.app_labels:
            return db == self.db_name
        return None


class ClinicalDBRouter(BaseDBRouter):
    app_labels={'patients','medical_records'}
    db_name='default'


class MasterFileDBRouter(BaseDBRouter):
    app_labels={'master_files'}
    db_name='master_files'
