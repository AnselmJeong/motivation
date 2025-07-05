Motivational interview의 가상 면담 기록을 만들고자 한다.

진행하기 전에 내담자(client)가 어떤 문제를 지니고 있느지에 대해 간략한 설명이 주어질 것이다.

이에 더하여 이번 session에 어떤 목표를 달성하고자 하는지와 그 목표를 달성하기 위해 면담자가 참고할 수 있는 motivational interview 전문적 자료가 주어질 것이다.



1) 면담자 agent

면담자(therapist) agent는 1) session에서 달성해야 할 목표를 위해 2) 주어진 자료를 참고하여, motivational interview라는 큰 틀의 범위 안에서 client agent와 대화를 이어나간다. 혼자서 독단적으로 인터뷰를 이끌어가는 것이 아니라, 내담자의 답변에 섬세하게 반응하여 유연하고 자연스레 진행해야 한다. 또한 슈퍼바이저 agent가 그때그때 개선점에 대해 알려주면, 이를 감안하여 좀더 효과적이고 원할하며, session의 목표를 달성하는데 좀더 다가가는 인터뷰가 되도록 애쓴다.



2. 내담자 agent

   내담자(client) agent는 진행 전에 주어진 문제로 고민하고 있는 환자의 역할을 simulation한다. 면담자 agent보다 미리 앞서나가선 안 되며, 일단 수동적 위치에서 면담자의 리드에 따라 맞춰나간다. 내담자는 자신의 생각과 감정을 솔직히 표현하는데 어려움을 갖고 있기 때문에, 면담자가 섬세하게 이끌어주어야 그에 맞춰나갈 수 있다. 다시한번 강조하지만, 원할한 인터뷰 기록을 만들기 위해 내담자가 애써서는 안 된다. 이는 면담자의 몫이다. 가장 현실적이고, 변하려는 의지가 없는 것은 아니지만 ambivalent하고 자꾸 유혹에 지고마는 보편적인 환자의 모습을 simulation 할 수 있어야 한다.

3. 슈퍼바이저 agent

   슈퍼바이저(supervisor) agent는 면담자를 지도, 감독하는 역할을 한다. 실시간으로 이루어지는 면담자와 내담자의 대화 내용에 대해 면담자가 놓친 부분이나 실수한 부분, 좀더 개선할 수 있는 부분에 대해 feedback을 준다. 또한 앞으로 어떤 내용에 초점을 맞출 것인지 코치할 수도 있다. 



이들 세명의 agent가 simulated interview flow를 만들어나간다. 모든 agent는 전체 면담 기록(shared session state)에 접근할 수 있으며, 면담자 -> 내담자 -> 슈퍼바이저 순으로 하나의 turn을 이루어 각자의 발언을 면담 기록에 첨가해 나간다. shared session state는 대화에서 오고간 모든 것을 기록하며, 마지막에는 sesstion state를 text file에 저장한다.

turn 횟수의 제한은 없지만, 시간 제한 상 한 session 당 50회 내로 제한한다.



일단 이러한 multi-agent loop를 가능하게 하는 python script를 만들도록 하여라. 

사용하는 tool은 google agent development kit (https://google.github.io/adk-docs/)이며

아래 기술된 바와 같이 Review/Critique Pattern과 Iterative Refinement Pattern의 개념을 빌어 script를 만들도록 하여라. 



### Review/Critique Pattern (Generator-Critic)[¶](https://google.github.io/adk-docs/agents/multi-agents/#reviewcritique-pattern-generator-critic)

- **Structure:** Typically involves two agents within a [`SequentialAgent`](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/): a Generator and a Critic/Reviewer.
- **Goal:** Improve the quality or validity of generated output by having a dedicated agent review it.
- ADK Primitives Used:
  - **Workflow:** `SequentialAgent` ensures generation happens before review.
  - **Communication:** **Shared Session State** (Generator uses `output_key` to save output; Reviewer reads that state key). The Reviewer might save its feedback to another state key for subsequent steps.

[Python](https://google.github.io/adk-docs/agents/multi-agents/#python_11)[Java](https://google.github.io/adk-docs/agents/multi-agents/#java_11)

```
# Conceptual Code: Generator-Critic
from google.adk.agents import SequentialAgent, LlmAgent

generator = LlmAgent(
    name="DraftWriter",
    instruction="Write a short paragraph about subject X.",
    output_key="draft_text"
)

reviewer = LlmAgent(
    name="FactChecker",
    instruction="Review the text in state key 'draft_text' for factual accuracy. Output 'valid' or 'invalid' with reasons.",
    output_key="review_status"
)

# Optional: Further steps based on review_status

review_pipeline = SequentialAgent(
    name="WriteAndReview",
    sub_agents=[generator, reviewer]
)
# generator runs -> saves draft to state['draft_text']
# reviewer runs -> reads state['draft_text'], saves status to state['review_status']
```

### Iterative Refinement Pattern[¶](https://google.github.io/adk-docs/agents/multi-agents/#iterative-refinement-pattern)

- **Structure:** Uses a [`LoopAgent`](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/) containing one or more agents that work on a task over multiple iterations.
- **Goal:** Progressively improve a result (e.g., code, text, plan) stored in the session state until a quality threshold is met or a maximum number of iterations is reached.
- ADK Primitives Used:
  - **Workflow:** `LoopAgent` manages the repetition.
  - **Communication:** **Shared Session State** is essential for agents to read the previous iteration's output and save the refined version.
  - **Termination:** The loop typically ends based on `max_iterations` or a dedicated checking agent setting `escalate=True` in the `Event Actions` when the result is satisfactory.

[Python](https://google.github.io/adk-docs/agents/multi-agents/#python_12)[Java](https://google.github.io/adk-docs/agents/multi-agents/#java_12)

```
# Conceptual Code: Iterative Code Refinement
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator

# Agent to generate/refine code based on state['current_code'] and state['requirements']
code_refiner = LlmAgent(
    name="CodeRefiner",
    instruction="Read state['current_code'] (if exists) and state['requirements']. Generate/refine Python code to meet requirements. Save to state['current_code'].",
    output_key="current_code" # Overwrites previous code in state
)

# Agent to check if the code meets quality standards
quality_checker = LlmAgent(
    name="QualityChecker",
    instruction="Evaluate the code in state['current_code'] against state['requirements']. Output 'pass' or 'fail'.",
    output_key="quality_status"
)

# Custom agent to check the status and escalate if 'pass'
class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("quality_status", "fail")
        should_stop = (status == "pass")
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))

refinement_loop = LoopAgent(
    name="CodeRefinementLoop",
    max_iterations=5,
    sub_agents=[code_refiner, quality_checker, CheckStatusAndEscalate(name="StopChecker")]
)
# Loop runs: Refiner -> Checker -> StopChecker
# State['current_code'] is updated each iteration.
# Loop stops if QualityChecker outputs 'pass' (leading to StopChecker escalating) or after 5 iterations.
```