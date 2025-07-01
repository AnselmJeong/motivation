"""
실제 Google ADK 실행 테스트
"""

import asyncio
import argparse
import tomllib
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


async def simulate_interview(config_path: str):
    """실제 ADK 실행 테스트"""

    print("🔧 실제 Google ADK 테스트 시작")

    # TOML 설정 로드
    config = load_config(config_path)

    # 설정값 추출
    client_section = config.get("Client", {})
    session_section = config.get("Session", {})

    client_problem = client_section.get("problem", "").strip()
    session_goal = session_section.get("goal", "").strip()
    max_interactions = session_section.get("max_interactions", 10)
    reference_material = session_section.get("reference", "").strip()

    print(f"📋 설정 파일: {config_path}")
    print(f"🎯 세션 목표: {session_goal}")
    print(f"🔄 최대 상호작용: {max_interactions}")

    mi_system = MotivationalInterviewingSystem(max_interactions=max_interactions)

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
    parser.add_argument("config", help="TOML 설정 파일 경로")

    args = parser.parse_args()

    result = asyncio.run(simulate_interview(args.config))
    print(f"최종 결과: {result}")


if __name__ == "__main__":
    main()
