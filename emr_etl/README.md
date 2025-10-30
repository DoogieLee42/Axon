# emr_etl — EMR 통합 ETL 도구

`emr_etl` 패키지는 별도의 샌드박스 프로젝트가 아니라, 본 EMR 코드베이스 안에서
외부 마스터 파일 적재와 SAM 청구 파일 변환을 담당하는 보조 모듈입니다.

## 제공 기능

- `import_excel` 관리 명령어: KCD/수가/약품 엑셀(xlsx/xlsb) 자료를
  `db.master_files.MasterItem` 으로 업서트합니다.
- `export_sam` 관리 명령어: 임상노트(`ClinicalNote`)와 처방(`Prescription`)을
  수집해 SAM 포맷으로 직렬화합니다.
- 프론트엔드 임상정보 화면에서 약물/처치/기타 처방을 구조화해 입력할 수 있도록
  UI가 추가되어, 저장 즉시 처방 레코드가 생성되고 SAM 변환에서도 재사용됩니다.

## 사용 예시

```bash
# 마스터 파일 적재
python manage.py import_excel --type diagnosis --file ~/KCD_202410.xlsb
python manage.py import_excel --type procedure --file ~/HIRA_PROC_202410.xlsx
python manage.py import_excel --type drug --file ~/HIRA_DRUG_202410.xlsx

# SAM 파일 내보내기
python manage.py export_sam --from 2025-10-01 --to 2025-10-31 --out ./out/claim_202510.sam
# 단일 임상노트(ID=42)만 내보내기
python manage.py export_sam --note 42 --out ./out/claim_note42.sam
```

> SAM 헤더의 요양기관기호는 `PROVIDER_ID` 환경변수(예: `.env`)로 설정할 수 있습니다.

## 디렉터리 개요

```
emr_etl/
  masterdata/   # 마스터 코드 적재 서비스 + import_excel 명령어
  samio/        # 임상데이터 → Claim DTO 수집/렌더, export_sam 명령어
  __init__.py   # 패키지 초기화 및 통합 설명
```

임상정보 화면은 `templates/medical_records/note_form.html` 과
`db/medical_records/views.py` 를 참조하세요. 여기서 작성된 처방 정보가
`db.medical_records.Prescription`으로 저장되어 SAM 내보내기와 연동됩니다.
