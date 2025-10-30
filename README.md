# EMR Repository Structure

이 프로젝트는 전자의무기록(EMR) 시스템을 구성하기 위한 Django 기반 코드베이스입니다. 데이터베이스 자산을 직관적으로 파악할 수 있도록 구조를 재정비하여, 환자 정보 · 의무기록 · 마스터파일 정보를 각각 독립된 저장소에 배치했습니다.

## 상위 디렉터리 개요

```
emr_cert_rx2/
├─ db/                     # 모든 데이터 계층을 한 곳에 모은 패키지
│  ├─ patients/            # 환자 인적사항 및 검색 로직
│  ├─ medical_records/     # 임상노트, 처방 등 의무기록 데이터
│  └─ master_files/        # 수가/약제/진단 마스터 관리
├─ emr_cert/               # 메인 Django 프로젝트 설정/URL 등
├─ templates/              # 앱 단위 템플릿 (예: patients, medical_records)
├─ masterfile_migration/   # 마스터 파일 변환용 별도 도구(선택 사용)
├─ manage.py               # 메인 프로젝트 진입점
└─ requirements.txt
```

## 데이터베이스 분리 설계

`emr_cert/settings.py` 에서는 운영 데이터와 마스터 데이터를 분리하기 위해 2개의 SQLite 파일을 정의합니다.

| Alias | File | 용도 |
| --- | --- | --- |
| `default` | `db/clinical.sqlite3` | 인증·세션을 포함한 모든 임상/운영 데이터 |
| `master_files` | `db/master_files.sqlite3` | 표준 코드/마스터 데이터 |

`db/routers.py` 에 선언된 라우터가 각 앱의 모델을 전용 DB로 자동 라우팅하며, 마이그레이션도 해당 파일에만 적용됩니다. 환자·의무기록·인증/세션 등 운영 데이터는 모두 `db/clinical.sqlite3` 에 저장되므로 교차-DB 외래키가 발생하지 않습니다.

```bash
# 필수 기본 마이그레이션
python manage.py migrate
# 마스터파일 DB 초기화 (필요 시)
python manage.py migrate master_files --database=master_files
```

## 앱 구성 요약

- `db.patients`  
  - 모델: 환자 기본정보, 검증 로직(`errors.py`) 포함  
  - 장고 Admin: 환자 레코드 관리

- `db.medical_records`  
  - 모델: 임상노트, 처방, 활력징후 등  
  - 뷰: 처방 검색(`orders/`), 임상 노트 작성(`clinical-notes/new/`)  
  - 템플릿: `templates/medical_records`

- `db.master_files`  
  - 모델: 마스터 업로드 이력, 표준 코드 엔트리  
  - API & UI: `/master/upload/` 화면에서 업로드 → `/master/import/` API로 처리  
  - 마이그레이션/어드민 구성 포함

## 프론트엔드 진입점

- 환자 검색: `/patients/search/`
- 임상 노트 작성: `/clinical-notes/new/`
- 의무기록 처방 조회: `/orders/`
- 마스터 파일 업로드/마이그레이션: `/master/upload/`

## REST API

마스터 파일 자원은 RESTful 엔드포인트로도 접근할 수 있습니다. 모든 응답은 JSON 형식이며, 인증·권한 레이어는 기존 Django 설정(세션/토큰 등)에 맞춰 추가하면 됩니다.

- `GET /api/master/items/` : 마스터 항목 목록 조회 (`category`, `search`, `page`, `page_size` 지원)
- `POST /api/master/items/` : 단일 마스터 항목 생성 (body 예시: `{"code":"AA001","name":"수술","category":"ACT"}`)
- `GET /api/master/items/<id>/` : 개별 항목 상세 조회
- `PATCH /api/master/items/<id>/` : 항목 부분 수정 (허용 필드: `code`, `name`, `category`, `price`, `unit`, `raw_fields`)
- `DELETE /api/master/items/<id>/` : 항목 삭제
- `GET /api/master/uploads/` : 업로드 이력 조회 (`limit` 파라미터 지원)
- `POST /api/master/uploads/` : 파일 업로드 및 import 실행 (`multipart/form-data`로 `file`, `category` 전송)
- `GET /api/master/uploads/<id>/` : 특정 업로드 이력 상세 조회

기존 `/master/import/` 경로는 업로드 화면 호환을 위해 유지되지만, 신규 기능 개발 시 `/api/master/…` 경로 사용을 권장합니다.

위 URL은 모두 `django.contrib.auth` 로그인 이후 접근하는 것을 전제로 하고 있습니다.

필요 시 `DATABASES` 항목에서 각 파일 경로를 다른 RDBMS로 교체할 수 있으며, 라우터 설정만 유지하면 동일하게 동작합니다.

## 관리자 화면 개요

- `/admin/` : 환자 등록, 등록 환자 목록 두 가지 액션만 노출
- 환자 목록에서 등록번호를 누르면 환자 요약/처방/임상/외부정보/등록번호 이력을 한 화면에서 확인
- `새 등록번호 발급` 버튼으로 동일 환자에게 새 등록번호를 부여하고 과거 이력은 목록으로 보존
- 기본 정보 수정 폼은 하단 접기 영역에 배치되어 필요할 때만 펼칠 수 있습니다.

### 환자 상세 대시보드 기능

- 처방, 임상 노트, 진단, 약물 알레르기, 활력징후, 신체계측, 외부 문서를 관리자 화면에서 바로 등록·수정·조회할 수 있도록 각 섹션별 폼을 제공
- KCD 진단 코드는 마스터 데이터(진단 마스터) 목록에서 검색 후 클릭하여 바로 기록할 수 있는 UI를 지원
- 처방 내역은 진료 일자와 약물명을 기준으로 그룹화되어 빠르게 확인할 수 있습니다.

### 환자 상세 대시보드 기능
- 처방, 진단, 알레르기, 외부 문서를 관리자 화면에서 바로 등록/수정/조회할 수 있도록 폼을 제공
- KCD 진단 코드는 마스터 데이터 목록에서 검색해 선택 후 바로 기록 가능
- 처방 내역은 진료일자와 약물명 기준으로 그룹화되어 빠르게 확인 가능합니다.
