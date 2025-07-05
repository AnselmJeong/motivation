"""
Review Planner Multi-Agent System using Google ADK

이 시스템은 두 가지 에이전트로 구성됩니다:
1. ReviewerAgent: 마지막 면담 세션을 분석하고 평가하는 에이전트
2. PlannerAgent: 다음 세션을 계획하고 목표를 설정하는 에이전트

ReviewerAgent는 output 디렉터리의 최신 대화 파일을 읽고 분석하며,
PlannerAgent는 리뷰 결과를 바탕으로 다음 세션을 계획합니다.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import glob

load_dotenv()

MODEL = "gemini-2.5-flash"

# Google ADK의 올바른 imports
try:
    from google.adk.agents import Agent as LlmAgent
    ADK_AVAILABLE = True
    print("✅ Google ADK가 성공적으로 로드되었습니다.")
except ImportError:
    print("❌ Google ADK가 설치되지 않았습니다. 모의(mock) 클래스를 사용합니다.")
    ADK_AVAILABLE = False

    # Mock classes for development without ADK
    class LlmAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "MockAgent")
            self.instruction = kwargs.get("instruction", "")
            self.output_key = kwargs.get("output_key", None)


def find_latest_dialogue_file(output_dir: str = "output", serial_number: int = 1) -> Optional[str]:
    """
    output 디렉터리에서 지정된 serial number의 가장 최근 세션 대화 파일을 찾습니다.
    파일 형식: {serial:03d}_s{session:02d}_dialogue_{timestamp}.md
    """
    # 지정된 serial number의 dialogue 파일들 찾기
    pattern = os.path.join(output_dir, f"{serial_number:03d}_s*_dialogue_*.md")
    files = glob.glob(pattern)
    
    if not files:
        print(f"❌ {output_dir} 디렉터리에서 {serial_number:03d}_s*_dialogue_*.md 파일을 찾을 수 없습니다.")
        return None
    
    # 파일명에서 세션 번호와 타임스탬프 추출하여 정렬
    def extract_session_and_timestamp(filename):
        basename = os.path.basename(filename)
        # 파일명 예: 001_s01_dialogue_20250704_110257.md
        parts = basename.split('_')
        if len(parts) >= 5:
            session_str = parts[1][1:]  # 's01' -> '01'
            timestamp = '_'.join(parts[3:5])  # '20250704_110257'
            return int(session_str), timestamp
        return 0, ''
    
    # 세션 번호 내림차순, 타임스탬프 내림차순으로 정렬
    files.sort(key=extract_session_and_timestamp, reverse=True)
    latest_file = files[0]
    
    session_num, timestamp = extract_session_and_timestamp(latest_file)
    print(f"✅ 최신 대화 파일을 찾았습니다: {latest_file} (세션 {session_num:02d})")
    return latest_file


def read_dialogue_file(file_path: str) -> Optional[str]:
    """
    대화 파일을 읽어서 내용을 반환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ 파일을 성공적으로 읽었습니다: {file_path}")
        return content
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {file_path}, 오류: {e}")
        return None


class ReviewerAgent(LlmAgent):
    """
    마지막 면담 세션을 분석하고 평가하는 에이전트
    """
    
    def __init__(self):
        instruction = """
        당신은 동기 부여 면담(Motivational Interviewing) 전문가입니다.
        
        주어진 면담 세션 내용을 철저히 분석하고 다음 항목에 대해 평가하세요:
        
        1. 치료사가 성취하려고 했던 목표와 접근 방식 분석
        2. 목표 달성 정도 평가 (0-100% 스케일)
        3. 목표가 달성되지 못한 부분의 문제점과 개선점 제안
        4. 내담자의 문제 해결에 도움이 되었는지 평가
        5. 필요시 목표 수정 제안
        
        분석 결과를 구조화된 마크다운 형태로 제공하세요.
        객관적이고 건설적인 피드백을 제공하되, 치료사의 노력을 인정하고 격려하는 톤을 유지하세요.
        """
        
        super().__init__(
            name="ReviewerAgent",
            instruction=instruction,
            model=MODEL,
            output_key="review_analysis"
        )

    async def analyze_session(self, dialogue_content: str) -> str:
        """
        면담 세션 내용을 분석하고 리뷰 결과를 반환합니다.
        """
        if not ADK_AVAILABLE:
            raise ImportError("Google ADK가 설치되지 않았습니다. 'uv add google-adk'로 설치해주세요.")
        
        # Google ADK를 사용한 실제 분석 구현
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        
        try:
            # 세션 서비스 및 세션 생성
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="ReviewPlanner",
                user_id="reviewer_001",
                session_id=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )
            
            # 초기 상태 설정
            session.state.update({
                "dialogue_content": dialogue_content,
                "analysis_request": "면담 세션 분석 요청"
            })
            
            # Runner 생성 및 실행
            runner = Runner(
                agent=self,
                session_service=session_service,
                app_name="ReviewPlanner"
            )
            
            # 분석 시작 메시지
            analysis_message = types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"다음 면담 세션 내용을 분석해주세요:\\n\\n{dialogue_content}"
                    )
                ],
            )
            
            print("📊 Google ADK를 사용하여 세션 분석을 시작합니다...")
            
            # 에이전트 실행
            events = runner.run(
                user_id="reviewer_001",
                session_id=session.id,
                new_message=analysis_message
            )
            
            # 결과 수집
            analysis_result = ""
            try:
                async for event in events:
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                analysis_result += part.text
                    
                    # 종료 조건 확인
                    if hasattr(event, "actions") and event.actions and event.actions.escalate:
                        break
                        
            except TypeError:
                # 동기 iterator인 경우
                for event in events:
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                analysis_result += part.text
                    
                    if hasattr(event, "actions") and event.actions and event.actions.escalate:
                        break
            
            return analysis_result if analysis_result else "분석 결과를 생성할 수 없습니다."
            
        except Exception as e:
            print(f"❌ 분석 중 오류 발생: {e}")
            raise e


