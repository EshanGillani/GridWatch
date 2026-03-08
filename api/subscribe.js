// Vercel serverless function — POST /api/subscribe
// Required Vercel env vars:
//   GH_TOKEN  — GitHub personal access token with repo write access

const OWNER = "EshanGillani";
const REPO  = "GridWatch";
const PATH  = "subscribers.json";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST")
    return res.status(405).json({ error: "Method not allowed" });

  const { email, city } = req.body || {};

  if (!email || !city)
    return res.status(400).json({ error: "Email and city are required." });

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    return res.status(400).json({ error: "Invalid email address." });

  const token = process.env.GH_TOKEN;
  if (!token)
    return res.status(500).json({ error: "Server misconfiguration." });

  const ghHeaders = {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
  };

  try {
    // Read current subscribers.json from repo
    const getRes = await fetch(
      `https://api.github.com/repos/${OWNER}/${REPO}/contents/${PATH}`,
      { headers: ghHeaders }
    );
    if (!getRes.ok) throw new Error("Could not read subscriber list.");
    const fileData = await getRes.json();

    const current = JSON.parse(
      Buffer.from(fileData.content, "base64").toString("utf-8")
    );

    // Deduplicate
    const alreadyExists = current.subscribers.some(
      (s) => s.email === email && s.city === city
    );
    if (alreadyExists)
      return res
        .status(200)
        .json({ message: `Already subscribed to alerts for ${city}.` });

    current.subscribers.push({
      email,
      city,
      subscribedAt: new Date().toISOString(),
    });

    // Write back to repo
    const putRes = await fetch(
      `https://api.github.com/repos/${OWNER}/${REPO}/contents/${PATH}`,
      {
        method: "PUT",
        headers: ghHeaders,
        body: JSON.stringify({
          message: `chore: subscribe ${email} → ${city}`,
          content: Buffer.from(
            JSON.stringify(current, null, 2)
          ).toString("base64"),
          sha: fileData.sha,
        }),
      }
    );

    if (!putRes.ok) {
      const err = await putRes.json();
      throw new Error(err.message || "Failed to save subscription.");
    }

    return res.status(200).json({
      message: `Subscribed! You'll be alerted when outage risk is high in ${city}.`,
    });
  } catch (err) {
    console.error("Subscribe error:", err);
    return res.status(500).json({ error: err.message || "Server error." });
  }
}
