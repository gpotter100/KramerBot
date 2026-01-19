/* ==========================================================
   CHARTS: FANTASY ATTRIBUTION VISUALS
   Reusable charting module for multi-week usage + PBP pages
========================================================== */

export function renderAttributionStackedBar(ctx, attrData) {
  /*
    attrData = [
      {
        week: 1,
        passing_yards: 12.3,
        rushing_yards: 4.1,
        receiving_yards: 38.2,
        passing_tds: 0,
        rushing_tds: 12.0,
        receiving_tds: 18.0,
        receptions: 14.0,
        turnovers: -4.4,
        bonuses: 6.0
      },
      ...
    ]
  */

  const labels = attrData.map(d => `W${d.week}`);

  const datasets = [
    { key: "passing_yards", label: "Pass Yds", color: "#4e79a7" },
    { key: "rushing_yards", label: "Rush Yds", color: "#59a14f" },
    { key: "receiving_yards", label: "Rec Yds", color: "#9c755f" },
    { key: "passing_tds", label: "Pass TDs", color: "#f28e2b" },
    { key: "rushing_tds", label: "Rush TDs", color: "#edc948" },
    { key: "receiving_tds", label: "Rec TDs", color: "#e15759" },
    { key: "receptions", label: "Receptions", color: "#76b7b2" },
    { key: "bonuses", label: "Bonuses", color: "#af7aa1" },
    { key: "turnovers", label: "Turnovers", color: "#ff9da7" }
  ];

  const chartData = {
    labels,
    datasets: datasets.map(ds => ({
      label: ds.label,
      data: attrData.map(d => d[ds.key] || 0),
      backgroundColor: ds.color,
      borderWidth: 0,
      stack: "stack1"
    }))
  };

  return new Chart(ctx, {
    type: "bar",
    data: chartData,
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
        tooltip: { mode: "index", intersect: false }
      },
      scales: {
        x: { stacked: true },
        y: { stacked: true, beginAtZero: true }
      }
    }
  });
}

export function renderAttributionDonut(ctx, totals) {
  /*
    totals = {
      passing_yards: 12.3,
      rushing_yards: 4.1,
      receiving_yards: 38.2,
      passing_tds: 0,
      rushing_tds: 12.0,
      receiving_tds: 18.0,
      receptions: 14.0,
      turnovers: -4.4,
      bonuses: 6.0
    }
  */

  const labels = Object.keys(totals);
  const values = Object.values(totals);

  const colors = [
    "#4e79a7", "#59a14f", "#9c755f", "#f28e2b", "#edc948",
    "#e15759", "#76b7b2", "#ff9da7", "#af7aa1"
  ];

  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });
}

export function renderEpaTrendline(ctx, epaData) {
  /*
    epaData = [
      { week: 1, epa: 0.12 },
      { week: 2, epa: -0.03 },
      ...
    ]
  */

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: epaData.map(d => `W${d.week}`),
      datasets: [
        {
          label: "EPA per Play",
          data: epaData.map(d => d.epa),
          borderColor: "#4e79a7",
          backgroundColor: "rgba(78,121,167,0.2)",
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" }
      },
      scales: {
        y: { beginAtZero: false }
      }
    }
  });
}
