import express from "express";
import cors from "cors";

const app = express();
app.use(cors());

app.get("/api/outages", (req, res) => {
  res.json([
    {
      provider: "Dominion Energy",
      lat: 37.54,
      lng: -77.43,
      customers: 1200
    }
  ]);
});

app.listen(3000, () => {
  console.log("GridWatch backend running on port 3000");
});