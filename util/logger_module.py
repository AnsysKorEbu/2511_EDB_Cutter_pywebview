# <2025> ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited

import os
import logging
from datetime import datetime
from pathlib import Path

# 모듈 레벨에서 타임스탬프 한 번만 생성 (한 실행 세션에서 재사용)
# 환경 변수에서 타임스탬프를 가져오거나, 없으면 새로 생성
_LOG_TIMESTAMP = os.environ.get('EDB_CUTTER_LOG_TIMESTAMP', datetime.now().strftime('%Y%m%d_%H%M%S'))

# 로그 파일 경로를 저장하는 전역 변수
_LOG_FILE_PATH = None

def get_log_file_path():
    """현재 로그 파일의 전체 경로를 반환

    Returns:
        str: 로그 파일의 전체 경로
    """
    global _LOG_FILE_PATH
    if _LOG_FILE_PATH is None:
        # 로거가 아직 초기화되지 않았으면 기본 경로 반환
        return str(Path('logs') / f'{_LOG_TIMESTAMP}.log')
    return _LOG_FILE_PATH

def setup_logger(save_folder=None, log_filename=None):
    """로거를 설정하거나 이미 설정된 로거를 재사용

    Args:
        save_folder: 로그 파일을 저장할 폴더 경로. None이면 'logs' 폴더 사용
        log_filename: 로그 파일 이름. None이면 '{timestamp}.log' 형식 사용

    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    global _LOG_FILE_PATH
    logger = logging.getLogger('process_logger')

    # 이미 핸들러가 설정되어 있으면 기존 로거 재사용
    # 이렇게 하면 한 실행 세션에서 여러 번 호출해도 같은 로거/파일 사용
    if logger.handlers:
        return logger

    # 기본 로그 폴더 설정
    if save_folder is None:
        save_folder = Path('logs')

    # 기본 로그 파일명 설정 (타임스탬프 포함)
    if log_filename is None:
        log_filename = f'{_LOG_TIMESTAMP}.log'

    # 핸들러가 없을 때만 새로 설정
    os.makedirs(save_folder, exist_ok=True)
    log_file = os.path.join(save_folder, log_filename)
    _LOG_FILE_PATH = str(Path(log_file).resolve())  # 절대 경로로 저장
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러 (파일에 저장)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    # 콘솔 핸들러 (터미널에 출력)
    ch = logging.StreamHandler()

    # 포매터 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

# 기본 로거 인스턴스 생성 (logs/{timestamp}.log에 저장)
logger = setup_logger()

# 환경 변수에 타임스탬프 설정 (subprocess에서 사용)
os.environ['EDB_CUTTER_LOG_TIMESTAMP'] = _LOG_TIMESTAMP
