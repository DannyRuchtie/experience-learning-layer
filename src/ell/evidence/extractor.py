"""Evidence extraction from user messages."""

from __future__ import annotations

from ell.evidence.schemas import EvidenceData
from ell.models.client import LanguageModel


async def extract_evidence(
    text: str,
    message_id: str,
    model: LanguageModel,
) -> list[EvidenceData]:
    """Extract evidence units from a single user message.

    Returns an empty list when the message contains no durable evidence.
    """
    from ell.models.prompts import load_prompt

    prompt_text = load_prompt("evidence_extraction")

    system_prompt = prompt_text.replace("{message_text}", text)

    resp = await model.generate_structured(
        system_prompt=system_prompt,
        user_prompt=text,
        response_model=list[EvidenceData],  # type: ignore
        prompt_version="1.0.0",
    )

    return resp.data
