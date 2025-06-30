"""
실제 Google ADK 실행 테스트
"""

import asyncio
from generator_critic.agent import MotivationalInterviewingSystem


async def test_real_adk():
    """실제 ADK 실행 테스트"""

    print("🔧 실제 Google ADK 테스트 시작")

    mi_system = MotivationalInterviewingSystem(max_interactions=10)  # 더 긴 세션

    client_problem = "직장 스트레스로 인한 과음 문제"
    session_goal = "음주 패턴 성찰 돕기"
    reference_material = "MI 기본 원칙: OARS"

    try:
        print("실제 ADK 세션 시작...")
        output_file = await mi_system.run_session(
            client_problem=client_problem,
            session_goal=session_goal,
            reference_material=reference_material,
            max_interactions=30,
        )
        print(f"성공: {output_file}")
        return output_file

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_real_adk())
    print(f"최종 결과: {result}")
