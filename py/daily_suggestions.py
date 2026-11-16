from google import genai
from google.genai.errors import APIError


MODEL = "gemini-3.5-flash-lite"


class DailySuggestionError(RuntimeError):
    pass


def generate_daily_suggestions(
    api_key: str, habits: list[dict[str, str]]
) -> str:
    prompt = (
        "You are a practical, encouraging habit coach. Give up to three short, "
        "specific suggestions the person can do for the rest of today, based "
        "only on these active habits and their progress. Prioritize unfinished "
        "or partly completed habits. If all are complete, suggest a simple way "
        "to maintain the routine or celebrate. Do not add unrelated habits or "
        "use guilt. Use a concise bullet list.\n\n"
        f"Today's habits and progress:\n{habits}"
    )

    try:
        response = genai.Client(api_key=api_key).models.generate_content(
            model=MODEL,
            contents=prompt,
        )
    except APIError as exc:
        raise DailySuggestionError(
            f"Gemini could not generate suggestions: {exc}"
        ) from exc

    suggestion = response.text
    if not suggestion or not suggestion.strip():
        raise DailySuggestionError(
            "Gemini returned no suggestions. Please try again."
        )
    return suggestion.strip()
