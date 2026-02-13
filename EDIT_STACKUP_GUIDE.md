# Edit Stackup 기능 사용 가이드

## 개요

EDB Cutter에 **Edit Stackup** 기능이 추가되었습니다. 이 기능을 통해 stackup_extractor로 추출한 데이터를 GUI에서 편집하고, 편집된 결과를 자동으로 Section Selection에 로드할 수 있습니다.

---

## 주요 기능

1. **Excel 파일 편집**: stackup_extractor의 내장 GUI를 활용하여 Excel 데이터 편집
2. **테이블 뷰**: Layer Data와 Section Data를 Excel과 유사한 테이블로 표시
3. **셀 단위 편집**: 더블클릭으로 Dk, Df, Thickness 등의 값 수정
4. **자동 JSON 생성**: 편집 완료 시 `{filename}_edited.json` 파일 자동 생성
5. **자동 로드**: 편집된 JSON이 Section Selection에 자동으로 로드됨

---

## 사용 방법

### 1. Edit 버튼 클릭

1. EDB Cutter GUI 실행: `python gui/initial_gui.py`
2. **Cut Executor** 탭으로 이동
3. **Excel File** 섹션에서 **✏️ Edit** 버튼 클릭

### 2. Excel 파일 선택

- File Dialog가 열리면 편집할 Excel 파일 선택 (.xlsx 또는 .xls)
- stackup_extractor GUI가 자동으로 실행됩니다

### 3. Stackup Editor GUI 사용

#### GUI 구조
- **상단**: Excel 파일 경로 표시
- **Extract 버튼**: Excel 파일 처리 (자동 실행됨)
- **Merge COPPER_PLATE 체크박스**: 연속된 copper 레이어 병합 옵션
- **3개 탭**:
  1. **Layer Data**: 레이어 정보 텍스트 뷰
  2. **Section Data**: 섹션별 정보 텍스트 뷰
  3. **Table View**: 편집 가능한 테이블 뷰 ⭐

#### 데이터 편집

**Table View 탭**에서:
1. 테이블의 셀을 **더블클릭**하여 편집 모드 진입
2. 값 수정 (예: Dk, Df, Thickness 등)
3. Enter 키로 확인

**편집 가능한 필드**:
- `material`: 재료 이름 (COPPER, PREPREG, POLYIMIDE 등)
- `dk`: 유전 상수 (Dielectric Constant)
- `df`: 손실 계수 (Dissipation Factor)
- `reference_thickness`: 참조 두께 (μm)
- Section별 `thickness`: 각 섹션의 실제 두께

### 4. JSON Export

1. **Export to Excel** 체크박스:
   - 체크: JSON과 함께 Excel 파일도 생성
   - 미체크: JSON만 생성 (권장)

2. **Complete 버튼** 클릭:
   - 편집된 데이터를 JSON으로 저장
   - 파일명: `{원본파일명}_edited.json`
   - 위치: Excel 파일과 동일한 폴더

3. **Cancel 버튼** 클릭:
   - 편집 취소
   - 변경사항 저장 안 함

### 5. 자동 로드 확인

- Complete 후 GUI가 닫히면 EDB Cutter로 자동 복귀
- 편집된 JSON의 섹션 정보가 자동으로 로드됨
- **Excel File Path** 표시가 `{파일명} (edited)`로 변경됨
- **📊 Section Selection** 버튼이 활성화됨

### 6. Section Selection 진행

1. **📊 Section Selection** 버튼 클릭
2. Cut-Section 매핑 수행
3. Save 버튼 클릭 → `.sss` 파일 생성
4. Cut Executor에서 EDB 생성

---

## 구현 세부사항

### 파일 구조

```
gui/
├── __init__.py
│   ├── edit_stackup_with_editor()      # 새로 추가된 API 메서드
│   └── get_sections_from_json()        # 새로 추가된 helper 메서드
├── index.html
│   └── "✏️ Edit" 버튼 추가 (line ~182)
└── sectionSelector.js
    └── editStackupWithEditor()         # 새로 추가된 JavaScript 함수

stackup/
└── extractor_integration.py
    └── extract_sections_from_json()    # 기존 함수 (재사용)
```

### API 메서드

#### `edit_stackup_with_editor(excel_file=None)`

**Parameters**:
- `excel_file` (optional): Excel 파일 경로. 없으면 file dialog 표시

**Returns**:
```python
{
    'success': bool,
    'excel_file': str,      # Excel 파일 경로
    'output_file': str,     # 생성된 JSON 파일 경로 ({filename}_edited.json)
    'error': str            # 실패 시 에러 메시지
}
```

**동작**:
1. Excel 파일 선택 (dialog 또는 인자)
2. `stackup_extractor.editor.edit_and_export()` 호출
3. tkinter GUI 실행 (blocking)
4. 사용자가 Complete/Cancel 선택
5. 결과 반환

#### `get_sections_from_json(json_file)`

**Parameters**:
- `json_file`: JSON 파일 경로 (`_extracted.json` 또는 `_edited.json`)

**Returns**:
```python
{
    'success': bool,
    'sections': list,       # 섹션 이름 리스트 ['Module', 'Cavity', ...]
    'error': str            # 실패 시 에러 메시지
}
```

### JavaScript 함수

#### `editStackupWithEditor()`

**동작 흐름**:
1. `window.pywebview.api.edit_stackup_with_editor()` 호출
2. 성공 시 `get_sections_from_json()` 호출
3. 섹션 데이터를 `sectionSelector` 객체에 저장
4. UI 업데이트 (파일 경로, Section Selection 버튼 활성화)
5. 성공 메시지 표시

