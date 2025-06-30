"""
간단한 테스트 스크립트 - 짧은 세션으로 테스트
"""

from generator_critic.agent import run_mi_session_sync

def test_short_session():
    """짧은 세션 테스트"""
    
    print("🩺 간단한 MI 세션 테스트 시작")
    print("=" * 40)
    
    client_problem = """
    직장 스트레스로 인한 과음 문제가 있는 35세 직장인입니다.
    """
    
    session_goal = """
    음주 패턴에 대한 성찰을 돕고 변화 동기를 탐색합니다.
    """
    
    reference_material = """
    MI 기본 원칙: OARS (Open questions, Affirmations, Reflections, Summaries)
    """
    
    try:
        print("세션 시작...")
        output_file = run_mi_session_sync(
            client_problem=client_problem,
            session_goal=session_goal,
            reference_material=reference_material,
            max_interactions=3  # 매우 짧은 테스트
        )
        print(f"✅ 테스트 완료: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

if __name__ == "__main__":
    test_short_session()