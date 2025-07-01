"""
Motivational Interviewing Multi-Agent System using Google ADK

이 시스템은 세 가지 에이전트로 구성됩니다:
1. TherapistAgent: Motivational Interview를 주도하는 면담자
2. ClientAgent: 문제를 가진 내담자 역할 시뮬레이션
3. SupervisorAgent: 면담자에게 피드백을 제공하는 슈퍼바이저

면담자 -> 내담자 -> 슈퍼바이저 순으로 진행되며, 설정된 최대 상호작용 횟수까지 가능합니다.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash"

# Google ADK의 올바른 imports
try:
    from google.adk.agents import Agent as LlmAgent, SequentialAgent, LoopAgent, BaseAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from google.adk.events import Event, EventActions
    from google.adk.agents.invocation_context import InvocationContext
    from google.adk.tools.tool_context import ToolContext

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

    class SequentialAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "MockSequential")
            self.sub_agents = kwargs.get("sub_agents", [])

    class LoopAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "MockLoop")
            self.max_iterations = kwargs.get("max_iterations", 10)

    class BaseAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "MockBase")

    class Event:
        def __init__(self, **kwargs):
            pass

    class EventActions:
        def __init__(self, **kwargs):
            pass

    class ToolContext:
        def __init__(self, **kwargs):
            pass

    class Runner:
        def __init__(self, **kwargs):
            pass


class TherapistAgent(LlmAgent):
    """Motivational Interview를 주도하는 면담자 에이전트"""

    def __init__(
        self,
        name: str = "Therapist",
        session_goal: str = "",
        reference_material: str = "",
        current_turn: int = 0,
        max_interactions: int = 100,
        remaining_turns: int = 100,
        stage: str = "초기",
    ):
        instruction = f"""
        당신은 경험이 풍부한 Motivational Interviewing 전문가입니다.
        
        🎯 **핵심 원칙: 아래 구체적인 세션 목표와 참고 자료를 최우선으로 활용하세요**
        
        **세션 목표**: {session_goal}
        
        **참고 자료**:
        {reference_material}
        
        **필수 진행 방식:**
        1. **첫 번째**: 위에 명시된 세션 목표 달성을 최우선으로 하세요
        2. **두 번째**: 참고 자료에 제시된 구체적 기법들을 적극 활용하세요. 기법에 얽매이기보다는 자연스러운 대화 진행을 우선시하세요
        3. **세 번째**: 내담자의 문제를 세션 목표 관점에서 재구성하여 접근하세요
        
        **구체적인 활용 방법:**
        - 참고 자료에 제시된 연습, 기법, 개념들을 직접 소개하고 적용하세요
        - 세션 목표와 관련된 질문과 개입을 우선적으로 사용하세요
        - 내담자의 답변을 세션 목표 달성 방향으로 유도하세요
        - 참고 자료의 언어와 개념을 면담에서 사용하세요
                
        **기본 MI 진행 방식 (세션 목표 달성을 위해 사용):**
        1. 공감적 경청과 열린 질문을 사용합니다
        2. 내담자의 양가감정을 탐색합니다  
        3. 변화 동기를 강화합니다
        4. 내담자 중심의 접근을 유지합니다
        
        ⏰ **현재 세션 진행 현황:**
        - **현재 턴**: {current_turn}/{max_interactions}
        - **남은 턴**: {remaining_turns}
        - **세션 단계**: {stage} 단계
        
        **세션 진행 단계별 접근:**
        - **초기 단계** (remaining_turns > max_interactions * 0.7): 라포 형성과 문제 탐색
        - **중기 단계** (remaining_turns > max_interactions * 0.3): 세션 목표 관련 기법 적극 활용
        - **후기 단계** (remaining_turns <= max_interactions * 0.3): 목표 달성을 위한 집중적 개입
        
        각 단계에 맞는 속도로 진행하되, 세션 목표 달성을 최우선으로 하세요.
        
        자연스럽고 따뜻한 톤으로 작성하되, 세션 목표 달성을 위한 참고 자료 기법 적용을 반드시 포함하세요.
        
        🔚 세션 종료 조건:
        세션 목표가 달성되었다고 판단되면 "오늘 면담은 이것으로 마치겠습니다"라고 말하여 세션을 종료하세요.
        목표 달성의 기준:
        - 세션 목표에서 제시한 구체적 목표가 달성됨
        - 참고 자료의 핵심 기법이 내담자에게 전달되고 이해됨
        - 내담자가 세션 목표 관련 인사이트나 변화를 보임
        """

        super().__init__(name=name, instruction=instruction, output_key="therapist_response", model=MODEL)


class ClientAgent(LlmAgent):
    """내담자 역할을 시뮬레이션하는 에이전트"""

    def __init__(self, name: str = "Client", client_problem: str = ""):
        instruction = f"""
        당신은 내담자 역할을 하는 에이전트입니다. 
        
        🎯 **핵심 원칙: 아래 구체적인 내담자 문제 상황에서 벗어나지 마세요**
        
        **내담자 문제**: {client_problem}
        
        **필수 준수사항:**
        1. **첫 번째**: 위에 명시된 내담자 문제로 고민하고 있는 내담자로서 일관되게 반응하세요
        2. **두 번째**: 내담자 문제에 명시된 구체적 상황, 감정, 어려움을 지속적으로 반영하세요
        3. **세 번째**: 면담자가 다른 주제로 유도하더라도 항상 내담자 문제로 돌아가는 경향을 보이세요
        
        **내담자 특성:**
        - 위에 명시된 내담자 문제를 막연히 인식하지만 관련된 생각과 감정을 표현하는 데 어려움이 있습니다
        - 면담자의 리드에 따라 수동적으로 반응하지만 항상 내담자 문제 상황으로 되돌아갑니다
        - 면담자를 존중하지만, 방어적일 수 있습니다
        - 근본적으로 이런 면담으로 자신의 문제가 해결될 수 있을 지 의구심을 갖고 있습니다
        - 완전히 변화를 거부하지는 않지만, 변화를 진정 원하는지 ambivalent한 태도를 보입니다.
         이 때문에 내담자 문제와 관련하여 저항을 보일 수 있습니다
        
        
        **응답 방식:**
        - 위에 명시된 내담자 문제 상황과 일치하는 현실적이고 자연스러운 반응을 보입니다
        - 이런 심리 면담에 익숙하지 않기 때문에 면담자의 말을 제대로 이해하지 못하거나 엉뚱한 이야기를 할 수 있습니다
        - 내담자 문제의 핵심 어려움에서 못 벗어나는 경향을 보입니다
        - 면담자가 제시하는 해결책이나 다른 주제에 대해서도 내담자 문제와 연관지어 반응합니다
        - 저항을 보일 때는 화제를 돌려 회피하거나, 침묵으로 일관할 수도 있습니다
        - 감정적인 순간에는 내담자 문제와 관련된 진솔함을 보입니다
        - 면담자가 자신의 문제를 너무 쉽게 보거나, 다분히 상식적인 조언을 해 주는 것에 대해 화를 내기도 합니다
        - 변화가 필요하다는 것은 인지하고 있지만 상담으로 변화가 가능하다고 생각하지 않기 때문에, 면담자에게 냉소적으로 굴 수 있습니다
        - 면담자보다 앞서 나가지 않습니다
        
        **중요**: 면담자가 session_goal 관련 질문이나 개입을 하더라도, 
        항상 위에 명시된 내담자 문제의 맥락에서 반응하고, 내담자 문제로 인한 구체적 어려움을 지속적으로 표현하세요.
        
        위에 명시된 내담자 문제, 면담자의 최근 질문과 대화 흐름을 확인하고, 
        내담자 문제에 명시된 내담자로서 일관되고 현실적인 반응을 제시하세요.
        """

        super().__init__(name=name, instruction=instruction, output_key="client_response", model=MODEL)


class SupervisorAgent(LlmAgent):
    """면담자를 지도하고 피드백을 제공하는 슈퍼바이저 에이전트"""

    def __init__(
        self,
        name: str = "Supervisor",
        session_goal: str = "",
        reference_material: str = "",
        current_turn: int = 0,
        max_interactions: int = 100,
        remaining_turns: int = 100,
        stage: str = "초기",
    ):
        instruction = f"""
        당신은 Motivational Interviewing 전문 슈퍼바이저입니다.
        
        🎯 **핵심 평가 원칙: 아래 구체적인 세션 목표 달성과 참고 자료 활용을 최우선으로 평가하세요**
        
        **세션 목표**: {session_goal}
        
        **참고 자료**:
        {reference_material}
        
        **필수 평가 방식:**
        1. **첫 번째**: 위에 명시된 세션 목표 달성 진행도를 최우선으로 평가하세요
        2. **두 번째**: 면담자가 참고 자료의 기법들을 얼마나 활용했는지 평가하세요
        3. **세 번째**: 면담자가 내담자를 세션 목표 방향으로 얼마나 효과적으로 유도했는지 평가하세요
        
        **우선 평가 기준 (중요도 순):**
        1. **세션 목표 달성 진행도** (최우선) - "{session_goal}" 달성을 위한 구체적 노력 여부
        2. **참고 자료 활용도** (필수) - 위에 제시된 기법, 연습, 개념들의 적용 여부
        3. **세션 목표 관련 질문과 개입** - "{session_goal}"과 직접 연관된 질문 사용 여부
        4. **내담자의 세션 목표 관련 반응 유도** - 목표 관련 인사이트나 변화 촉진 여부
        5. MI 정신과 기법의 적절한 사용 (기본 요건)
        6. 내담자의 변화 언어(change talk) 포착
        7. 저항에 대한 적절한 반응
        8. 내담자 중심 접근 유지
        
        **피드백 제공 방식:**
        - **개선점**: "{session_goal}" 달성을 위해 참고 자료를 어떻게 더 잘 활용할 수 있는지 구체적으로 제시
        - **놓친 기회**: 참고 자료의 어떤 기법이나 개념을 활용할 기회를 놓쳤는지 지적
        - **다음 단계**: "{session_goal}" 달성을 위한 구체적이고 실행 가능한 방향 제시
        
        ⏰ **현재 세션 진행 현황:**
        - **현재 턴**: {current_turn}/{max_interactions}
        - **남은 턴**: {remaining_turns}
        - **세션 단계**: {stage} 단계
        
        **세션 진행 단계별 접근:**
        - **초기 단계** (remaining_turns > max_interactions * 0.7): 탐색과 라포 형성에 집중
        - **중기 단계** (remaining_turns > max_interactions * 0.3): 세션 목표 관련 개입 강화
        - **후기 단계** (remaining_turns <= max_interactions * 0.3): 집중적이고 직접적인 개입 요구
        
        **💡 현재 상황에 맞는 접근:**
        - 현재 남은 턴: **{remaining_turns}턴** (전체 {max_interactions}턴 중 {current_turn}턴 진행)
        - {"🚨 마무리 단계: 세션 종료를 고려할 시점입니다" if remaining_turns <= 5 else "⏳ 충분한 시간: 서두르지 말고 세션 목표에 집중하세요"}
        
        **중요**: 남은 턴이 5턴 미만일 때만 "남은 턴이 얼마 남지 않았다"고 언급하세요. 
        현재 {remaining_turns}턴이 남았으므로 {"마무리를 고려해야 합니다" if remaining_turns <= 5 else "여유롭게 진행하세요"}.
        
        면담자가 세션 목표를 무시하고 일반적인 MI만 진행하고 있다면 강하게 지적하고, 
        참고 자료 활용을 촉구하세요. 장점보다는 세션 목표 달성을 위한 개선점에 주력하여 피드백을 제시하세요.
        
        **절대 금지**: 남은 턴이 많을 때 (5턴 초과) "효율적으로 진행", "서둘러야", "마무리" 등의 표현 사용 금지.
        {"현재 " + str(remaining_turns) + "턴이 남았으므로 서두르지 마세요." if remaining_turns > 5 else ""}
        """

        super().__init__(name=name, instruction=instruction, output_key="supervisor_feedback", model=MODEL)


class ConversationManager(BaseAgent):
    """대화 흐름을 관리하고 종료 조건을 확인하는 에이전트"""

    def __init__(self, name: str = "ConversationManager"):
        super().__init__(name=name)
        self._system_reference = None

    def set_system_reference(self, system_ref):
        """시스템 참조 설정"""
        self._system_reference = system_ref

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # 현재 턴 증가
        current_turn = ctx.session.state.get("current_turn", 0) + 1
        ctx.session.state["current_turn"] = current_turn

        # 대화 히스토리 업데이트
        conversation = ctx.session.state.get("conversation_history", [])

        # 최근 응답들을 대화에 추가
        if "therapist_response" in ctx.session.state:
            conversation.append({
                "speaker": "Therapist",
                "message": ctx.session.state["therapist_response"],
                "turn": current_turn,
            })

        if "client_response" in ctx.session.state:
            conversation.append({
                "speaker": "Client",
                "message": ctx.session.state["client_response"],
                "turn": current_turn,
            })

        if "supervisor_feedback" in ctx.session.state:
            conversation.append({
                "speaker": "Supervisor",
                "message": ctx.session.state["supervisor_feedback"],
                "turn": current_turn,
            })

        ctx.session.state["conversation_history"] = conversation

        # 진행 상황 정보 업데이트
        max_interactions = ctx.session.state.get("max_interactions", 50)  # Default fallback
        remaining_turns = max_interactions - current_turn

        # 세션 상태에 진행 정보 추가
        ctx.session.state["current_turn_info"] = {
            "current_turn": current_turn,
            "max_interactions": max_interactions,
            "remaining_turns": remaining_turns,
        }

        print(
            f"🔄 Turn {current_turn}/{max_interactions} - 대화 기록: {len(conversation)}개 (남은 턴: {remaining_turns})"
        )

        # 에이전트들에게 현재 턴 정보 업데이트
        if self._system_reference and hasattr(self._system_reference, "update_agents_with_turn_info"):
            self._system_reference.update_agents_with_turn_info(
                current_turn=current_turn, max_interactions=max_interactions, remaining_turns=remaining_turns
            )

        # 시스템 백업에 상태 저장
        if self._system_reference:
            self._system_reference.session_backup.update({
                "conversation_history": conversation.copy(),
                "current_turn": current_turn,
                "client_problem": ctx.session.state.get("client_problem", ""),
                "session_goal": ctx.session.state.get("session_goal", ""),
                "reference_material": ctx.session.state.get("reference_material", ""),
                "current_turn_info": ctx.session.state["current_turn_info"],
            })

        # 종료 조건 확인
        should_stop = False
        max_interactions = ctx.session.state.get("max_interactions", 50)  # Default fallback

        # 최대 상호작용 횟수 도달
        if current_turn >= max_interactions:
            should_stop = True
            ctx.session.state["termination_reason"] = "최대 상호작용 횟수 도달"
            print(f"🛑 최대 상호작용 도달: {current_turn}/{max_interactions}")

        # 자연스러운 종료 감지
        if not should_stop and current_turn >= 3:  # 최소 3턴 보장
            recent_responses = [
                ctx.session.state.get("therapist_response", ""),
                ctx.session.state.get("client_response", ""),
            ]

            end_phrases = [
                "오늘 면담은 이것으로 마치겠습니다",
                "면담을 마치겠습니다",
                "세션을 마치겠습니다",
                "다음에 뵙겠습니다",
            ]

            for response in recent_responses:
                for phrase in end_phrases:
                    if phrase in response:
                        should_stop = True
                        ctx.session.state["termination_reason"] = "자연스러운 대화 종료"
                        print(f"🛑 자연스러운 종료: {phrase}")
                        break
                if should_stop:
                    break

        # 루프 제어
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))


# SessionRecorder는 제거되고 MotivationalInterviewingSystem에서 직접 처리됩니다.


class MotivationalInterviewingSystem:
    """전체 Motivational Interviewing 시스템을 관리하는 클래스"""

    def __init__(self, max_interactions: int = 100):
        self.max_interactions = max_interactions
        self.session_backup = {}  # 세션 상태 백업용

    def _setup_agents(self, client_problem: str, session_goal: str, reference_material: str):
        """에이전트들을 초기화하고 연결 (실제 session 정보 포함)"""

        # 개별 에이전트 생성 (실제 session 정보 전달)
        self.therapist = TherapistAgent(session_goal=session_goal, reference_material=reference_material)
        self.client = ClientAgent(client_problem=client_problem)
        self.supervisor = SupervisorAgent(session_goal=session_goal, reference_material=reference_material)
        self.conversation_manager = ConversationManager()
        self.conversation_manager.set_system_reference(self)

        # Store base instructions for dynamic updates
        self.base_session_goal = session_goal
        self.base_reference_material = reference_material
        self.base_client_problem = client_problem

        # 한 턴의 상호작용을 위한 순차 에이전트
        self.turn_sequence = SequentialAgent(
            name="InteractionTurn", sub_agents=[self.therapist, self.client, self.supervisor, self.conversation_manager]
        )

        # 전체 시스템: LoopAgent로 반복 실행
        self.full_system = LoopAgent(
            name="MotivationalInterviewingLoop", max_iterations=self.max_interactions, sub_agents=[self.turn_sequence]
        )

    def update_agents_with_turn_info(self, current_turn: int, max_interactions: int, remaining_turns: int):
        """각 턴마다 에이전트들에게 현재 턴 정보 업데이트"""

        # Calculate session stage
        if remaining_turns > max_interactions * 0.7:
            stage = "초기"
        elif remaining_turns > max_interactions * 0.3:
            stage = "중기"
        else:
            stage = "후기"

        # Update agent instructions directly to avoid parent relationship conflicts
        self._update_therapist_instruction(current_turn, max_interactions, remaining_turns, stage)
        self._update_supervisor_instruction(current_turn, max_interactions, remaining_turns, stage)

    def _update_therapist_instruction(self, current_turn: int, max_interactions: int, remaining_turns: int, stage: str):
        """Update therapist instruction with current turn info"""
        instruction = f"""
        당신은 경험이 풍부한 Motivational Interviewing 전문가입니다.
        
        🎯 **핵심 원칙: 아래 구체적인 세션 목표와 참고 자료를 최우선으로 활용하세요**
        
        **세션 목표**: {self.base_session_goal}
        
        **참고 자료**:
        {self.base_reference_material}
        
        **필수 진행 방식:**
        1. **첫 번째**: 위에 명시된 세션 목표 달성을 최우선으로 하세요
        2. **두 번째**: 참고 자료에 제시된 구체적 기법들을 적극 활용하세요. 기법에 얽매이기보다는 자연스러운 대화 진행을 우선시하세요
        3. **세 번째**: 내담자의 문제를 세션 목표 관점에서 재구성하여 접근하세요
        
        **구체적인 활용 방법:**
        - 참고 자료에 제시된 연습, 기법, 개념들을 직접 소개하고 적용하세요
        - 세션 목표와 관련된 질문과 개입을 우선적으로 사용하세요
        - 내담자의 답변을 세션 목표 달성 방향으로 유도하세요
        - 참고 자료의 언어와 개념을 면담에서 사용하세요
                
        **기본 MI 진행 방식 (세션 목표 달성을 위해 사용):**
        1. 공감적 경청과 열린 질문을 사용합니다
        2. 내담자의 양가감정을 탐색합니다  
        3. 변화 동기를 강화합니다
        4. 내담자 중심의 접근을 유지합니다
        
        ⏰ **현재 세션 진행 현황:**
        - **현재 턴**: {current_turn}/{max_interactions}
        - **남은 턴**: {remaining_turns}
        - **세션 단계**: {stage} 단계
        
        **세션 진행 단계별 접근:**
        - **초기 단계** (remaining_turns > max_interactions * 0.7): 라포 형성과 문제 탐색
        - **중기 단계** (remaining_turns > max_interactions * 0.3): 세션 목표 관련 기법 적극 활용
        - **후기 단계** (remaining_turns <= max_interactions * 0.3): 목표 달성을 위한 집중적 개입
        
        각 단계에 맞는 속도로 진행하되, 세션 목표 달성을 최우선으로 하세요.
        
        자연스럽고 따뜻한 톤으로 작성하되, 세션 목표 달성을 위한 참고 자료 기법 적용을 반드시 포함하세요.
        
        🔚 세션 종료 조건:
        세션 목표가 달성되었다고 판단되면 "오늘 면담은 이것으로 마치겠습니다"라고 말하여 세션을 종료하세요.
        목표 달성의 기준:
        - 세션 목표에서 제시한 구체적 목표가 달성됨
        - 참고 자료의 핵심 기법이 내담자에게 전달되고 이해됨
        - 내담자가 세션 목표 관련 인사이트나 변화를 보임
        """
        self.therapist.instruction = instruction

    def _update_supervisor_instruction(
        self, current_turn: int, max_interactions: int, remaining_turns: int, stage: str
    ):
        """Update supervisor instruction with current turn info"""
        instruction = f"""
        당신은 Motivational Interviewing 전문 슈퍼바이저입니다.
        
        🎯 **핵심 평가 원칙: 아래 구체적인 세션 목표 달성과 참고 자료 활용을 최우선으로 평가하세요**
        
        **세션 목표**: {self.base_session_goal}
        
        **참고 자료**:
        {self.base_reference_material}
        
        **필수 평가 방식:**
        1. **첫 번째**: 위에 명시된 세션 목표 달성 진행도를 최우선으로 평가하세요
        2. **두 번째**: 면담자가 참고 자료의 기법들을 얼마나 활용했는지 평가하세요
        3. **세 번째**: 면담자가 내담자를 세션 목표 방향으로 얼마나 효과적으로 유도했는지 평가하세요
        
        **우선 평가 기준 (중요도 순):**
        1. **세션 목표 달성 진행도** (최우선) - "{self.base_session_goal}" 달성을 위한 구체적 노력 여부
        2. **참고 자료 활용도** (필수) - 위에 제시된 기법, 연습, 개념들의 적용 여부
        3. **세션 목표 관련 질문과 개입** - "{self.base_session_goal}"과 직접 연관된 질문 사용 여부
        4. **내담자의 세션 목표 관련 반응 유도** - 목표 관련 인사이트나 변화 촉진 여부
        5. MI 정신과 기법의 적절한 사용 (기본 요건)
        6. 내담자의 변화 언어(change talk) 포착
        7. 저항에 대한 적절한 반응
        8. 내담자 중심 접근 유지
        
        **피드백 제공 방식:**
        - **개선점**: "{self.base_session_goal}" 달성을 위해 참고 자료를 어떻게 더 잘 활용할 수 있는지 구체적으로 제시
        - **놓친 기회**: 참고 자료의 어떤 기법이나 개념을 활용할 기회를 놓쳤는지 지적
        - **다음 단계**: "{self.base_session_goal}" 달성을 위한 구체적이고 실행 가능한 방향 제시
        
        ⏰ **현재 세션 진행 현황:**
        - **현재 턴**: {current_turn}/{max_interactions}
        - **남은 턴**: {remaining_turns}
        - **세션 단계**: {stage} 단계
        
        **세션 진행 단계별 접근:**
        - **초기 단계** (remaining_turns > max_interactions * 0.7): 탐색과 라포 형성에 집중
        - **중기 단계** (remaining_turns > max_interactions * 0.3): 세션 목표 관련 개입 강화
        - **후기 단계** (remaining_turns <= max_interactions * 0.3): 집중적이고 직접적인 개입 요구
        
        **💡 현재 상황에 맞는 접근:**
        - 현재 남은 턴: **{remaining_turns}턴** (전체 {max_interactions}턴 중 {current_turn}턴 진행)
        - {"🚨 마무리 단계: 세션 종료를 고려할 시점입니다" if remaining_turns <= 5 else "⏳ 충분한 시간: 서두르지 말고 세션 목표에 집중하세요"}
        
        **중요**: 남은 턴이 5턴 미만일 때만 "남은 턴이 얼마 남지 않았다"고 언급하세요. 
        현재 {remaining_turns}턴이 남았으므로 {"마무리를 고려해야 합니다" if remaining_turns <= 5 else "여유롭게 진행하세요"}.
        
        면담자가 세션 목표를 무시하고 일반적인 MI만 진행하고 있다면 강하게 지적하고, 
        참고 자료 활용을 촉구하세요. 장점보다는 세션 목표 달성을 위한 개선점에 주력하여 피드백을 제시하세요.
        
        **절대 금지**: 남은 턴이 많을 때 (5턴 초과) "효율적으로 진행", "서둘러야", "마무리" 등의 표현 사용 금지.
        {"현재 " + str(remaining_turns) + "턴이 남았으므로 서두르지 마세요." if remaining_turns > 5 else ""}
        """
        self.supervisor.instruction = instruction

    async def run_session(self, client_problem: str, session_goal: str, reference_material: str = "") -> str:
        """Motivational Interviewing 세션을 실행"""

        if not ADK_AVAILABLE:
            raise RuntimeError("Google ADK가 설치되지 않았습니다. 'pip install google-adk'로 설치해주세요.")

        # 실제 session 정보로 agents 설정
        self._setup_agents(client_problem, session_goal, reference_material)

        try:
            # 세션 서비스 및 세션 생성
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="MotivationalInterviewing",
                user_id="user_001",
                session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

            # 초기 상태 설정
            session.state.update({
                "client_problem": client_problem,
                "session_goal": session_goal,
                "reference_material": reference_material,
                "conversation_history": [],
                "current_turn": 0,
                "max_interactions": self.max_interactions,
            })

            # Runner 생성 및 실행
            runner = Runner(
                agent=self.full_system, session_service=session_service, app_name="MotivationalInterviewing"
            )

            # 세션 시작 메시지
            initial_message = types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"새로운 Motivational Interviewing 세션을 시작합니다. 내담자 문제: {client_problem}"
                    )
                ],
            )

            print(f"🚀 세션 시작: max_interactions={self.max_interactions}")

            # 세션 실행 - LoopAgent가 자동으로 반복 실행
            events = runner.run(user_id="user_001", session_id=session.id, new_message=initial_message)

            # 이벤트 처리 (간소화)
            try:
                async for event in events:
                    if hasattr(event, "actions") and event.actions and event.actions.escalate:
                        print("🏁 세션 종료 신호 감지")
                        break
            except TypeError:
                # 동기 iterator인 경우
                for event in events:
                    if hasattr(event, "actions") and event.actions and event.actions.escalate:
                        print("🏁 세션 종료 신호 감지")
                        break

            # 세션 기록 저장
            output_files = await self._save_session_record(session)
            return output_files

        except Exception as e:
            print(f"세션 실행 중 오류 발생: {e}")
            raise e

    async def _save_session_record(self, session) -> Dict[str, str]:
        """세션 기록을 파일로 저장"""

        # 디버깅: 세션 상태 출력
        # print("📊 세션 저장 시 상태 확인:")
        # print(f"   세션 상태 키들: {list(session.state.keys())}")
        # print(f"   conversation_history: {session.state.get('conversation_history', [])}")
        # print(f"   current_turn: {session.state.get('current_turn', 0)}")
        # print(f"   백업 상태: {self.session_backup}")

        # 백업된 데이터 사용 (세션 상태가 비어있을 경우)
        conversation_history = session.state.get("conversation_history", [])
        if not conversation_history and self.session_backup.get("conversation_history"):
            print("⚠️ 세션 상태가 비어있음. 백업 데이터 사용.")
            conversation_history = self.session_backup["conversation_history"]

        # 세션 데이터 수집
        session_data = {
            "session_info": {
                "timestamp": datetime.now().isoformat(),
                "client_problem": session.state.get("client_problem", "")
                or self.session_backup.get("client_problem", ""),
                "session_goal": session.state.get("session_goal", "") or self.session_backup.get("session_goal", ""),
                "reference_material": session.state.get("reference_material", "")
                or self.session_backup.get("reference_material", ""),
                "total_turns": session.state.get("current_turn", 0) or self.session_backup.get("current_turn", 0),
                "termination_reason": session.state.get("termination_reason", "세션 완료"),
            },
            "conversation": conversation_history,
        }

        # 출력 디렉토리 생성
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 전체 세션 기록 (마크다운)
        full_filename = f"mi_session_{timestamp}.md"
        full_filepath = output_dir / full_filename
        full_markdown_content = self._generate_markdown(session_data)

        with open(full_filepath, "w", encoding="utf-8") as f:
            f.write(full_markdown_content)

        # 치료사-내담자 대화만 저장 (마크다운)
        dialogue_filename = f"mi_dialogue_{timestamp}.md"
        dialogue_filepath = output_dir / dialogue_filename
        dialogue_markdown_content = self._generate_dialogue_markdown(session_data)

        with open(dialogue_filepath, "w", encoding="utf-8") as f:
            f.write(dialogue_markdown_content)

        return {"full_session": str(full_filepath), "dialogue_only": str(dialogue_filepath)}

    def _generate_markdown(self, session_data: Dict[str, Any]) -> str:
        """세션 데이터를 마크다운 형식으로 변환"""

        content = f"""# Motivational Interviewing 세션 기록

