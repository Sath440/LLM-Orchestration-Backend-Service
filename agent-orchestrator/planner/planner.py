import re
from typing import List


def decompose_task(description: str) -> List[str]:
    sentences = re.split(r"[\n\.]+", description)
    steps = [sentence.strip() for sentence in sentences if sentence.strip()]
    return steps or [description.strip()]


def assign_agent(step: str) -> str:
    lowered = step.lower()
    if any(keyword in lowered for keyword in ["research", "analyze", "summarize"]):
        return "research"
    if any(keyword in lowered for keyword in ["deploy", "implement", "build", "code"]):
        return "builder"
    return "general"
