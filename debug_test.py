"""
디버깅용 테스트 스크립트
"""

import asyncio
from generator_critic.agent import MotivationalInterviewingSystem

async def debug_test():
    """기본 시스템 초기화 테스트"""
    
    print("🔧 디버깅 테스트 시작")
    
    try:
        # 시스템 생성
        print("1. 시스템 생성 중...")
        mi_system = MotivationalInterviewingSystem(max_interactions=2)
        print("   ✅ 시스템 생성 완료")
        
        # 에이전트 확인
        print("2. 에이전트 확인 중...")
        print(f"   - Therapist: {mi_system.therapist.name}")
        print(f"   - Client: {mi_system.client.name}")
        print(f"   - Supervisor: {mi_system.supervisor.name}")
        print(f"   - ConversationManager: {mi_system.conversation_manager.name}")
        print("   ✅ 에이전트 확인 완료")
        
        print("3. Mock 세션 테스트...")
        output = await mi_system._run_mock_session(
            "테스트 문제", 
            "테스트 목표", 
            "테스트 자료"
        )
        print(f"   ✅ Mock 세션 완료: {output}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(debug_test())
    print(f"최종 결과: {result}")