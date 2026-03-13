import { kv } from "@vercel/kv"

export default async function handler(_req, res) {
  const raw = await kv.lrange("gridwatch-reports", 0, -1)
  const reports = raw.map(r => typeof r === "string" ? JSON.parse(r) : r)
  res.json({ reports })
}
