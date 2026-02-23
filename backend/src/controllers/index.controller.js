const indexService = require("../services/index.service");
const logger = require("../utils/logger");

/**
 * Build index for a specific book
 */
exports.buildIndexForBook = async (req, res, next) => {
  try {
    const { id } = req.params;

    const stats = await indexService.buildIndexForBook(id);

    res.status(200).json({
      success: true,
      message: "Index built successfully for book",
      data: stats
    });
  } catch (error) {
    logger.error("Build index for book error:", error);
    next(error);
  }
};

/**
 * Build index for all processed books
 */
exports.buildIndexForAllBooks = async (req, res, next) => {
  try {
    const stats = await indexService.buildIndexForAllBooks();

    res.status(200).json({
      success: true,
      message: "Index built successfully for all books",
      data: stats
    });
  } catch (error) {
    logger.error("Build index for all books error:", error);
    next(error);
  }
};

/**
 * Rebuild entire index (clear and rebuild)
 */
exports.rebuildIndex = async (req, res, next) => {
  try {
    const stats = await indexService.rebuildIndex();

    res.status(200).json({
      success: true,
      message: "Index rebuilt successfully",
      data: stats
    });
  } catch (error) {
    logger.error("Rebuild index error:", error);
    next(error);
  }
};

/**
 * Get index statistics
 */
exports.getIndexStats = async (req, res, next) => {
  try {
    const stats = await indexService.getIndexStats();

    res.status(200).json({
      success: true,
      data: stats
    });
  } catch (error) {
    logger.error("Get index stats error:", error);
    next(error);
  }
};

/**
 * Remove book from index
 */
exports.removeBookFromIndex = async (req, res, next) => {
  try {
    const { id } = req.params;

    const result = await indexService.removeBookFromIndex(id);

    res.status(200).json({
      success: true,
      message: "Book removed from index",
      data: result
    });
  } catch (error) {
    logger.error("Remove book from index error:", error);
    next(error);
  }
};