class PlannerAgent(LlmAgent):
    """
    다음 세션을 계획하고 목표를 설정하는 에이전트
    """
    
    def __init__(self):
        instruction = """
        당신은 동기 부여 면담(Motivational Interviewing) 세션 계획 전문가입니다.
        
        리뷰 분석 결과를 바탕으로 다음 세션을 계획하세요:
        
        1. 내담자의 원래 상담 목적 재확인
        2. 전체 MI 관점에서 내담자의 심리 상태 진전도 평가
        3. 문제 해결 가능성 향상 정도 평가
        4. 다음 세션의 구체적 목표 설정
        5. 적절한 참고 자료 및 접근 방법 제안
        
        전체 12 세션 중 현재 위치를 고려하여 단계적이고 현실적인 계획을 수립하세요.
        내담자의 준비도와 변화 단계를 고려한 맞춤형 계획을 제공하세요.
        """
        
        super().__init__(
            name="PlannerAgent",
            instruction=instruction,
            model=MODEL,
            output_key="session_plan"
        )

    async def create_session_plan(self, review_analysis: str, session_number: int = 1) -> str:
        """
        리뷰 분석을 바탕으로 다음 세션 계획을 생성합니다.
        """
        if not ADK_AVAILABLE:
            return self._mock_planning(review_analysis, session_number)
        
        # 실제 ADK 구현은 여기에 추가
        # 현재는 mock 계획을 반환
        return self._mock_planning(review_analysis, session_number)
    
    def _mock_planning(self, review_analysis: str, session_number: int) -> str:
        """
        Mock 세션 계획을 반환합니다.
        """
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        
        plan = f"""# 다음 세션 계획서

**생성일시**: {current_time}
**세션 번호**: {session_number + 1}/12
**계획 근거**: 이전 세션 분석 결과

## 1. 내담자의 원래 상담 목적

### 주요 문제
- 생활 패턴 개선 및 자기관리 능력 향상
- 대인관계에서의 자신감 부족
- 미래에 대한 불안감과 방향성 부족

### 상담 목적
- 건강한 생활 습관 형성
- 자기효능감 증진
- 구체적인 목표 설정 및 실행력 향상

## 2. 심리 상태 진전도 평가

**전체 진전도: 65%**

### 진전 영역
- ✅ 문제 인식 및 동기 부여: 80% 진전
- ✅ 자기 탐색 및 통찰: 70% 진전
- ⚠️ 행동 변화 준비: 50% 진전
- ❌ 실제 행동 실행: 30% 진전

### 변화 단계
**현재 단계**: 숙고 단계 (Contemplation)
**목표 단계**: 준비 단계 (Preparation)로 이동

## 3. 문제 해결 가능성 향상 정도

**가능성 증가율: 60%**

### 긍정적 요인
- 내담자의 변화 동기 증가
- 문제에 대한 인식 명확화
- 치료적 관계 형성

### 도전 요인
- 구체적 행동 계획 부족
- 자기효능감 여전히 낮음
- 환경적 지지체계 부족

## 4. 다음 세션 목표 설정

### 주요 목표
1. **구체적 행동 계획 수립** (우선순위: 높음)
   - 일일 루틴 중 1-2개 작은 변화 선택
   - 실행 가능한 단기 목표 설정

2. **자기효능감 증진** (우선순위: 높음)
   - 과거 성공 경험 탐색
   - 강점과 자원 재발견

3. **변화 동기 강화** (우선순위: 중간)
   - 변화의 이유와 가치 명확화
   - 변화 후 긍정적 결과 시각화

### 세부 목표
- 내담자가 스스로 실행 가능한 목표 1개 설정
- 변화에 대한 자신감 점수 20% 향상
- 다음 세션까지의 구체적 실행 계획 수립

## 5. 참고 자료 및 접근 방법

### 권장 참고 자료
- **목표 설정 워크시트**: SMART 목표 설정 기법
- **자기효능감 증진 가이드**: 성공 경험 탐색 및 활용
- **변화 준비도 체크리스트**: 내담자의 준비 상태 점검

### 접근 방법
1. **협력적 목표 설정**
   - 내담자 주도의 목표 선택
   - 치료사는 안내자 역할

2. **강점 중심 접근**
   - 문제보다는 해결책과 자원에 집중
   - 내담자의 능력에 대한 믿음 표현

3. **단계적 접근**
   - 작은 변화부터 시작
   - 성공 경험 축적

### 세션 구조 제안
1. **도입** (5분): 지난 세션 요약 및 현재 상태 체크
2. **탐색** (25분): 목표 설정 및 자기효능감 증진 활동
3. **계획** (20분): 구체적 행동 계획 수립
4. **마무리** (10분): 요약 및 다음 세션 준비

## 6. 세션 진행 시 주의사항

### 유의사항
- 내담자의 속도에 맞춰 진행
- 저항이 나타나면 탐색의 기회로 활용
- 완벽함보다는 진전에 집중

### 성공 지표
- 내담자가 구체적 목표 1개 설정
- 실행 계획에 대한 자신감 표현
- 다음 세션에 대한 긍정적 기대

## 전체 평가 및 권장사항

현재 내담자는 변화의 필요성을 인식하고 있으나 구체적 행동으로 이어지지 못하고 있습니다.
다음 세션에서는 작고 실현 가능한 목표 설정에 집중하여 성공 경험을 만들어 주는 것이 중요합니다.
내담자의 자율성을 존중하면서도 적절한 구조와 지지를 제공하는 것이 핵심입니다.
"""
        
        return plan


