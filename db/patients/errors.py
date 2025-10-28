from dataclasses import dataclass
@dataclass(frozen=True)
class ErrorCode:
    code:str
    message:str
ERR_INVALID_RRN=ErrorCode('PAT001','잘못된 주민등록번호 형식')
ERR_DUPLICATE_RRN=ErrorCode('PAT002','이미 등록된 주민등록번호')
