연구의 목표가 뭘까?

궁극적인 목표: 실제로 client와 Motivational interview를 진행하는 LLM-based therapist의 개발

세부과제

1. Motivational interview를 하는 small LLM의 training

   1-1. training을 위한 synthetic dataset 마련

​      1-1-1. 좀더 현실감있는 synthetic dataset를 만들어내기 위한 flow 설계

​         1-1-1-1. 자신만의 문제와 독특한 인격을 지닌 client - virtual human with realistic psychology의 개발

​         1-1-1-2. MI의 rule을 최대한 따르며, 면담의 진행상황과 스스로의 performance를 reflection할 수 있는 therapist 개발

   2-1. training 준비 단계

​      2-1-1. synthetic interview에서 training을 위한 data formatting - prompt/response 형태로 바꿈

​      2-1-2. GRPO training을 위해 각 prompt/response에 대해 reward scoring을 하는 flow 설계

  3-1. 실제 training

​       3-1-1. Hardware, software 마련

  4-1. Trained 된 모델에 대한 evaluation

​       4-1-1. train되지 않은 basic local LLM model에 의한 면담과 비교 - 앞서 마련해놓은 reward scoring function으로 평가

​       4-1-2. ChatGPT와 같은 large LLM의 면담과 비교

​       4-1-3. MI 전문가(human)가 직접 virtual therapist의 반응 평가 - manual scoring or A/B testing

​       . 

2. Training된 LLM이 치료현장에서 순발력있게 대응하도록 flow 설계

   2-1. 면담의 질을 평가하고 개선점을 제시해주는 supervisor agent의 개발

   2-2. client의 반응과 변화 정도에 적합한 goal과 strategy를 수립하는 planner agent의 개발

   2-3. 현장과 가장 흡사한 상황에서 단일 session의 simulation이 아니라, multiple session을 simulatioN하여 client에게 얼마나 도움이 되는 지 평가

이렇게 보면 굉장히 방대한 작업이거든.....

그런데 우리는 synthetic dataset을 마련하는 과정에서 아직 벗어나지 못했어.

내가 말했듯이. synthetic dataset을 준비하는 과정은 다음과 같이 두 가지로 구분할 수 있어

1. LLM에게 multiple turn으로 진행되는 session 전체를 한번에 simulation해달라고 하는 방법 (네 방법)
2. client agent, therapist agent, supervisor agent를 따로따로 나누어, 한번에 발언 하나씩만 simulation하는 방법 (아빠의 방법)

효율성 측면에서 네 방법인 첫번째가 훨씬 유리해. 한번의 session이 약 30번의 turn으로 이루어진다고 하면, 아빠 방식으로는 90번 LLM을 call 해야 해.

게다가 이렇게 call 할 때마다 과거 기록을 모두 prompt에 넣기 때문에 token 사용량이 기하급수적으로 늘어나.

반면 네가 client에게 성격이나 치료 진전에 대한 반응을 넣어서 현실감있는 simulation을 하고자 한다면, 아빠 방식으로 할 수 밖에 없어.

아빠 생각에는 virtual client을 만드는데 그렇게 정력을 투자할 필요가 있을까 해.

어차피 목적이 small LLM을 training하는 거니까. 그렇게 현실적인 client가 아니라도 괜찮으리라 생각해

오히려 두번째 목표인 training된 LLM을 평가할 때는 좀더 현실적인 virtual client가 필요할 지도 모르겠어

인격을 지닌 virtual client를 만드는 목적은 수련과정에 있는 사람(의사 혹은 심리사)을 training 할 때 필요한 거야. 진짜 환자에게 사용할 때는 그보다는 인격을 갖춘 virtual therapist가 필요한 거겠지.