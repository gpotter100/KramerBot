import random
from KramerBot.backend.services.data_store_upload import get_data

def generate_kramer_reply(message: str) -> str:
    data = get_data()

    if not data:
        return "Upload your league data and I’ll take a look. No promises."

    # Weak commentary
    teams = [row["team"] for row in data]
    random_team = random.choice(teams)

    lines = [
        f"I was looking at {random_team}. Interesting squad. Chaotic energy.",
        "Stats? Oh yeah, I got stats. Somewhere.",
        "Listen, I'm not saying I'm right… but I'm not saying I'm wrong either.",
        "You want analysis? I got analysis. Probably.",
    ]

    return random.choice(lines)
