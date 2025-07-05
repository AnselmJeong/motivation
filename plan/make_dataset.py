import json
from pathlib import Path


def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        # 파일 전체를 읽어서 단일 JSON 객체로 파싱
        data = json.load(f)
        # 단일 객체인 경우 리스트로 감싸서 반환
        if isinstance(data, dict):
            return [data]
        # 이미 리스트인 경우 그대로 반환
        return data


def prepare_single_examples(session):
    """Phase 1: Turn-by-turn 발화 예측용 예시 생성"""
    examples = []
    context = []
    for i, turn in enumerate(session["dialogue"]):
        role, content = turn["role"], turn["content"]
        context.append(f"{role}: {content}")
        if role == "therapist" and i >= 2:
            input_text = f"[세션 목표: {session['session_goal']}]\n"
            input_text += "\n".join(context[:-1]) + "\ntherapist:"
            output_text = content
            examples.append({"input": input_text.strip(), "output": output_text.strip()})
    return examples


def prepare_arc_example(session):
    """Phase 2: ARC 계획 기반 발화 예측"""
    therapist_turns = [t for t in session["dialogue"] if t["role"] == "therapist"]
    if not therapist_turns:
        return None
    first_turn = therapist_turns[0]
    arc_plan_str = "\n".join(f"Session {p['session_id']}: {p['goal']}" for p in session["arc_plan"])
    input_text = f"[ARC Plan]\n{arc_plan_str}\n\n"
    input_text += f"[Client Profile]\n{json.dumps(session['client_profile'], ensure_ascii=False)}\n\n"
    input_text += f"[Session Goal]\n{session['session_goal']}\n\n"
    input_text += (
        "[Context]\n" + "\n".join(f"{t['role']}: {t['content']}" for t in session["dialogue"][:3]) + "\ntherapist:"
    )
    return {"input": input_text.strip(), "output": first_turn["content"].strip()}


def main():
    raw_data = load_data("test_arc_dataset.jsonl")
    single_out = []
    arc_out = []

    for session in raw_data:
        single_out.extend(prepare_single_examples(session))
        arc_ex = prepare_arc_example(session)
        if arc_ex:
            arc_out.append(arc_ex)

    Path("output_datasets").mkdir(exist_ok=True)

    with open("output_datasets/single_train.jsonl", "w") as f:
        for item in single_out:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open("output_datasets/arc_train.jsonl", "w") as f:
        for item in arc_out:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
