// Bare-bones in-memory limiter. Doesn't matter much while responses are
// scripted lookups, but the hook needs to already exist for the day
// personaService starts making real (costed) model calls.
const WINDOW_MS = 60 * 60 * 1000; // 1 hour
// 60/hour was set for single-scene scenarios. The Streets is 51 nodes over 7
// days - one full playthrough is ~30-40 /respond calls plus a /node resume at
// each day boundary - so 60 cut players off partway through their first run.
// Configurable per environment; 600 is ~15 full runs an hour.
const MAX_REQUESTS_PER_WINDOW = Number(process.env.RATE_LIMIT_PER_HOUR) || 600;

const hits = new Map();

function rateLimiter(req, res, next) {
  const key = req.ip;
  const now = Date.now();
  const windowStart = now - WINDOW_MS;

  const timestamps = (hits.get(key) || []).filter((t) => t > windowStart);
  timestamps.push(now);
  hits.set(key, timestamps);

  if (timestamps.length > MAX_REQUESTS_PER_WINDOW) {
    return res.status(429).json({ error: "Too many requests. Try again shortly." });
  }
  next();
}

module.exports = rateLimiter;