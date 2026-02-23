function notFoundHandler(req, res, next) {
  res.status(404).json({ 
    message: "Route not found",
    path: req.originalUrl 
  });
}

function errorHandler(err, req, res, next) {
  console.error("❌ Error:", err);
  
  const statusCode = err.statusCode || 500;
  const message = err.message || "Internal server error";
  
  res.status(statusCode).json({
    message,
    ...(process.env.NODE_ENV === "development" && { stack: err.stack }),
  });
}

module.exports = { notFoundHandler, errorHandler };
