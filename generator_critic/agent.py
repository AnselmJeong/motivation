"""
Motivational Interviewing Multi-Agent System using Google ADK

이 시스템은 세 가지 에이전트로 구성됩니다:
1. TherapistAgent: Motivational Interview를 주도하는 면담자
2. ClientAgent: 문제를 가진 내담자 역할 시뮬레이션
3. SupervisorAgent: 면담자에게 피드백을 제공하는 슈퍼바이저

면담자 -> 내담자 -> 슈퍼바이저 순으로 진행되며, 최대 100회 상호작용까지 가능합니다.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


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

    def __init__(self, name: str = "Therapist"):
        instruction = """
        당신은 경험이 풍부한 Motivational Interviewing 전문가입니다.
        
        역할:
        - 세션 목표를 달성하기 위해 체계적으로 면담을 진행합니다
        - 제공된 전문 자료를 참고하여 효과적인 질문을 합니다
        - 내담자의 답변에 섬세하게 반응하고 유연하게 대응합니다
        - 슈퍼바이저의 피드백을 적극 수용하여 면담을 개선합니다
        
        진행 방식:
        1. 공감적 경청과 열린 질문을 사용합니다
        2. 내담자의 양가감정을 탐색합니다
        3. 변화 동기를 강화합니다
        4. 내담자 중심의 접근을 유지합니다
        
        세션 상태 정보는 context에서 확인하세요. 내담자의 문제, 세션 목표, 참고 자료, 
        대화 진행상황, 슈퍼바이저 피드백을 모두 고려하여 다음 질문이나 개입을 제시하세요.
        자연스럽고 따뜻한 톤으로 작성하세요.
        """

        super().__init__(name=name, instruction=instruction, output_key="therapist_response", model="gemini-2.5-flash")


class ClientAgent(LlmAgent):
    """내담자 역할을 시뮬레이션하는 에이전트"""

    def __init__(self, name: str = "Client"):
        instruction = """
        당신은 내담자 역할을 하는 에이전트입니다. 세션 context에서 내담자의 문제를 확인하고,
        그 문제로 고민하고 있는 내담자로서 반응하세요.
        
        특성:
        - 변화에 대해 양가감정(ambivalent)을 가지고 있습니다
        - 자신의 생각과 감정을 표현하는 데 어려움이 있습니다
        - 면담자의 리드에 따라 수동적으로 반응합니다
        - 솔직하지만 방어적일 수 있습니다
        - 완전히 변화를 거부하지는 않지만 저항을 보일 수 있습니다
        
        응답 방식:
        - 현실적이고 자연스러운 반응을 보입니다
        - 때로는 회피하거나 주제를 돌리기도 합니다
        - 감정적인 순간에는 진솔함을 보입니다
        - 면담자보다 앞서 나가지 않습니다
        
        context에서 면담자의 최근 질문과 대화 흐름을 확인하고, 
        내담자로서 자연스럽고 현실적인 반응을 제시하세요.
        """

        super().__init__(name=name, instruction=instruction, output_key="client_response", model="gemini-2.5-flash")


class SupervisorAgent(LlmAgent):
    """면담자를 지도하고 피드백을 제공하는 슈퍼바이저 에이전트"""

    def __init__(self, name: str = "Supervisor"):
        instruction = """
        당신은 Motivational Interviewing 전문 슈퍼바이저입니다.
        
        역할:
        - 면담자의 개입을 실시간으로 평가합니다
        - 놓친 기회나 개선점을 지적합니다
        - 구체적이고 실행 가능한 피드백을 제공합니다
        - 앞으로의 방향성을 제시합니다
        
        평가 기준:
        1. MI 정신과 기법의 적절한 사용
        2. 내담자의 변화 언어(change talk) 포착
        3. 저항에 대한 적절한 반응
        4. 세션 목표 달성을 위한 진행
        5. 내담자 중심 접근 유지
        
        context에서 세션 목표, 면담자의 최근 개입, 내담자 반응, 전체 대화 흐름을 확인하세요.
        
        피드백 형식:
        1. 잘한 점: [구체적인 칭찬]
        2. 개선점: [구체적인 개선 사항]
        3. 제안: [다음에 시도할 수 있는 구체적인 질문이나 기법]
        4. 방향성: [앞으로의 진행 방향]
        
        건설적이고 격려적인 톤으로 피드백을 제시하세요.
        """

        super().__init__(name=name, instruction=instruction, output_key="supervisor_feedback", model="gemini-2.5-flash")


class ConversationManager(BaseAgent):
    """대화 흐름을 관리하고 종료 조건을 확인하는 에이전트"""

    def __init__(self, name: str = "ConversationManager"):
        super().__init__(name=name)

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
        print(f"🔄 Turn {current_turn} - 대화 기록: {len(conversation)}개")

        # 종료 조건 확인
        should_stop = False
        max_interactions = ctx.session.state.get("max_interactions", 100)

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

            end_phrases = ["오늘은 여기까지", "세션을 마무리", "다음에 뵙겠습니다", "감사합니다"]

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
        self._setup_agents()

    def _setup_agents(self):
        """에이전트들을 초기화하고 연결"""

        # 개별 에이전트 생성
        self.therapist = TherapistAgent()
        self.client = ClientAgent()
        self.supervisor = SupervisorAgent()
        self.conversation_manager = ConversationManager()

        # 한 턴의 상호작용을 위한 순차 에이전트
        self.turn_sequence = SequentialAgent(
            name="InteractionTurn", sub_agents=[self.therapist, self.client, self.supervisor, self.conversation_manager]
        )

        # 전체 시스템: LoopAgent로 반복 실행
        self.full_system = LoopAgent(
            name="MotivationalInterviewingLoop", max_iterations=self.max_interactions, sub_agents=[self.turn_sequence]
        )

    async def run_session(self, client_problem: str, session_goal: str, reference_material: str = "") -> str:
        """Motivational Interviewing 세션을 실행"""

        if not ADK_AVAILABLE:
            print("Google ADK를 사용할 수 없습니다. 모의 세션을 실행합니다.")
            return await self._run_mock_session(client_problem, session_goal, reference_material)

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
            runner = Runner(agent=self.full_system, session_service=session_service, app_name="MotivationalInterviewing")

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
            output_file = await self._save_session_record(session)
            return output_file

        except Exception as e:
            print(f"세션 실행 중 오류 발생: {e}")
            print("모의 세션으로 대체합니다.")
            return await self._run_mock_session(client_problem, session_goal, reference_material)

    async def _run_mock_session(self, client_problem: str, session_goal: str, reference_material: str) -> str:
        """Google ADK를 사용할 수 없을 때 실행되는 모의 세션"""

        # 모의 대화 데이터 생성
        mock_conversation = [
            {
                "speaker": "Therapist",
                "message": f"안녕하세요. 오늘 어떤 일로 오셨나요? 혹시 {client_problem.split('.')[0]}와 관련된 문제이신가요?",
                "turn": 1,
            },
            {"speaker": "Client", "message": "네, 맞습니다. 요즘 이 문제 때문에 많이 힘들어하고 있어요.", "turn": 1},
            {
                "speaker": "Supervisor",
                "message": "잘한 점: 내담자의 문제를 즉시 인지하고 공감적으로 접근했습니다. 개선점: 좀 더 구체적인 질문으로 문제의 깊이를 탐색해보세요.",
                "turn": 1,
            },
            {
                "speaker": "Therapist",
                "message": "그렇군요. 이 문제가 일상생활에 어떤 영향을 미치고 있는지 좀 더 자세히 말씀해주실 수 있나요?",
                "turn": 2,
            },
            {
                "speaker": "Client",
                "message": "가족들과의 관계도 어려워지고, 집중하기도 힘들어서 일상이 많이 힘들어졌어요.",
                "turn": 2,
            },
            {
                "speaker": "Supervisor",
                "message": "좋습니다. 내담자가 구체적인 영향을 말하도록 유도했습니다. 이제 변화에 대한 동기를 탐색해보세요.",
                "turn": 2,
            },
        ]

        # 모의 세션 데이터
        session_data = {
            "session_info": {
                "timestamp": datetime.now().isoformat(),
                "client_problem": client_problem,
                "session_goal": session_goal,
                "reference_material": reference_material,
                "total_turns": 2,
                "termination_reason": "모의 세션 완료",
            },
            "conversation": mock_conversation,
        }

        # 파일 저장
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mi_session_mock_{timestamp}.md"
        filepath = output_dir / filename

        markdown_content = self._generate_markdown(session_data)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✅ 모의 세션이 {filepath}에 저장되었습니다.")
        return str(filepath)

    async def _save_session_record(self, session) -> str:
        """세션 기록을 파일로 저장"""

        # 디버깅: 세션 상태 출력
        print(f"📊 세션 저장 시 상태 확인:")
        print(f"   세션 상태 키들: {list(session.state.keys())}")
        print(f"   conversation_history: {session.state.get('conversation_history', [])}")
        print(f"   current_turn: {session.state.get('current_turn', 0)}")

        # 세션 데이터 수집
        session_data = {
            "session_info": {
                "timestamp": datetime.now().isoformat(),
                "client_problem": session.state.get("client_problem", ""),
                "session_goal": session.state.get("session_goal", ""),
                "reference_material": session.state.get("reference_material", ""),
                "total_turns": session.state.get("current_turn", 0),
                "termination_reason": session.state.get("termination_reason", "세션 완료"),
            },
            "conversation": session.state.get("conversation_history", []),
        }

        # 마크다운 형식으로 저장
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mi_session_{timestamp}.md"
        filepath = output_dir / filename

        markdown_content = self._generate_markdown(session_data)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return str(filepath)

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


# 편의를 위한 함수들
async def create_mi_session(
    client_problem: str, session_goal: str, reference_material: str = "", max_interactions: int = 100
) -> str:
    """새로운 MI 세션을 생성하고 실행"""

    system = MotivationalInterviewingSystem(max_interactions=max_interactions)
    output_file = await system.run_session(
        client_problem=client_problem, session_goal=session_goal, reference_material=reference_material
    )

    return output_file


def run_mi_session_sync(
    client_problem: str, session_goal: str, reference_material: str = "", max_interactions: int = 100
) -> str:
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
    output_file = run_mi_session_sync(
        client_problem=example_client_problem,
        session_goal=example_session_goal,
        reference_material=example_reference_material,
        max_interactions=10,  # 예시를 위해 짧게 설정
    )

    print(f"세션이 완료되었습니다. 결과: {output_file}")
