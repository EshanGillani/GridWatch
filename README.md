# GridWatch 

A real-time power outage monitoring dashboard for Dominion Energy's service territory in Virginia. GridWatch scrapes live outage data, stores it as JSON, and visualizes it on an interactive map with heatmap support and auto-refresh.

---

## Features

- **Live outage map** — circle markers sized and colored by severity, powered by Leaflet.js
- **Heatmap overlay** — toggle a density heatmap via `leaflet.heat`
- **Auto-refresh** — data reloads every 60 seconds with a live countdown
- **Summary stats** — customers out, active outage count, percent affected, and last-updated time
- **Popup details** — click any marker to see cause, crew status, ETR, and incident ID
- **Python scraper** — fetches live data from Dominion Energy's outage API and writes `outages.json`
- **Deployed on Vercel** — static frontend + Python serverless API function

---

## License

MIT
