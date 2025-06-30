"""
Motivational Interviewing Multi-Agent System

Google ADK를 사용한 MI 가상 면담 시스템의 메인 패키지입니다.
"""

from . import agent

# 주요 클래스와 함수들을 패키지 레벨에서 직접 접근 가능하도록 export
from .agent import (
    # 메인 시스템
    MotivationalInterviewingSystem,
    # 개별 에이전트들
    TherapistAgent,
    ClientAgent,
    SupervisorAgent,
    ConversationManager,
    # 편의 함수들
    create_mi_session,
    run_mi_session_sync,
)

__version__ = "0.1.0"
__author__ = "Your Name"
__description__ = "Motivational Interviewing Multi-Agent System using Google ADK"

__all__ = [
    "MotivationalInterviewingSystem",
    "TherapistAgent",
    "ClientAgent",
    "SupervisorAgent",
    "ConversationManager",
    "create_mi_session",
    "run_mi_session_sync",
]
