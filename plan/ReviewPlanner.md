planner.py에는 두가지 agent 즉 reviewer agent와 planner agent가 정의된다.



Reviewer agent

마지막 interview에서 이루어졌던 interview material (output directory에 저장된 markdown file)을 철저히 읽고, 다음에 대해 점검한다.

1. therapist가 성취하려고 했던 목표와 이를 위해 어떤 식으로 접근헀는지
2. 그 목표가 얼마나 달성되었는지
3. 목표가 달성되지 못한 부분이 있다면, 문제점과 그 개선점은 어떤 것인지 제안.
4. 이를 통해 내담자의 문제 해결에 도움이 되었는지, 만약 그렇지 않다면 목표를 수정할 필요가 있는지
5. 이러한 검토 결과를 markdown file로 출력한다.



Output directory에서 mi_dialogue_{timestamp}.md라고 되어있는 file을 읽으며, timestamp가 가장 최근인 것을 읽어들인다.



Planner agent

지금까지 이루어졌던 일련의 interview에 대해 reviewer agent가 작성한 review material을 모두 검토하고 다음에 대해 점검한다.

1. 애초에 내담자가 상담하고자 했던 문제가 무엇이었는지
2. motivational interviewing이라는 전체적 관점에서 내담자의 심리상태는 얼마나 진전되었는지
3. 이런 진전을 통해 내담자의 문제 해결 가능성이 얼마나 높아졌는지
4. 다음 session에는 어떤 목표를 세우고, 어떤 reference material을 이용하여 접근할 것인지
5. Motivational interview가 모두 12 session으로 이루어지기 때문에, 현재 session number를 고려하여 목표를 세운다.



