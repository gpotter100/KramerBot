# models/chat_models.py
from typing import List, Dict, Optional
from data_store import get_known_data, get_global_context
from analysis_tools import analyze_message
from kramer_persona import wrap_as_kramer, system_preamble

# Super simple in-memory history for now (per-process)
chat_history: List[Dict[str, str]] = []

async def generate_reply(user_message: str) -> str:
  # Store the user message
  chat_history.append({"role": "user", "content": user_message})

  # 1. See if this question hits our "data"
  data_context = get_known_data(user_message)

  # 2. Try to compute some pseudo-analysis
  analysis_snippet = analyze_message(user_message, data_context)

  # 3. Global context (league overview, what data we "have")
  global_context = get_global_context()

  # 4. Build a fake "prompt" to feed into a pretend model (or real LLM later)
  prompt = build_prompt(chat_history, global_context, data_context, analysis_snippet)

  # 5. For now, call a simple heuristic "model"
  base_reply = fake_llm(prompt)

  # 6. Wrap in Kramer persona
  final_reply = wrap_as_kramer(base_reply)

  # 7. Save response to history
  chat_history.append({"role": "assistant", "content": final_reply})

  return final_reply


def build_prompt(
  history: List[Dict[str, str]],
  global_context: str,
  data_context: Optional[Dict[str, Dict]],
  analysis_snippet: Optional[str]
) -> str:
  parts = [system_preamble(), "\n\n"]

  parts.append("Known league context:\n")
  parts.append(global_context)
  parts.append("\n\n")

  if data_context:
    parts.append("Relevant team data for this question:\n")
    for team, stats in data_context.items():
      parts.append(f"- {team}: wins={stats['wins']}, points={stats['points']}\n")
    parts.append("\n")

  if analysis_snippet:
    parts.append("Quick analysis:\n")
    parts.append(analysis_snippet)
    parts.append("\n\n")

  parts.append("Recent conversation:\n")
  for msg in history[-6:]:  # last 6 messages
    role = "User" if msg["role"] == "user" else "KramerBot"
    parts.append(f"{role}: {msg['content']}\n")

  parts.append("\nNow continue as KramerBot with a concise, witty answer.\n")

  return "".join(parts)


def fake_llm(prompt: str) -> str:
  """
  Stand-in for an actual LLM. For now, we just look at the latest user message
  and the analysis snippet implied by the prompt.
  This is where you can later plug in a real model call.
  """

  # Extremely simple heuristic:
  # Just grab the last "User:" line as the question to respond to.
  lines = prompt.splitlines()
  user_lines = [ln for ln in lines if ln.startswith("User:")]
  question = user_lines[-1][len("User:"):].strip() if user_lines else "something"

  # A few simple "smart" patterns
  q_lower = question.lower()
  if "who is winning" in q_lower or "best team" in q_lower:
    return "Right now it looks like Team A is running the show, but things can change fast in this league."

  if "worst team" in q_lower or "last place" in q_lower:
    return "Team D is bringing up the rear at the moment. Hey, someone’s gotta do it."

  if "points" in q_lower and "team a" in q_lower:
    return "Team A is sitting pretty with 1123 points. Not too shabby."

  if "wins" in q_lower and "team b" in q_lower:
    return "Team B has stacked up 7 wins. They’re knocking on the door."

  if "help" in q_lower or "what can you do" in q_lower:
    return (
      "I can talk through your league, react to your data, give fake-but-funny insights, "
      "and pretend to be a serious analytics department."
    )

  # Default: paraphrase the question as if thinking about it
  return (
    f"You're asking about \"{question}\". Based on what I’ve seen in this league, "
    "I can give you a rough, very unofficial take."
  )
