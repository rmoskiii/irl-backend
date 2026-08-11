// Bare-bones in-memory limiter. Doesn't matter much while responses are
// scripted lookups, but the hook needs to already exist for the day
// personaService starts making real (costed) model calls.
const WINDOW_MS = 60 * 60 * 1000; // 1 hour
const MAX_REQUESTS_PER_WINDOW = 60;

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
