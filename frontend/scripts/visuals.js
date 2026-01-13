export async function refreshVisuals(API_BASE) {
  try {
    const res = await fetch(`${API_BASE}/visuals/`);
    const data = await res.json();

    if (data.error) {
      console.warn("No visuals available yet.");
      return;
    }

    console.log("Visuals:", data);
    // You can add chart rendering logic here later
  } catch (err) {
    console.error("Error loading visuals", err);
  }
}
