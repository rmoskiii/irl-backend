require("dotenv").config();
const express = require("express");
const cors = require("cors");
const rateLimiter = require("./middleware/rateLimiter");
const scenarioRoutes = require("./routes/scenarios");

const app = express();
// Behind a hosting proxy req.ip is the PROXY's address unless this is set, so
// the per-IP rate limit would put every player in one shared bucket.
app.set("trust proxy", Number(process.env.TRUST_PROXY_HOPS ?? 1));
const PORT = process.env.PORT || 4000;

app.use(cors({
  origin: [
    /^http:\/\/localhost:\d+$/, // Matches http://localhost:<any_port>
    'https://irx.world',
    'https://www.irx.world'
  ],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
app.use(express.json());
app.use(rateLimiter);

app.get("/", (req, res) => {
  res.json({ status: "IRL backend v0 - running" });
});

app.use("/api/scenarios", scenarioRoutes);

app.listen(PORT, "0.0.0.0", () => {
  console.log(`IRL backend listening on port ${PORT}`);
});