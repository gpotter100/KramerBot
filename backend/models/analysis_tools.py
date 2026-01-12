# models/analysis_tools.py
from typing import Optional, Dict

def analyze_message(message: str, data_context: Optional[Dict[str, Dict]]) -> Optional[str]:
  """
  Return a short text snippet that sounds like analysis based on the limited data we 'have'.
  """
  if not data_context:
    # No specific team referenced, maybe talk generally
    if "who is winning" in message.lower() or "best team" in message.lower():
      return "Team A currently has the most wins and points, so they are the front-runner."
    if "standings" in message.lower() or "rankings" in message.lower():
      return (
        "Rough ranking by wins and points: Team A, Team B, Team C, then Team D. "
        "It’s a small sample size, though."
      )
    return None

  # If a team was matched, just pick the first for now
  team, stats = list(data_context.items())[0]
  msg_lower = message.lower()

  if "wins" in msg_lower:
    return f"{team} currently has {stats['wins']} wins, which puts them in the mix competitively."

  if "points" in msg_lower or "score" in msg_lower:
    return f"{team} has racked up {stats['points']} total points so far."

  if "good" in msg_lower or "any good" in msg_lower:
    return (
      f"{team} sits at {stats['wins']} wins and {stats['points']} points. "
      "Not elite, not terrible—just living in that messy middle."
    )

  # Generic fallback
  return (
    f"For {team}, I only have simple season totals: {stats['wins']} wins and {stats['points']} points. "
    "No fancy breakdowns, but we can riff on that."
  )
