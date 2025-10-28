import io
import pandas as pd
from django.db import router, transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import MasterItem, MasterUpload

# 컬럼 매핑: 파일마다 다른 한글 헤더를 표준 필드로 매핑
# 필요한 경우 여기 항목을 추가/수정하면 코드 변경 없이 대응 가능
COLUMN_ALIASES = {
    'code':  ['코드','항목코드','수가코드','약가코드','진단코드','코드값','코드번호'],
    'name':  ['명칭','항목명','품목명','성분명','산정명칭','항목명칭'],
    'price': ['금액','수가(원)','약가','단가','가격','가격(원)'],
    'unit':  ['단위','용량','회수','횟수','규격'],
    'category_hint': ['구분','분류','급여구분','항목구분'],
}

def _build_mapping(columns):
    mapping = {'code': None, 'name': None, 'price': None, 'unit': None, 'category_hint': None}
    lower = [str(c).strip().lower() for c in columns]
    for std_key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            try:
                idx = lower.index(str(alias).strip().lower())
                mapping[std_key] = columns[idx]
                break
            except ValueError:
                continue
    return mapping

def _normalize_category(user_category: str, hint_value: str|None):
    """
    사용자가 선택한 category 우선.
    hint_value(예: '행위','약제','진단','치과')가 보이면 보정.
    """
    cat = user_category or 'ACT'
    if hint_value:
        hv = str(hint_value).strip()
        if any(k in hv for k in ['약', 'Drug', 'DRG']):
            return 'DRG'
        if any(k in hv for k in ['진단', 'KCD', 'DX']):
            return 'DX'
        if any(k in hv for k in ['행위', '수가', 'Procedure']):
            return 'ACT'
    return cat

def _clean_price(v):
    if pd.isna(v):
        return None
    s = str(v).replace(',', '').strip()
    if s == '':
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def _read_file_to_iterator(fobj, ext, sheet_name=None, chunk_size=5000):
    """
    큰 파일도 버틸 수 있도록 제너레이터로 배치(df)를 yield.
    """
    if ext == 'csv':
        # pandas read_csv에 chunksize로 스트리밍
        for chunk in pd.read_csv(fobj, chunksize=chunk_size, dtype=str, keep_default_na=False):
            yield chunk
    elif ext == 'xlsx':
        # 전체를 읽되, 큰 파일은 메모리 고려 필요 → 필요시 openpyxl로 로우 스트리밍 가능
        df = pd.read_excel(fobj, dtype=str, engine='openpyxl')
        for i in range(0, len(df), chunk_size):
            yield df.iloc[i:i+chunk_size]
    elif ext == 'xlsb':
        # pyxlsb는 ExcelFile + parse가 무겁기 때문에, 빠른 전체 로딩 후 슬라이스
        df = pd.read_excel(fobj, dtype=str, engine='pyxlsb')
        for i in range(0, len(df), chunk_size):
            yield df.iloc[i:i+chunk_size]
    else:
        raise ValueError(f"Unsupported extension: {ext}")

@csrf_exempt
@require_POST
def import_master_api(request):
    """
    multipart/form-data:
      - file: 업로드 파일(.xlsx | .xlsb | .csv)
      - category: ACT | DRG | DX | ETC
    """
    f = request.FILES.get('file')
    category = request.POST.get('category', 'ACT').strip().upper()
    if not f:
        return HttpResponseBadRequest("file is required")

    filename = f.name
    ext = filename.split('.')[-1].lower()
    if ext not in ('xlsx','xlsb','csv'):
        return HttpResponseBadRequest("Only .xlsx, .xlsb, .csv are supported")

    db_alias = router.db_for_write(MasterItem)

    # 업로드 메타 기록
    up = MasterUpload.objects.using(db_alias).create(
        filename=filename,
        filetype=ext,
        total_rows=0,
        notes=''
    )

    total_inserted = 0
    total_updated  = 0
    total_rows     = 0

    try:
        # 파일 객체를 바이트로 확보(다회전 파서 대비)
        content = f.read()
        bio = io.BytesIO(content)

        # 컬럼 탐지 위해 첫 청크만 따로 읽어 컬럼 매핑 세팅
        first_iter = _read_file_to_iterator(io.BytesIO(content), ext)
        try:
            first_df = next(first_iter)
        except StopIteration:
            return HttpResponseBadRequest("Empty file")
        mapping = _build_mapping(first_df.columns)

        # 첫 청크부터 처리
        for df in [first_df] + list(first_iter):
            total_rows += len(df)
            # 표준 컬럼 추출 (없으면 None)
            code_col = mapping['code']
            name_col = mapping['name']
            price_col = mapping['price']
            unit_col = mapping['unit']
            hint_col = mapping['category_hint']

            # 행 단위 upsert (가독성/호환성 우선; 추후 bulk upsert로 최적화 가능)
            records = df.to_dict(orient='records')
            with transaction.atomic(using=db_alias):
                for r in records:
                    code = str(r.get(code_col, '')).strip() if code_col else ''
                    name = str(r.get(name_col, '')).strip() if name_col else ''
                    if not code or not name:
                        continue

                    price = _clean_price(r.get(price_col)) if price_col else None
                    unit = (str(r.get(unit_col)).strip() or None) if unit_col else None
                    cat = _normalize_category(category, r.get(hint_col) if hint_col else None)

                    raw = {k: (None if (pd.isna(v) or str(v).strip()=='' ) else str(v)) for k, v in r.items()}

                    obj, created = MasterItem.objects.update_or_create(
                        code=code, category=cat,
                        defaults={
                            'name': name,
                            'price': price,
                            'unit': unit,
                            'raw_fields': raw
                        }
                    )
                    if created: total_inserted += 1
                    else:        total_updated  += 1

        up.total_rows = total_rows
        up.notes = f"inserted={total_inserted}, updated={total_updated}"
        up.save(using=db_alias)

        return JsonResponse({
            "ok": True,
            "upload_id": up.id,
            "filename": filename,
            "filetype": ext,
            "total_rows": total_rows,
            "inserted": total_inserted,
            "updated": total_updated,
            "mapping_used": mapping
        })
    except Exception as e:
        up.notes = f"error: {e}"
        up.save(using=db_alias, update_fields=['notes'])
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
