# EDB Cutter - Refactoring Plan

> **작성일**: 2026-02-12
> **전체 코드량**: Python 12,948 LOC (`.venv` 제외)
> **목적**: 반복 수정으로 누적된 코드 품질 저하 정리

---

## 현재 상태 요약

| 지표 | 수치 | 평가 |
|------|------|------|
| 가장 큰 파일 | `net_port_handler.py` (1,097줄) | 분할 필요 |
| 중복 코드 | ~1,990줄 (excel_reader 2벌) | 즉시 제거 |
| God Class | `gui/__init__.py` Api (1,033줄, 25개 메서드) | 분할 필요 |
| 에러 처리 | `import traceback` 인라인 7곳+ | 통일 필요 |
| 테스트 커버리지 | ~10% 추정 | 부족 |

### 파일 크기 TOP 10

```
1,097  edb/cut/net_port_handler.py      ← 기하학 연산 + EDB 처리 혼재
1,043  stackup/readers/excel_reader.py  ← standalone/와 중복
1,033  gui/__init__.py                  ← God Class (Api)
  947  standalone/excel_reader.py       ← stackup/readers/와 중복
  889  stackup/generate_stackup.py      ← XML 생성 + 데이터 처리 혼재
  509  edb/cut/edb_manager.py
  484  gui/analysis/analysis_gui.py
  447  edb/cut/__main__.py
  417  edb/cut/stackup_loader.py
  386  stackup/section_selector.py
```

---

## Phase 1: 중복 코드 제거 (Priority: Critical)

### 1-1. standalone/ 모듈의 excel_reader 중복 제거

**문제**: `stackup/readers/excel_reader.py` (1,043줄)과 `standalone/excel_reader.py` (947줄)이 95% 동일한 코드. 버그 수정 시 양쪽 다 수정해야 하는 유지보수 악몽.

**연관 파일**:
- `standalone/preprocessing.py` (146줄) ↔ `stackup/core/preprocessing.py` (384줄)
- `standalone/config.py` (108줄) ↔ `stackup/core/config.py` (125줄)
- `standalone/logger.py` (68줄) ↔ `util/logger_module.py` (146줄)

**해결 방안**:
1. `standalone/` 모듈이 `stackup/readers/excel_reader.py`를 직접 import 하도록 변경
2. `standalone/excel_reader.py`, `standalone/preprocessing.py` 삭제
3. `standalone/config.py`와 `standalone/logger.py`는 본체 모듈의 것을 re-export
4. standalone 전용 로직만 남김

**예상 삭감**: ~1,100줄

---

## Phase 2: God Class 분할 (Priority: High)

### 2-1. `gui/__init__.py` Api 클래스 분할

**문제**: 1,033줄, 25개 메서드가 하나의 클래스에 집중. 15가지 이상의 책임을 가짐.

**현재 메서드 분류**:

| 그룹 | 메서드 | 줄 수 (대략) |
|------|--------|-------------|
| EDB 데이터 로딩 | `load_edb_data`, `_ensure_data_loaded`, `get_planes_data`, `get_vias_data`, `get_traces_data`, `get_nets_data` | ~60줄 |
| Cut 관리 (CRUD) | `save_cut_data`, `get_cut_list`, `delete_cut`, `rename_cut`, `get_cut_data` | ~140줄 |
| Cut 실행 | `execute_cuts` | ~115줄 |
| Stackup/Section | `process_stackup`, `browse_excel_for_sections`, `use_stackup_extractor`, `get_cuts_for_section_selection`, `save_section_selection` | ~280줄 |
| SSS 파일 | `get_latest_sss_file`, `browse_sss_file` | ~90줄 |
| GUI 런처 | `browse_results_folder_for_analysis`, `launch_analysis_gui_window`, `launch_schematic_gui_window`, `launch_circuit_gui_window` | ~140줄 |
| 윈도우 관리 | `close_main_window` | ~20줄 |

**해결 방안**: Mixin 패턴으로 분리 (pywebview가 단일 js_api 객체를 요구하므로 상속으로 합성)

