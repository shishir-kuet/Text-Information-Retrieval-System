const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const morgan = require("morgan");
const rateLimit = require("express-rate-limit");

const healthRoutes = require("./routes/health.routes");
const bookRoutes = require("./routes/book.routes");
const indexRoutes = require("./routes/index.routes");
const { notFoundHandler, errorHandler } = require("./middlewares/error.middleware");

const app = express();

// Security & basics
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true }));

// Logging
app.use(morgan("dev"));

// Rate limiting
app.use(
  rateLimit({
    windowMs: 60 * 1000,
    max: 120,
    standardHeaders: true,
    legacyHeaders: false,
  })
);

// Routes
app.use("/api/health", healthRoutes);
app.use("/api/books", bookRoutes);
app.use("/api/index", indexRoutes);

// Error handlers
app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
