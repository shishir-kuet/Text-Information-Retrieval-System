const router = require("express").Router();

router.get("/", (req, res) => {
  res.json({
    status: "ok",
    service: "text-information-retrieval-backend",
    time: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || "development",
  });
});

module.exports = router;