## 세션 정보
- **일시**: {session_data["session_info"]["timestamp"]}
- **내담자 문제**: {session_data["session_info"]["client_problem"]}
- **세션 목표**: {session_data["session_info"]["session_goal"]}
- **참고 자료**: {session_data["session_info"]["reference_material"]}
- **총 상호작용 횟수**: {session_data["session_info"]["total_turns"]}
- **종료 사유**: {session_data["session_info"]["termination_reason"]}

## 면담 기록

"""

        if session_data["conversation"]:
            current_turn = 0
            for entry in session_data["conversation"]:
                if entry["turn"] != current_turn:
                    current_turn = entry["turn"]
                    content += f"\n### Turn {current_turn}\n\n"

                speaker_emoji = {"Therapist": "🩺", "Client": "😊", "Supervisor": "👨‍🏫"}

                content += f"**{speaker_emoji.get(entry['speaker'], '🔹')} {entry['speaker']}**: {entry['message']}\n\n"
        else:
            content += "면담 기록이 없습니다.\n\n"

        content += "\n---\n*이 기록은 ADK Multi-Agent System으로 생성되었습니다.*"

        return content

    def _generate_dialogue_markdown(self, session_data: Dict[str, Any]) -> str:
        """치료사-내담자 대화만 마크다운 형식으로 변환"""

        content = f"""# Motivational Interviewing 대화 기록

