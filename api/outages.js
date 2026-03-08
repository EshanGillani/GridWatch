import axios from "axios";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");

  try {
    const dominionURL =
      "https://outagemap.dominionenergy.com/resources/data/external/interval_generation_data/Outage.json";
    const appalachianURL =
      "https://outagemap.appalachianpower.com/resources/data/external/interval_generation_data/Outage.json";

    const [dominionRes, appRes] = await Promise.all([
      axios.get(dominionURL),
      axios.get(appalachianURL),
    ]);

    const dominionAreas = dominionRes.data?.file_data?.areas || [];
    const appAreas = appRes.data?.file_data?.areas || [];

    const outages = [
      ...dominionAreas.map((o) => ({
        provider: "Dominion Energy",
        lat: o.lat,
        lng: o.lng,
        customers: o.cust_a?.val ?? o.cust_a ?? 0,
        cause: o.cause || "Unknown",
        crew_status: o.crew_status || "Unknown",
        etr: o.etr || "Unknown",
        incident_id: o.id || null,
      })),
      ...appAreas.map((o) => ({
        provider: "Appalachian Power",
        lat: o.lat,
        lng: o.lng,
        customers: o.cust_a?.val ?? o.cust_a ?? 0,
        cause: o.cause || "Unknown",
        crew_status: o.crew_status || "Unknown",
        etr: o.etr || "Unknown",
        incident_id: o.id || null,
      })),
    ];

    const customersOut = outages.reduce((sum, o) => sum + (o.customers || 0), 0);
    const totalCustomers = 2820940; // approximate Dominion + Appalachian service area

    res.status(200).json({
      pulled_at_utc: new Date().toISOString(),
      summary: {
        report_date: new Date().toISOString(),
        customers_out: customersOut,
        total_customers: totalCustomers,
        pct_out: +((customersOut / totalCustomers) * 100).toFixed(2),
        total_outages: outages.length,
      },
      outages,
    });
  } catch (err) {
    console.error("Outage fetch error:", err.message);
    res.status(500).json({ error: "Failed to fetch outage data" });
  }
}
