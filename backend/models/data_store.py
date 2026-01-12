# models/data_store.py

LEAGUE_DATA = {
  "Team A": {"wins": 8, "points": 1123},
  "Team B": {"wins": 7, "points": 1087},
  "Team C": {"wins": 5, "points": 975},
  "Team D": {"wins": 3, "points": 842},
}

def get_known_data(message: str):
  """
  Return a subset of LEAGUE_DATA relevant to the message.
  For now: match by team name if mentioned.
  """
  message_lower = message.lower()
  matched = {}

  for team, stats in LEAGUE_DATA.items():
    if team.lower() in message_lower:
      matched[team] = stats

  # If no specific team is referenced, return None and let analysis be generic
  return matched or None


def get_global_context() -> str:
  """
  A short description of the league and what data we 'have'.
  This gets baked into the prompt to make the bot feel data-aware.
  """
  lines = ["We are tracking a small fantasy-style league with the following teams:\n"]
  for team, stats in LEAGUE_DATA.items():
    lines.append(f"- {team}: wins={stats['wins']}, points={stats['points']}")
  lines.append(
    "\nData is limited to basic season summary stats: total wins and total points. "
    "No per-player or per-week details are stored."
  )
  return "\n".join(lines)