```
gui/
├── __init__.py          ← Api 클래스 (Mixin 상속만), start_gui()
├── api_data.py          ← EdbDataMixin (EDB 데이터 로딩/조회)
├── api_cut.py           ← CutManagementMixin (Cut CRUD + 실행)
├── api_stackup.py       ← StackupMixin (Stackup/Section 처리)
├── api_file.py          ← FileManagementMixin (SSS, 파일 브라우저)
├── api_launcher.py      ← LauncherMixin (Analysis/Schematic/Circuit GUI 실행)
```

**`gui/__init__.py` 변경 후 모습**:
```python
class Api(EdbDataMixin, CutManagementMixin, StackupMixin,
          FileManagementMixin, LauncherMixin):
    def __init__(self, edb_path, edb_version, grpc=False):
        # 공통 초기화만
        ...
```

**예상 효과**: `__init__.py`가 1,033줄 → ~60줄로 축소. 각 Mixin은 100~280줄.

---

## Phase 3: 대형 모듈 정리 (Priority: Medium)

### 3-1. `edb/cut/net_port_handler.py` 분할

**문제**: 1,097줄. 기하학 유틸리티(점-다각형 판정, 거리 계산 등)와 EDB 커팅 로직이 혼재.

**해결 방안**:
```
edb/cut/
├── net_port_handler.py  ← EDB 커팅 관련만 (cutout, port 생성)
├── geometry.py          ← 기하학 유틸 분리 (point_in_polygon, distance, intersection)
```

**예상 효과**: 각 파일 400~600줄 수준으로 분할, 기하학 유틸은 독립 테스트 가능

### 3-2. `stackup/generate_stackup.py` 정리

**문제**: 889줄. XML 생성, 데이터 변환, 파일 I/O가 한 파일에 혼재.

**해결 방안**:
```
stackup/
├── generate_stackup.py  ← orchestration만 (기존 public API 유지)
├── xml_builder.py       ← XML 생성 로직 분리
```

---

## Phase 4: 코드 품질 통일 (Priority: Medium)

### 4-1. 에러 핸들링 통일

**문제**: 같은 패턴이 7곳 이상에서 반복:
```python
# 현재 - 파일마다 반복
except Exception as e:
    error_msg = f"Failed to ...: {str(e)}"
    logger.error(f"\n[ERROR] {error_msg}")
    import traceback
    traceback.print_exc()
    return {'success': False, 'error': error_msg}
```

**해당 파일들**:
- `gui/__init__.py` (7곳: L375, L412, L448, L482, L509, L548, L693...)
- `stackup_new/extractor_integration.py` (2곳)
- 기타 산발적

**해결 방안**: 데코레이터로 통일
```python
# util/error_handler.py
def api_error_handler(func):
    """API 메서드용 에러 핸들링 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {e}")
            return error_response(e)
    return wrapper
```

**적용 후**:
```python
@api_error_handler
def execute_cuts(self, cut_ids, selected_nets=None, use_stackup=True):
    # try-except 블록 제거, 핵심 로직만 남음
    ...
```

### 4-2. 로깅 레벨 수정

**문제**: 에러인데 `logger.info()`로 기록하는 곳이 있음.

**해당 위치**:
- `gui/__init__.py:89` → `logger.info(f"Error loading data: {e}")` → `logger.error()`
- `gui/__init__.py:184` → `logger.info(f"Error reading {cut_file}: {e}")` → `logger.warning()`
- `gui/__init__.py:188` → 같은 문제
- `gui/__init__.py:446` → `logger.info(f"\n[ERROR] {error_msg}")` → `logger.error()`

### 4-3. 응답 포맷 통일

**문제**: 일부는 `success_response()`/`error_response()` 사용, 일부는 직접 dict 생성.

**직접 dict를 쓰는 곳** (config의 헬퍼 함수 미사용):
- `gui/__init__.py:82-90` (`load_edb_data`)
- `gui/__init__.py:403` (`browse_results_folder_for_analysis`)
- `gui/__init__.py:442` (`launch_analysis_gui_window`)
- `gui/__init__.py:476` (`launch_schematic_gui_window`)
- `gui/__init__.py:503` (`launch_circuit_gui_window`)

**해결**: 모두 `success_response()`/`error_response()` 사용으로 통일

### 4-4. tkinter 파일 다이얼로그 중복 제거

