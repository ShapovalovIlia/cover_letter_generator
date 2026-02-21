import functools

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from src.config import settings

_SYSTEM_PROMPT = """\
You are an expert career consultant who writes compelling, \
personalised cover letters.

Instructions:
- Analyse the candidate's resume and the job description carefully.
- Highlight the candidate's most relevant experience, skills, \
and achievements that match the job requirements.
- Write a professional cover letter in {language} language.
- Keep it concise (3-4 paragraphs) and engaging.
- Do NOT invent facts about the candidate — use only information \
from the resume.
- Output ONLY the cover letter text, no extra commentary.\
"""

_USER_PROMPT = """\
=== RESUME ===
{resume_text}

=== JOB DESCRIPTION ===
{job_description}\
"""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        ("human", _USER_PROMPT),
    ]
)


@functools.lru_cache(maxsize=1)
def get_chain() -> Runnable[dict[str, str], str]:
    model = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.7,
    )
    return _prompt | model | StrOutputParser()
