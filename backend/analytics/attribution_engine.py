def compute_multiweek_attribution(pbp_rows, usage_rows):
    """
    Combine PBP + usage to compute fantasy attribution across weeks.
    Returns a dict keyed by player_id.
    """

    players = {}

    # Initialize players from usage
    for u in usage_rows:
        pid = u.get("player_id")
        players[pid] = {
            "player_id": pid,
            "player_name": u.get("player_name"),
            "team": u.get("team"),
            "position": u.get("position"),
            "weeks": u.get("weeks", []),

            # Usage totals
            "touches": u.get("touches", 0),
            "total_yards": u.get("total_yards", 0),
            "touchdowns": u.get("touchdowns", 0),

            # Fantasy totals
            "fantasy_points": u.get("fantasy_points", 0),
            "fantasy_points_ppr": u.get("fantasy_points_ppr", 0),
            "fantasy_points_half": u.get("fantasy_points_half", 0),
            "fantasy_points_shen2000": u.get("fantasy_points_shen2000", 0),

            # Attribution buckets
            "rush_yards": 0,
            "rec_yards": 0,
            "pass_yards": 0,
            "rush_tds": 0,
            "rec_tds": 0,
            "pass_tds": 0,
            "epa_total": 0,
            "success_plays": 0,
            "total_plays": 0,
        }

    # Attribute PBP rows
    for p in pbp_rows:
        pid = p.get("rusher_player_id") or p.get("receiver_player_id") or p.get("passer_player_id")
        if pid not in players:
            continue

        player = players[pid]

        # Yardage attribution
        player["rush_yards"] += p.get("rushing_yards", 0)
        player["rec_yards"] += p.get("receiving_yards", 0)
        player["pass_yards"] += p.get("passing_yards", 0)

        # TD attribution
        player["rush_tds"] += p.get("rushing_tds", 0)
        player["rec_tds"] += p.get("receiving_tds", 0)
        player["pass_tds"] += p.get("passing_tds", 0)

        # EPA + success
        player["epa_total"] += p.get("epa", 0)
        player["total_plays"] += 1
        if p.get("success"):
            player["success_plays"] += 1

    # Finalize success rate
    for pid, p in players.items():
        if p["total_plays"] > 0:
            p["success_rate"] = p["success_plays"] / p["total_plays"]
        else:
            p["success_rate"] = 0.0

    return list(players.values())
