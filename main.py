"""
실제 Google ADK 실행 테스트
"""

import asyncio
import argparse
import tomllib
import re
from pathlib import Path
from generator_critic.agent import MotivationalInterviewingSystem


def load_config(toml_path: str) -> dict:
    """TOML 파일에서 설정 로드"""
    toml_file = Path(toml_path)
    if not toml_file.exists():
        raise FileNotFoundError(f"TOML 파일을 찾을 수 없습니다: {toml_path}")

    with open(toml_file, "rb") as f:
        config = tomllib.load(f)

    return config


def extract_session_number(config_path: str) -> str:
    """config 파일 경로에서 세션 번호 추출

    예시:
        tasks/task_01.toml → "01"
        task_12.toml → "12"
        other_file.toml → "01" (기본값)
    """
    config_filename = Path(config_path).stem  # 확장자 제거

    # task_XX 패턴에서 숫자 추출
    match = re.search(r"task_(\d+)", config_filename)
    if match:
        return match.group(1).zfill(2)  # 2자리로 패딩 (1 → 01)

    # 패턴이 맞지 않으면 기본값 반환
    return "01"


async def simulate_interview(config_path: str, serial_number: int = 1):
    """실제 ADK 실행 테스트"""

    print("🔧 실제 Google ADK 테스트 시작")

    # TOML 설정 로드
    config = load_config(config_path)

    # 세션 번호 추출
    session_number = extract_session_number(config_path)

    # 시리얼 번호를 3자리 0 패딩된 문자열로 변환
    serial_str = f"{serial_number:03d}"

    # 설정값 추출
    client_section = config.get("Client", {})
    session_section = config.get("Session", {})

    client_problem = client_section.get("problem", "").strip()
    session_goal = session_section.get("goal", "").strip()
    max_interactions = session_section.get("max_interactions", 10)
    reference_material = session_section.get("reference", "").strip()

    print(f"📋 설정 파일: {config_path}")
    print(f"🏷️  시리얼 번호: {serial_number} → {serial_str}")
    print(f"📝 세션 번호: {session_number}")
    print(f"🎯 세션 목표: {session_goal}")
    print(f"🔄 최대 상호작용: {max_interactions}")

    mi_system = MotivationalInterviewingSystem(
        max_interactions=max_interactions, serial_number=serial_str, session_number=session_number
    )

    try:
        print("실제 ADK 세션 시작...")
        output_file = await mi_system.run_session(
            client_problem=client_problem, session_goal=session_goal, reference_material=reference_material
        )
        print(f"성공: {output_file}")
        return output_file

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Motivational Interviewing System")
    parser.add_argument("config", help="TOML 설정 파일 경로 (예: tasks/task_01.toml)")
    parser.add_argument(
        "--serial", type=int, default=1, help="시리얼 번호 (정수, 기본값: 1, 파일명에서는 001로 패딩됨)"
    )

    args = parser.parse_args()

    result = asyncio.run(simulate_interview(args.config, args.serial))
    print(f"최종 결과: {result}")

    # # 파일명 예시 출력
    # session_number = extract_session_number(args.config)
    # serial_str = f"{args.serial:03d}"
    # print(f"\n💡 생성된 파일명 형식:")
    # print(f"   전체 세션: {serial_str}_s{session_number}_session_YYYYMMDD_HHMMSS.md")
    # print(f"   대화만: {serial_str}_s{session_number}_dialogue_YYYYMMDD_HHMMSS.md")


if __name__ == "__main__":
    main()
