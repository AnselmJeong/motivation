"""
Motivational Interviewing Multi-Agent System 테스트 스크립트

이 스크립트는 Google ADK를 사용한 MI 시스템의 간단한 사용 예시를 보여줍니다.
"""

from generator_critic.agent import run_mi_session_sync, create_mi_session
import asyncio


def main():
    """메인 실행 함수"""

    print("🩺 Motivational Interviewing Multi-Agent System")
    print("=" * 50)

    # 예시 시나리오 1: 음주 문제
    print("\n📋 시나리오 1: 음주 문제 상담")
    print("-" * 30)

    client_problem_1 = """
    35세 직장인으로 최근 스트레스로 인한 과음 문제가 심해지고 있습니다.
    주 4-5회 정도 퇴근 후 혼자 술을 마시며, 양도 점점 늘어나고 있습니다.
    가족들이 걱정을 표하지만 본인은 스트레스 해소를 위해 필요하다고 생각합니다.
    """

    session_goal_1 = """
    내담자가 현재 음주 패턴에 대해 성찰하고, 
    건강한 스트레스 관리 방법에 대한 동기를 발견하도록 돕는다.
    """

    reference_material_1 = """
    MI 기본 원칙: OARS (Open questions, Affirmations, Reflections, Summaries)
    변화 언어 강화, 저항 최소화, 내담자 자율성 존중
    양가감정 탐색: "한편으로는... 다른 한편으로는..."
    """

    try:
        print("세션을 시작합니다...")
        output_file_1 = run_mi_session_sync(
            client_problem=client_problem_1,
            session_goal=session_goal_1,
            reference_material=reference_material_1,
            max_interactions=15,  # 짧은 데모를 위해
        )
        print(f"✅ 세션 1 완료: {output_file_1}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    print("\n" + "=" * 50)

    # 예시 시나리오 2: 운동 동기 부족
    print("\n📋 시나리오 2: 운동 동기 부족")
    print("-" * 30)

    client_problem_2 = """
    28세 사무직 직장인으로 최근 체중이 늘어나고 건강이 우려되는 상황입니다.
    운동의 필요성은 알고 있지만 시간도 부족하고 의지도 부족합니다.
    여러 번 헬스장 등록을 했지만 한 달도 못 가고 포기하곤 합니다.
    """

    session_goal_2 = """
    내담자가 운동에 대한 내재적 동기를 찾고,
    현실적이고 지속 가능한 운동 계획에 대한 의지를 강화하도록 돕는다.
    """

    reference_material_2 = """
    변화의 단계: 전숙고 → 숙고 → 준비 → 행동 → 유지
    목표 설정: SMART 원칙 (구체적, 측정가능, 달성가능, 관련성, 시간한정)
    MI 기법: 확대 질문, 중요도 척도, 자신감 척도
    """

    try:
        print("세션을 시작합니다...")
        output_file_2 = run_mi_session_sync(
            client_problem=client_problem_2,
            session_goal=session_goal_2,
            reference_material=reference_material_2,
            max_interactions=15,  # 짧은 데모를 위해
        )
        print(f"✅ 세션 2 완료: {output_file_2}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def async_example():
    """비동기 실행 예시 - 게임 중독 상담"""

    print("\n🔄 비동기 실행 예시: 게임 중독 상담")
    print("-" * 40)

    client_problem = """
    대학생으로 최근 학업 스트레스로 인해 게임에 과도하게 의존하고 있습니다.
    하루 6-8시간씩 게임을 하며, 수업도 자주 빠지고 과제도 밀리고 있습니다.
    부모님과 갈등도 심해지고 있으며, 친구들과도 만나지 않게 되었습니다.
    """

    session_goal = """
    게임 사용 패턴을 점검하고 학업과 게임 사이의 균형을 찾도록 돕는다.
    건강한 여가 활동과 스트레스 관리 방법을 모색하게 한다.
    """

    reference_material = """
    행동 변화 기법: 자기 모니터링, 환경 조성, 대안 활동 탐색
    MI 원칙: 판단하지 않기, 저항과 함께 구르기, 자율성 지지하기
    변화 준비도 척도: 중요도와 자신감 탐색
    """

    try:
        print("비동기 세션을 시작합니다...")
        output_file = await create_mi_session(
            client_problem=client_problem,
            session_goal=session_goal,
            reference_material=reference_material,
            max_interactions=50,  # 조금 더 긴 세션
        )
        print(f"✅ 비동기 세션 완료: {output_file}")
        return output_file

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


if __name__ == "__main__":
    print("Google ADK를 사용한 Motivational Interviewing System 시작\n")

    # 동기 예시들 실행
    main()

    # 비동기 예시 실행
    print("\n" + "=" * 50)
    async_result = asyncio.run(async_example())

    if async_result:
        print(f"\n📄 비동기 세션 결과 파일: {async_result}")

    print("\n🎉 모든 세션이 완료되었습니다!")
    print("📁 output/ 폴더에서 생성된 세션 기록을 확인할 수 있습니다.")
