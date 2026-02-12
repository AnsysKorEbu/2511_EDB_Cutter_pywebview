# EDB Cutter - Claude Instructions

## Project Overview
PCB/FPCB Stackup 처리 및 EDB 파일 생성 도구

## Stackup_new Module
FPCB-Extractor 패키지 통합 모듈

### Core Components
- `extractor_integration.py` - FPCB-Extractor 통합 인터페이스
- `section_adapter.py` - 섹션 선택기 포맷 어댑터
- `__init__.py` - 모듈 초기화

### Key Features
1. **Stackup 처리**: FPCB-Extractor로 Excel 파일 처리
2. **merge_copper**: 연속된 copper 레이어 병합 기능 (기본 활성화)
3. **Section 추출**: JSON에서 섹션 데이터 자동 추출
4. **레이어 데이터 변환**: Extractor → SectionSelector 포맷 변환

### Testing
- **테스트 위치**: `test/` 폴더
- **최소 테스트**: 기능 동작 확인 후 유저에게 인계
- **테스트 원칙**: 완료 확인 후 테스트 생략 가능

### Function Signatures
```python
def process_stackup_with_extractor(
    excel_file: str,
    output_dir: Optional[str] = None,
    merge_copper: bool = True  # ⭐ 기본값 True
) -> Tuple[bool, Dict]
```

### GUI Integration
- `gui/__init__.py:668` - merge_copper=True로 호출
- 섹션 선택 UI와 통합됨

### Output Format
- JSON 파일: `{filename}_extracted.json`
- 포함 데이터: layer_data, section_data, format_type, summary

## Development Rules
1. **merge_copper는 항상 True**로 사용
2. 테스트는 `test/` 폴더에서만 수행
3. 완료 확인 시 추가 테스트 생략 가능
4. 기존 코드 패턴 유지
