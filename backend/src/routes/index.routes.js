const express = require("express");
const router = express.Router();
const indexController = require("../controllers/index.controller");

/**
 * @route   POST /api/index/build/:id
 * @desc    Build inverted index for a specific book
 * @access  Public (should be protected in production)
 */
router.post("/build/:id", indexController.buildIndexForBook);

/**
 * @route   POST /api/index/build-all
 * @desc    Build inverted index for all processed books
 * @access  Public (should be protected in production)
 */
router.post("/build-all", indexController.buildIndexForAllBooks);

/**
 * @route   POST /api/index/rebuild
 * @desc    Rebuild entire index (clear and rebuild)
 * @access  Public (should be protected in production)
 */
router.post("/rebuild", indexController.rebuildIndex);

/**
 * @route   GET /api/index/stats
 * @desc    Get index statistics
 * @access  Public
 */
router.get("/stats", indexController.getIndexStats);

/**
 * @route   DELETE /api/index/book/:id
 * @desc    Remove a book from the index
 * @access  Public (should be protected in production)
 */
router.delete("/book/:id", indexController.removeBookFromIndex);

module.exports = router;
