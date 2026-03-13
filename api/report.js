import { kv } from "@vercel/kv"

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "4mb"
    }
  }
}

export default async function handler(req, res) {

if (req.method !== "POST") {
  return res.status(405).json({ error: "Method not allowed" })
}

try {

  const { zip, type, description, image } = req.body

  let lat = null, lng = null
  try {
    const geo = await fetch(`https://api.zippopotam.us/us/${zip}`)
    if (geo.ok) {
      const geoData = await geo.json()
      lat = parseFloat(geoData.places[0].latitude)
      lng = parseFloat(geoData.places[0].longitude)
    }
  } catch (geoErr) {
    console.error("Geo lookup failed:", geoErr)
  }

  const report = {
    zip,
    type,
    description,
    image: image || null,
    lat,
    lng,
    time: Date.now()
  }

  await kv.lpush("gridwatch-reports", JSON.stringify(report))

  res.json({ message: "Report submitted" })

} catch (err) {
  console.error("Report handler error:", err)
  res.status(500).json({ error: "Failed to submit report: " + err.message })
}
}
