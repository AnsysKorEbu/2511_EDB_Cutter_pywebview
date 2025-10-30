"""
Unit configuration for EDB Cutter

To change the input unit, modify INPUT_UNIT below:
- 'mm': millimeters
- 'meter': meters
- 'um': micrometers
"""

# EDB 추출 데이터 단위 (여기만 수정하면 됨)
INPUT_UNIT = 'mm'  # 옵션: 'mm', 'meter', 'um'

# um으로 변환하는 배율
UNIT_TO_UM = {
    'mm': 1000,      # 1mm = 1000um
    'meter': 1e6,    # 1m = 1,000,000um
    'um': 1          # 1um = 1um
}

# 현재 설정에 따른 배율
SCALE = UNIT_TO_UM[INPUT_UNIT]

# EDB 버전 설정
EDB_VERSION = "2025.1"
