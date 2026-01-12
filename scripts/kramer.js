const KRAMER_RESPONSES = [
  "Buddy, let me take a look at that…",
  "Stats are like pretzels — crunchy and confusing.",
  "Giddy up! Processing your data.",
  "Whoa! These numbers are wild.",
  "I got charts, I got tables, I got… something.",
  "Listen, I'm not saying this is accurate, but it is interesting.",
  "You ever just *feel* like your team is cursed?",
  "I’m seeing numbers… big, small, all of ‘em.",
];

function getRandomKramerResponse() {
  const idx = Math.floor(Math.random() * KRAMER_RESPONSES.length);
  return KRAMER_RESPONSES[idx];
}

function kramerIntroLines() {
  return [
    "KramerBot here. I got stats… probably.",
    "Upload your league CSVs and I’ll show you a few things. No guarantees.",
  ];
}
