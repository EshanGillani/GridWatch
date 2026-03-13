import { kv } from "@vercel/kv"

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" })
  }

  const { time, password } = req.body

  if (!process.env.ADMIN_PASSWORD || password !== process.env.ADMIN_PASSWORD) {
    return res.status(401).json({ error: "Unauthorized" })
  }

  const all = await kv.lrange("gridwatch-reports", 0, -1)
  const target = all.find(r => {
    const parsed = typeof r === "string" ? JSON.parse(r) : r
    return parsed.time === time
  })

  if (!target) {
    return res.status(404).json({ error: "Report not found" })
  }

  await kv.lrem("gridwatch-reports", 1, target)
  res.json({ message: "Deleted" })
}
