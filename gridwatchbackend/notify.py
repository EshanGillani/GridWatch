"""
GridWatch outage risk notifier.
Reads subscribers.json, fetches live weather for each subscribed city,
and emails anyone in a city with risk >= RISK_THRESHOLD via Resend.

Required env vars:
  RESEND_API_KEY  — from resend.com (free tier: 3 000 emails/month)

Optional: update FROM_EMAIL once you have a verified Resend domain.
"""

import json
import os
import sys
import requests

CITIES = {
    "Richmond, VA":        (37.5538, -77.4603),
    "Virginia Beach, VA":  (36.8529, -75.9780),
    "Norfolk, VA":         (36.8508, -76.2859),
    "Arlington, VA":       (38.8816, -77.0910),
    "Roanoke, VA":         (37.2709, -79.9414),
    "Charlottesville, VA": (38.0293, -78.4767),
    "Newport News, VA":    (37.0871, -76.4730),
    "Hampton, VA":         (37.0299, -76.3452),
    "Chesapeake, VA":      (36.7682, -76.2875),
    "Alexandria, VA":      (38.8048, -77.0469),
}

RISK_THRESHOLD = 0.25   # 25% — alert subscribers above this level
FROM_EMAIL     = "GridWatch Alerts <onboarding@resend.dev>"   # update with verified domain
SITE_URL       = "https://gridwatch.vercel.app/predictions.html"


def compute_risk(w: dict) -> float:
    score = 0.0
    gusts  = w.get("wind_gusts_10m", 0) or 0
    wind   = w.get("wind_speed_10m",  0) or 0
    precip = w.get("precipitation",   0) or 0
    snow   = w.get("snowfall",        0) or 0

    if   gusts > 50: score += 0.40
    elif gusts > 35: score += 0.25
    elif gusts > 20: score += 0.10

    if   wind > 40: score += 0.20
    elif wind > 25: score += 0.10

    if   precip > 1.0: score += 0.30
    elif precip > 0.3: score += 0.15

    if   snow > 2:   score += 0.30
    elif snow > 0.5: score += 0.15

    return min(1.0, score)


def fetch_risk(city: str) -> float:
    lat, lon = CITIES[city]
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=wind_speed_10m,wind_gusts_10m,precipitation,snowfall"
        f"&temperature_unit=fahrenheit"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return compute_risk(r.json()["current"])


def send_alert(to: str, city: str, risk_pct: float, api_key: str) -> bool:
    # Pick color along green→yellow→red gradient matching the site
    if risk_pct <= 50:
        hue = round(120 - risk_pct * 1.2)
    else:
        hue = round(60 - (risk_pct - 50) * 1.2)
    color = f"hsl({hue}, 88%, 38%)"

    html = f"""
    <div style="font-family:'DM Sans',sans-serif;max-width:500px;margin:auto;
                padding:32px;background:#FAF9F6;border:3px solid #484848;">
      <h2 style="font-family:serif;font-size:26px;color:#484848;margin:0 0 4px;">
        &#9889; GridWatch Alert
      </h2>
      <p style="color:#9a9188;font-size:13px;margin:0 0 24px;
                text-transform:uppercase;letter-spacing:.08em;">
        Outage Risk Notification
      </p>

      <div style="border:2px solid #484848;padding:20px 24px;margin-bottom:24px;
                  box-shadow:4px 4px 0 #C8C0B8;">
        <p style="font-size:36px;font-weight:700;color:{color};margin:0;">
          {risk_pct:.1f}%
        </p>
        <p style="color:#9a9188;font-size:13px;margin:4px 0 0;">
          Predicted outage risk &mdash; {city}
        </p>
      </div>

      <p style="color:#484848;font-size:14px;line-height:1.75;margin-bottom:24px;">
        Current weather conditions in <b>{city}</b> have triggered a GridWatch
        high-risk alert. We recommend charging devices and preparing for a
        potential power outage.
      </p>

      <a href="{SITE_URL}"
         style="display:inline-block;background:#FF8B80;color:#484848;
                font-weight:700;padding:10px 24px;text-decoration:none;
                border:2px solid #484848;font-family:sans-serif;">
        View Live Predictions &rarr;
      </a>

      <p style="margin-top:32px;font-size:11px;color:#C8C0B8;line-height:1.6;">
        You subscribed to GridWatch outage alerts for {city}.<br>
        To unsubscribe, reply to this email with &ldquo;unsubscribe&rdquo;.
      </p>
    </div>
    """

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from":    FROM_EMAIL,
            "to":      [to],
            "subject": f"⚡ High Outage Risk Alert — {city} ({risk_pct:.1f}%)",
            "html":    html,
        },
        timeout=10,
    )
    return resp.status_code in (200, 201)


def main():
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("[notify] RESEND_API_KEY not set — skipping.")
        return

    subscribers_path = os.path.join(
        os.path.dirname(__file__), "..", "subscribers.json"
    )
    with open(subscribers_path) as f:
        data = json.load(f)

    subscribers = data.get("subscribers", [])
    if not subscribers:
        print("[notify] No subscribers.")
        return

    # Fetch risk once per unique city
    city_risks: dict[str, float] = {}
    for city in {s["city"] for s in subscribers}:
        if city not in CITIES:
            print(f"[notify] Unknown city '{city}', skipping.")
            continue
        try:
            risk = fetch_risk(city)
            city_risks[city] = risk
            print(f"[notify] {city}: {risk*100:.1f}%")
        except Exception as e:
            print(f"[notify] {city}: fetch failed — {e}")

    # Notify subscribers in high-risk cities
    sent = 0
    for sub in subscribers:
        city = sub.get("city", "")
        risk = city_risks.get(city, 0.0)
        if risk >= RISK_THRESHOLD:
            ok = send_alert(sub["email"], city, risk * 100, api_key)
            status = "sent" if ok else "FAILED"
            print(f"[notify] {status} → {sub['email']} ({city} {risk*100:.1f}%)")
            if ok:
                sent += 1

    print(f"[notify] Done. {sent} alert(s) sent.")


if __name__ == "__main__":
    main()
