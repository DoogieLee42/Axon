# clinical/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from pathlib import Path

from .models import Order
from samio.services.collector import collect_claim_for_encounter
from samio.services.renderer_sam import write_claim_to_file

@receiver(post_save, sender=Order)
def generate_sam_on_order_save(sender, instance: Order, created, **kwargs):
    """
    임상의가 처방(Order)을 저장할 때마다, 해당 Encounter 단위로 SAM 파일을 out/ 폴더에 생성.
    - 실제 운영에서는 '완료/서명' 상태일 때만 생성하도록 조건을 두는 것을 권장.
    """
    try:
        claim = collect_claim_for_encounter(instance.encounter_id)
        if not claim:
            return
        out_dir = Path(getattr(settings, "SAM_OUT_DIR", Path(settings.BASE_DIR) / "out"))
        out_path = write_claim_to_file(claim, out_dir)
        # 콘솔 로그로 경로만 남김
        print(f"[SAM] Generated: {out_path}")
    except Exception as e:
        # 조용히 삼키지 않고 콘솔에 남겨 디버깅 가능하게
        print(f"[SAM] Generation failed for encounter {instance.encounter_id}: {e}")
