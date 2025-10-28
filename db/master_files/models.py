
from django.db import models
from django.utils import timezone

class MasterUpload(models.Model):
    """
    원본 마스터 파일 업로드 이력 + 메타데이터 추적용
    """
    FILE_TYPES = [
        ('xlsx', 'XLSX'),
        ('xlsb', 'XLSB'),
        ('csv',  'CSV'),
    ]
    id = models.BigAutoField(primary_key=True)
    filename = models.CharField(max_length=255)
    filetype = models.CharField(max_length=10, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(default=timezone.now)
    total_rows = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.filename} ({self.filetype}) @ {self.uploaded_at:%Y-%m-%d %H:%M}"


class MasterItem(models.Model):
    """
    수가/약제/진단 등 마스터 공통 스키마 (최소 필드)
    - 필수 표준 필드 5개 + 유연성을 위한 raw_fields
    """
    CATEGORY_CHOICES = [
        ('ACT', '행위'),      # procedure/수가
        ('DRG', '약제'),      # drug
        ('DX',  '진단'),      # diagnosis
        ('ETC', '기타'),
    ]

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=64, db_index=True)       # 수가코드/약제코드/진단코드 등
    name = models.CharField(max_length=255)                     # 명칭
    category = models.CharField(max_length=8, choices=CATEGORY_CHOICES, default='ACT')
    price = models.IntegerField(null=True, blank=True)          # 단가(원)
    unit = models.CharField(max_length=64, null=True, blank=True) # 단위/용량/회수 등

    # 원본 컬럼 전체를 보존(유연성 & 회귀추적)
    raw_fields = models.JSONField(default=dict, blank=True)

    # 중복 방지를 위한 고유키 제약 (code + category)
    class Meta:
        unique_together = ('code', 'category')

    def __str__(self):
        return f"[{self.category}] {self.code} - {self.name}"
