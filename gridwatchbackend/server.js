import express from "express"
import axios from "axios"
import cors from "cors"

const app = express()
app.use(cors())

const PORT = 3000

// API route
app.get("/api/outages", async (req, res) => {

  try {

    const dominionURL =
      "https://outagemap.dominionenergy.com/resources/data/external/interval_generation_data/Outage.json"

    const appalachianURL =
      "https://outagemap.appalachianpower.com/resources/data/external/interval_generation_data/Outage.json"

    const [dominionRes, appRes] = await Promise.all([
      axios.get(dominionURL),
      axios.get(appalachianURL)
    ])

    const dominionAreas = dominionRes.data?.file_data?.areas || []
    const appAreas = appRes.data?.file_data?.areas || []

    const dominion = dominionAreas.map(o => ({
      provider: "Dominion Energy",
      lat: o.lat,
      lng: o.lng,
      customers: o.cust_a || 0
    }))

    const appalachian = appAreas.map(o => ({
      provider: "Appalachian Power",
      lat: o.lat,
      lng: o.lng,
      customers: o.cust_a || 0
    }))

    res.json([...dominion, ...appalachian])

  } catch (err) {

    console.error("Outage fetch error:", err)
    res.status(500).json({ error: "Failed to fetch outage data" })

  }

})

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
})