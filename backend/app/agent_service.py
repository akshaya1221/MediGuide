import json
import os

from .config import settings
from .document_processing import chunk_text, heuristic_medications
from .schemas import AgentAnalysis, AgentCitation, AgentFollowUp, AgentMedication

SAFETY_RULES = """MediGuide explains only what appears in the supplied record. It must not diagnose,
prescribe, change a dosage, infer drug interactions, or claim that a result is normal or abnormal unless
the source explicitly states that interpretation. Unclear medication details require professional confirmation.
Urgent symptoms are outside this document-summary workflow and should be directed to local emergency care."""


def local_analysis(text: str) -> AgentAnalysis:
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 5]
    summary_lines = lines[:5]
    medications = [AgentMedication(**item) for item in heuristic_medications(text)]
    followups: list[AgentFollowUp] = []
    for line in lines:
        lowered = line.lower()
        if any(term in lowered for term in ("follow up", "follow-up", "review after", "return after", "repeat test")):
            followups.append(AgentFollowUp(instruction=line[:500], source_text=line[:500]))
    questions = ["Which findings in this record need attention at my next visit?"]
    if medications:
        questions.append("Can you confirm each medicine, dose, timing and duration shown here?")
    if followups:
        questions.append("What should I do before the listed follow-up?")
    return AgentAnalysis(
        simple_summary=" ".join(summary_lines)[:1600] or "No readable medical text was found.",
        important_points=summary_lines[:6],
        cautions=["This automated summary may miss context. Compare it with the original record and confirm medical decisions with a qualified professional."],
        medications=medications,
        followups=followups[:10],
        consultation_questions=questions,
        citations=[AgentCitation(chunk=1, quote=(lines[0][:220] if lines else "No readable text"))],
    )


async def analyze_record(text: str, doc_type: str) -> tuple[AgentAnalysis, str]:
    if not settings.openai_api_key:
        return local_analysis(text), "local-safe-fallback"

    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    from agents import Agent, Runner, function_tool

    @function_tool
    def get_mediguide_safety_boundaries() -> str:
        """Return the non-negotiable medical safety limits for the patient explanation."""
        return SAFETY_RULES

    chunks = chunk_text(text)[:18]
    source = "\n\n".join(f"[CHUNK {index}]\n{chunk}" for index, chunk in enumerate(chunks, 1))
    agent = Agent(
        name="MediGuide record coordinator",
        model=settings.openai_model,
        output_type=AgentAnalysis,
        tools=[get_mediguide_safety_boundaries],
        instructions=(
            "You simplify a patient's own uploaded medical record. First call the safety-boundaries tool. "
            "Return a conservative, plain-language explanation grounded only in the numbered chunks. "
            "Every important statement must have a short exact source quote and chunk number. "
            "Extract follow-ups only when explicitly stated. Never invent a due date. "
            "Copy medication names, dosage and timing exactly; mark each for confirmation. "
            "Create practical questions for a clinician. Avoid diagnoses and treatment recommendations."
        ),
    )
    prompt = f"Document type: {doc_type}\n\nSOURCE RECORD:\n{source}"
    result = await Runner.run(agent, prompt, max_turns=5)
    output = result.final_output
    if not isinstance(output, AgentAnalysis):
        output = AgentAnalysis.model_validate(output)
    return output, settings.openai_model


def encode_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