class ReviewPlannerSystem:
    """
    리뷰와 계획 시스템을 관리하는 메인 클래스
    """
    
    def __init__(self, serial_number: int = 1):
        self.reviewer = ReviewerAgent()
        self.planner = PlannerAgent()
        self.output_dir = "output"
        self.serial_number = serial_number
        
        # output 디렉터리 생성
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def run_review_and_planning(self, session_number: int = 1) -> tuple[str, str]:
        """
        리뷰와 계획 프로세스를 실행합니다.
        """
        print(f"🔍 리뷰 및 계획 시스템을 시작합니다... (Serial: {self.serial_number:03d})")
        
        # 1. 지정된 serial number의 최신 대화 파일 찾기
        latest_file = find_latest_dialogue_file(self.output_dir, self.serial_number)
        if not latest_file:
            raise FileNotFoundError(f"Serial {self.serial_number:03d}의 분석할 대화 파일을 찾을 수 없습니다.")
        
        # 2. 대화 파일 읽기
        dialogue_content = read_dialogue_file(latest_file)
        if not dialogue_content:
            raise ValueError("대화 파일을 읽을 수 없습니다.")
        
        # 3. 리뷰 분석 수행
        print("📊 세션 분석을 시작합니다...")
        review_analysis = await self.reviewer.analyze_session(dialogue_content)
        
        # 4. 결과 저장 (플래너는 나중에 구현)
        review_file = self._save_review_analysis(review_analysis, session_number)
        
        print(f"✅ 리뷰 분석이 저장되었습니다: {review_file}")
        
        return review_file, ""
    
    def _save_review_analysis(self, analysis: str, session_number: int) -> str:
        """
        리뷰 분석 결과를 파일로 저장합니다.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.serial_number:03d}_s{session_number:02d}_review_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(analysis)
        
        return filepath
    
    def _save_session_plan(self, plan: str, session_number: int) -> str:
        """
        세션 계획을 파일로 저장합니다.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.serial_number:03d}_s{session_number + 1:02d}_plan_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(plan)
        
        return filepath


# 동기 실행 함수
def run_review_planning_sync(serial_number: int = 1, session_number: int = 1) -> tuple[str, str]:
    """
    리뷰와 계획 시스템을 동기적으로 실행합니다.
    """
    system = ReviewPlannerSystem(serial_number=serial_number)
    
    try:
        return asyncio.run(system.run_review_and_planning(session_number))
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise


# 비동기 실행 함수
async def run_review_planning_async(serial_number: int = 1, session_number: int = 1) -> tuple[str, str]:
    """
    리뷰와 계획 시스템을 비동기적으로 실행합니다.
    """
    system = ReviewPlannerSystem(serial_number=serial_number)
    return await system.run_review_and_planning(session_number)


if __name__ == "__main__":
    # 테스트 실행
    print("🚀 Review Planner System 테스트를 시작합니다...")
    
    try:
        review_file, plan_file = run_review_planning_sync(serial_number=1, session_number=1)
        print("\n✅ 테스트 완료!")
        print(f"📊 리뷰 파일: {review_file}")
        if plan_file:
            print(f"📋 계획 파일: {plan_file}")
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")