**문제**: tkinter 초기화/정리 코드가 4곳에서 동일하게 반복:
```python
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', 1)
# ... filedialog 호출 ...
root.destroy()
```

**해당 위치**:
- `gui/__init__.py:567-583` (`browse_excel_for_sections`)
- `gui/__init__.py:638-654` (`use_stackup_extractor`)
- `gui/__init__.py:778-796` (`browse_sss_file`)
- `gui/__init__.py:387-399` (`browse_results_folder_for_analysis`)

**해결**: 유틸리티 함수로 추출
```python
# gui/dialogs.py
def open_file_dialog(title, initial_dir, filetypes):
    """tkinter 파일 선택 대화상자 (보일러플레이트 제거)"""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    try:
        return filedialog.askopenfilename(
            title=title, initialdir=str(initial_dir), filetypes=filetypes
        )
    finally:
        root.destroy()
```

---

## Phase 5: config 활용도 개선 (Priority: Low)

### 5-1. config에 정의된 상수 미사용 문제

**문제**: `config/config.py`에 잘 정리된 상수가 있지만, 일부 코드에서 하드코딩을 사용.

**예시**:
- `gui/__init__.py:987-993` → 윈도우 크기/타이틀이 하드코딩됨 (`MAIN_WINDOW_WIDTH` 등 미사용)
- `gui/__init__.py:1020-1028` → Analysis 윈도우 설정도 하드코딩

**해결**: config 상수 import 및 적용

### 5-2. `config/config.py`의 ERROR_MESSAGES / SUCCESS_MESSAGES 미사용

현재 정의만 되어 있고 어디서도 참조하지 않음. 활용하거나 삭제.

---

## Phase 6: 테스트 정비 (Priority: Low)

### 6-1. 루트 레벨 테스트 파일 이동

**문제**: `test_stackup_generation.py`가 프로젝트 루트에 존재.

**해결**: `test/` 폴더로 이동

### 6-2. 핵심 모듈 테스트 추가

Phase 1~4 리팩토링 완료 후, 분리된 모듈에 대해 단위 테스트 추가:
- `gui/api_cut.py` → Cut CRUD 테스트
- `edb/cut/geometry.py` → 기하학 연산 테스트
- `util/error_handler.py` → 데코레이터 동작 테스트

---

## 리팩토링 순서 요약

| 순서 | Phase | 작업 | 영향도 | 난이도 |
|------|-------|------|--------|--------|
| 1 | Phase 4-2 | 로깅 레벨 수정 (4곳) | 낮음 | 매우 쉬움 |
| 2 | Phase 4-3 | 응답 포맷 통일 (5곳) | 낮음 | 쉬움 |
| 3 | Phase 4-4 | tkinter 다이얼로그 헬퍼 추출 | 낮음 | 쉬움 |
| 4 | Phase 4-1 | 에러 핸들링 데코레이터 | 중간 | 쉬움 |
| 5 | Phase 1-1 | standalone/ 중복 제거 | 높음 | 중간 |
| 6 | Phase 2-1 | Api God Class 분할 (Mixin) | 높음 | 중간 |
| 7 | Phase 3-1 | net_port_handler 분할 | 중간 | 중간 |
| 8 | Phase 3-2 | generate_stackup 분할 | 중간 | 중간 |
| 9 | Phase 5 | config 상수 활용 | 낮음 | 쉬움 |
| 10 | Phase 6 | 테스트 정비 | 낮음 | 중간 |

---

## 주의사항

1. **pywebview 제약**: `js_api`에 단일 객체만 전달 가능 → Api 클래스를 완전 분리하면 안 되고 Mixin 상속으로 합성해야 함
2. **subprocess 패턴 유지**: `edb.cut`, `edb.analysis` 등은 pythonnet 충돌 방지를 위해 subprocess로 실행 → 이 패턴은 건드리지 않음
3. **merge_copper=True 기본값**: CLAUDE.md 규칙 유지
4. **단계적 적용**: 한 번에 전부 하지 말고 Phase별로 동작 확인 후 다음 진행
5. **기존 API 시그니처 유지**: JS에서 호출하는 메서드 이름/파라미터는 변경하지 않음 (내부 구조만 리팩토링)
