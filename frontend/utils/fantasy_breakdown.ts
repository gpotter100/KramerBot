type PlayerRow = {
  [key: string]: number | string | null;
};

export function buildFantasyBreakdown(row: PlayerRow) {
  const safe = (v: any) => (typeof v === "number" ? v : 0);

  return {
    passing: {
      yds: safe(row.passing_yards),
      fpts_yds: safe(row.comp_passing_yards),
      attr_pct_yds: safe(row.pct_passing_yards),
      tds: safe(row.passing_tds),
      fpts_tds: safe(row.comp_passing_tds),
      attr_pct_tds: safe(row.pct_passing_tds),
    },
    rushing: {
      yds: safe(row.rushing_yards),
      fpts_yds: safe(row.comp_rushing_yards),
      attr_pct_yds: safe(row.pct_rushing_yards),
      tds: safe(row.rushing_tds),
      fpts_tds: safe(row.comp_rushing_tds),
      attr_pct_tds: safe(row.pct_rushing_tds),
    },
    receiving: {
      rec: safe(row.receptions),
      yds: safe(row.receiving_yards),
      fpts_yds: safe(row.comp_receiving_yards),
      attr_pct_yds: safe(row.pct_receiving_yards),
      tds: safe(row.receiving_tds),
      fpts_tds: safe(row.comp_receiving_tds),
      attr_pct_tds: safe(row.pct_receiving_tds),
    },
    fumbles: {
      lost: safe(row.fumbles_lost),
      fpts_lost: safe(row.comp_fumbles_lost),
      attr_pct_lost: safe(row.pct_fumbles_lost),
    },
    fantasy: {
      total: safe(row.fantasy_points),
      // you can pass weeks in separately or read from row.weeks if present
    },
  };
}
