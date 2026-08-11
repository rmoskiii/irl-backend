require("dotenv").config();
const express = require("express");
const cors = require("cors");
const rateLimiter = require("./middleware/rateLimiter");
const scenarioRoutes = require("./routes/scenarios");

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());
app.use(rateLimiter);

app.get("/", (req, res) => {
  res.json({ status: "IRL backend v0 - running" });
});

app.use("/api/scenarios", scenarioRoutes);

app.listen(PORT, () => {
  console.log(`IRL backend listening on http://localhost:${PORT}`);
});