## 세션 정보
- **일시**: {session_data["session_info"]["timestamp"]}
- **내담자 문제**: {session_data["session_info"]["client_problem"]}
- **세션 목표**: {session_data["session_info"]["session_goal"]}
- **총 상호작용 횟수**: {session_data["session_info"]["total_turns"]}

## 치료사-내담자 대화

"""

        if session_data["conversation"]:
            current_turn = 0
            for entry in session_data["conversation"]:
                # 치료사와 내담자 대화만 포함
                if entry["speaker"] in ["Therapist", "Client"]:
                    if entry["turn"] != current_turn:
                        current_turn = entry["turn"]
                        content += f"\n### Turn {current_turn}\n\n"

                    speaker_emoji = {"Therapist": "🩺", "Client": "😊"}
                    content += (
                        f"**{speaker_emoji.get(entry['speaker'], '🔹')} {entry['speaker']}**: {entry['message']}\n\n"
                    )
        else:
            content += "대화 기록이 없습니다.\n\n"

        content += "\n---\n*이 기록은 ADK Multi-Agent System으로 생성되었습니다.*"

        return content


# 편의를 위한 함수들
async def create_mi_session(
    client_problem: str, session_goal: str, reference_material: str = "", max_interactions: int = 100
) -> Dict[str, str]:
    """새로운 MI 세션을 생성하고 실행"""

    system = MotivationalInterviewingSystem(max_interactions=max_interactions)
    output_files = await system.run_session(
        client_problem=client_problem, session_goal=session_goal, reference_material=reference_material
    )

    return output_files


def run_mi_session_sync(
    client_problem: str, session_goal: str, reference_material: str = "", max_interactions: int = 100
) -> Dict[str, str]:
    """동기 방식으로 MI 세션을 실행"""

    return asyncio.run(
        create_mi_session(
            client_problem=client_problem,
            session_goal=session_goal,
            reference_material=reference_material,
            max_interactions=max_interactions,
        )
    )


# 도구 정의
def exit_conversation(tool_context: ToolContext):
    """대화가 자연스럽게 종료되었을 때 호출하는 도구"""
    print(f"  [Tool Call] exit_conversation triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {"status": "conversation_ended", "reason": "natural_completion"}


if __name__ == "__main__":
    # 예시 실행
    example_client_problem = """
    35세 직장인으로 최근 스트레스로 인한 과음 문제가 심해지고 있습니다.
    주 4-5회 정도 퇴근 후 혼자 술을 마시며, 양도 점점 늘어나고 있습니다.
    가족들이 걱정을 표하지만 본인은 스트레스 해소를 위해 필요하다고 생각합니다.
    """

    example_session_goal = """
    내담자가 현재 음주 패턴에 대해 성찰하고, 
    건강한 스트레스 관리 방법에 대한 동기를 발견하도록 돕는다.
    """

    example_reference_material = """
    MI 기본 원칙: OARS (Open questions, Affirmations, Reflections, Summaries)
    변화 언어 강화, 저항 최소화, 내담자 자율성 존중
    """

    print("Motivational Interviewing 세션을 시작합니다...")
    output_files = run_mi_session_sync(
        client_problem=example_client_problem,
        session_goal=example_session_goal,
        reference_material=example_reference_material,
        max_interactions=10,  # 예시를 위해 짧게 설정
    )

    print("세션이 완료되었습니다.")
    print(f"전체 세션 기록: {output_files['full_session']}")
    print(f"치료사-내담자 대화: {output_files['dialogue_only']}")
