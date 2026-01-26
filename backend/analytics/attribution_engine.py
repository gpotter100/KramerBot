def compute_multiweek_attribution(pbp_rows, usage_rows):
    """
    Combine PBP + usage to compute fantasy attribution across weeks.
    Returns a list of player attribution dicts.
    """

    players = {}

    # ------------------------------------------------------------
    # Initialize players from usage (fantasy totals + raw usage)
    # ------------------------------------------------------------
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
            "fantasy_points_vandalay": u.get("fantasy_points_vandalay", 0),
            "fantasy_points_shen2000": u.get("fantasy_points_shen2000", 0),

            # Raw attribution buckets
            "rush_yards": 0,
            "rec_yards": 0,
            "pass_yards": 0,
            "rush_tds": 0,
            "rec_tds": 0,
            "pass_tds": 0,
            "interceptions": 0,
            "fumbles_lost": 0,
            "sack_fumbles": 0,
            "sack_fumbles_lost": 0,

            # EPA + success
            "epa_total": 0,
            "success_plays": 0,
            "total_plays": 0,

            # Fantasy component totals (multi-week)
            "comp_passing_yards": 0,
            "comp_rushing_yards": 0,
            "comp_receiving_yards": 0,
            "comp_passing_tds": 0,
            "comp_rushing_tds": 0,
            "comp_receiving_tds": 0,
            "comp_interceptions": 0,
            "comp_fumbles_lost": 0,
            "comp_sack_fumbles": 0,
            "comp_sack_fumbles_lost": 0,
            "comp_receptions": 0,
        }

    # ------------------------------------------------------------
    # Attribute PBP rows (raw stats)
    # ------------------------------------------------------------
    for p in pbp_rows:
        pid = (
            p.get("rusher_player_id")
            or p.get("receiver_player_id")
            or p.get("passer_player_id")
        )
        if pid not in players:
            continue

        player = players[pid]

        # Yardage
        player["rush_yards"] += p.get("rushing_yards", 0)
        player["rec_yards"] += p.get("receiving_yards", 0)
        player["pass_yards"] += p.get("passing_yards", 0)

        # TDs
        player["rush_tds"] += p.get("rushing_tds", 0)
        player["rec_tds"] += p.get("receiving_tds", 0)
        player["pass_tds"] += p.get("passing_tds", 0)

        # Turnovers
        player["interceptions"] += p.get("interceptions", 0)
        player["fumbles_lost"] += p.get("fumbles_lost", 0)
        player["sack_fumbles"] += p.get("sack_fumbles", 0)
        player["sack_fumbles_lost"] += p.get("sack_fumbles_lost", 0)

        # EPA + success
        player["epa_total"] += p.get("epa", 0)
        player["total_plays"] += 1
        if p.get("success"):
            player["success_plays"] += 1

    # ------------------------------------------------------------
    # Add fantasy component totals (from usage rows)
    # ------------------------------------------------------------
    for u in usage_rows:
        pid = u.get("player_id")
        if pid not in players:
            continue

        p = players[pid]

        for key in [
            "comp_passing_yards",
            "comp_rushing_yards",
            "comp_receiving_yards",
            "comp_passing_tds",
            "comp_rushing_tds",
            "comp_receiving_tds",
            "comp_interceptions",
            "comp_fumbles_lost",
            "comp_sack_fumbles",
            "comp_sack_fumbles_lost",
            "comp_receptions",
        ]:
            p[key] += u.get(key, 0)

    # ------------------------------------------------------------
    # Finalize success rate
    # ------------------------------------------------------------
    for pid, p in players.items():
        if p["total_plays"] > 0:
            p["success_rate"] = p["success_plays"] / p["total_plays"]
        else:
            p["success_rate"] = 0.0

    return list(players.values())
