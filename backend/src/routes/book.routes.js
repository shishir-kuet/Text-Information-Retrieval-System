const express = require("express");
const router = express.Router();
const bookController = require("../controllers/book.controller");
const upload = require("../config/multer");

/**
 * @route   POST /api/books/upload
 * @desc    Upload and process a PDF book
 * @access  Public (should be protected in production)
 */
router.post("/upload", upload.single("pdf"), bookController.uploadBook);

/**
 * @route   GET /api/books
 * @desc    Get all books
 * @access  Public
 */
router.get("/", bookController.getAllBooks);

/**
 * @route   GET /api/books/:id
 * @desc    Get book by ID with all pages
 * @access  Public
 */
router.get("/:id", bookController.getBookById);

/**
 * @route   GET /api/books/:id/status
 * @desc    Get book processing status
 * @access  Public
 */
router.get("/:id/status", bookController.getBookStatus);

/**
 * @route   DELETE /api/books/:id
 * @desc    Delete book and all its pages
 * @access  Public (should be protected in production)
 */
router.delete("/:id", bookController.deleteBook);

module.exports = router;