### 출력 파일

#### JSON 파일 구조 (`{filename}_edited.json`)

```json
{
  "format_type": "type1",
  "layer_data": [
    {
      "layer": 1,
      "material": "COPPER",
      "dk": 3.5,
      "df": 0.05,
      "reference_thickness": 31.2,
      "row": 13
    },
    ...
  ],
  "section_data": {
    "Module_8": {
      "name": "Module",
      "column": 8,
      "layers": [
        {
          "layer": 1,
          "material": "PSR",
          "thickness": 26,
          "dk": 4,
          "df": 0.02,
          "row": 4
        },
        ...
      ]
    },
    ...
  },
  "summary": {
    "layer_count": 13,
    "section_count": 8,
    "center_row": 12
  }
}
```

---

## 에러 처리

### 일반적인 에러

1. **"stackup_extractor.editor not available"**
   - **원인**: stackup_extractor 패키지가 설치되지 않았거나 버전이 낮음
   - **해결**: `pip install --upgrade stackup_extractor`

2. **"Edit cancelled by user"**
   - **원인**: 사용자가 Cancel 버튼 클릭
   - **처리**: 정상 동작, 변경사항 없음

3. **"File selection canceled"**
   - **원인**: File dialog에서 취소 선택
   - **처리**: 정상 동작

4. **"No sections found in the edited JSON file"**
   - **원인**: JSON에 유효한 섹션 데이터 없음
   - **해결**: Excel 파일 포맷 확인 (TYPE0-TYPE4 지원)

### 디버깅

로그 확인:
```python
# gui/__init__.py의 logger 출력 확인
logger.info("Launching stackup editor GUI")
logger.info(f"Edit completed successfully: {output_json}")
```

---

## 워크플로우 예시

### Case 1: 새로운 Excel 파일 편집

```
1. ✏️ Edit 버튼 클릭
2. Case1.xlsx 선택
3. Editor GUI에서 Layer 2의 Dk 값을  3.5 → 4.0으로 수정
4. Complete 버튼 클릭
5. Case1_edited.json 생성됨
6. 4개 섹션 자동 로드: [Module, Cavity, Flex, Connector]
7. 📊 Section Selection 버튼 활성화
8. Cut-Section 매핑 후 .sss 파일 저장
```

### Case 2: 기존 _extracted.json 재편집

```
1. ✏️ Edit 버튼 클릭
2. Case1.xlsx 선택 (이미 _extracted.json 존재)
3. Editor GUI에서 기존 데이터 표시됨
4. Thickness 값 수정
5. Complete → Case1_edited.json 생성
6. 새로운 JSON으로 섹션 로드
```

---

## 기술 스택

- **GUI Framework**: tkinter (stackup_extractor 내장)
- **Integration**: pywebview API + JavaScript
- **Data Format**: JSON (FPCB-Extractor 표준 포맷)
- **File Handling**: pathlib + json

---

## 제한사항

1. **tkinter 의존성**: stackup_extractor.editor는 tkinter 기반이므로 GUI 환경 필요
2. **Blocking 동작**: 편집 중에는 메인 GUI 응답 불가 (별도 창이므로 괜찮음)
3. **Excel 포맷**: TYPE0-TYPE4만 지원 (stackup_extractor 제약)
4. **XLS 파일**: 자동으로 XLSX로 변환 시도 (실패 시 수동 변환 필요)

---

## 향후 개선 가능성

1. **Undo/Redo**: 편집 히스토리 관리
2. **실시간 검증**: 편집 중 EDB conductor count와 비교
3. **Template 저장**: 자주 사용하는 설정 저장/로드
4. **Batch 편집**: 여러 파일 동시 편집

---

## 문제 해결

### Q: Edit 버튼을 눌렀는데 아무 반응이 없어요

**A**:
1. 콘솔 로그 확인
2. stackup_extractor 설치 여부 확인: `pip list | grep stackup`
3. tkinter 설치 여부 확인: `python -m tkinter`

### Q: Complete를 눌렀는데 JSON 파일이 생성되지 않아요

**A**:
1. 파일 쓰기 권한 확인
2. 디스크 용량 확인
3. 로그에서 에러 메시지 확인

### Q: Section Selection에서 섹션이 표시되지 않아요

**A**:
1. JSON 파일이 정상적으로 생성되었는지 확인
2. `get_sections_from_json()` 로그 확인
3. JSON 파일 내부의 `section_data` 구조 확인

---

## 테스트

자동 테스트 실행:
```bash
cd c:/Python_Code/2511_EDB_Cutter_pywebview
.venv/Scripts/python.exe test_edit_integration.py
```

**기대 결과**:
```
Test 1: OK - Method exists
Test 2: OK - Method exists
Test 3: OK - Loaded 4 sections
Test 4: OK - Module imported successfully
All tests passed!
```

---

## 버전 정보

- **추가 날짜**: 2026-02-13
- **EDB Cutter 버전**: 2511 (pywebview)
- **stackup_extractor 요구 버전**: ≥ 1.0 (editor 모듈 포함)
- **Python 버전**: 3.10+

---

## 참고 자료

- `stackup_extractor.editor.edit_and_export()` 문서
- `gui/__init__.py` - API 메서드 구현
- `gui/sectionSelector.js` - JavaScript 함수 구현
- `CLAUDE.md` - 프로젝트 가이드라인
