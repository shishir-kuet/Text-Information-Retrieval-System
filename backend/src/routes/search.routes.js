const express = require("express");
const router = express.Router();
const searchController = require("../controllers/search.controller");

/**
 * @route   POST /api/search
 * @desc    Search for documents using TF-IDF ranking
 * @access  Public
 * @body    { query: string, limit?: number, minScore?: number, books?: array }
 */
router.post("/", searchController.search);

/**
 * @route   GET /api/search/stats
 * @desc    Get search statistics
 * @access  Public
 */
router.get("/stats", searchController.getSearchStats);

module.exports = router;
