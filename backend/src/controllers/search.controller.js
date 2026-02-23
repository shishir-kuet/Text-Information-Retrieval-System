const searchService = require("../services/search.service");
const logger = require("../utils/logger");

/**
 * Search for documents
 */
exports.search = async (req, res, next) => {
  try {
    const { query, limit, minScore, books } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        message: "Query parameter is required"
      });
    }

    const options = {
      limit: limit ? parseInt(limit) : 10,
      minScore: minScore ? parseFloat(minScore) : 0.01,
      books: books || null
    };

    const results = await searchService.search(query, options);

    res.status(200).json({
      success: true,
      data: results
    });

  } catch (error) {
    logger.error("Search controller error:", error);
    next(error);
  }
};

/**
 * Get search statistics
 */
exports.getSearchStats = async (req, res, next) => {
  try {
    const stats = await searchService.getSearchStats();

    res.status(200).json({
      success: true,
      data: stats
    });

  } catch (error) {
    logger.error("Get search stats error:", error);
    next(error);
  }
};
