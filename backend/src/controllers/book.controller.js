const pdfService = require("../services/pdf.service");
const logger = require("../utils/logger");

/**
 * Upload and process PDF
 */
exports.uploadBook = async (req, res, next) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No PDF file uploaded"
      });
    }

    // Extract metadata from request body
    const metadata = {
      title: req.body.title,
      author: req.body.author,
      year: req.body.year ? parseInt(req.body.year) : null,
      source: req.body.source
    };

    // Process PDF (this is async and may take time)
    const book = await pdfService.processPDF(req.file, metadata);

    res.status(201).json({
      success: true,
      message: "Book uploaded and processed successfully",
      data: {
        bookId: book._id,
        title: book.title,
        author: book.author,
        totalPages: book.totalPages,
        status: book.status
      }
    });
  } catch (error) {
    logger.error("Upload book error:", error);
    next(error);
  }
};

/**
 * Get all books
 */
exports.getAllBooks = async (req, res, next) => {
  try {
    const books = await pdfService.getAllBooks();

    res.status(200).json({
      success: true,
      count: books.length,
      data: books
    });
  } catch (error) {
    logger.error("Get all books error:", error);
    next(error);
  }
};

/**
 * Get book by ID with all pages
 */
exports.getBookById = async (req, res, next) => {
  try {
    const { id } = req.params;

    const { book, pages } = await pdfService.getBookWithPages(id);

    res.status(200).json({
      success: true,
      data: {
        book,
        pages,
        pageCount: pages.length
      }
    });
  } catch (error) {
    logger.error("Get book by ID error:", error);
    next(error);
  }
};

/**
 * Delete book
 */
exports.deleteBook = async (req, res, next) => {
  try {
    const { id } = req.params;

    await pdfService.deleteBook(id);

    res.status(200).json({
      success: true,
      message: "Book deleted successfully"
    });
  } catch (error) {
    logger.error("Delete book error:", error);
    next(error);
  }
};

/**
 * Get book processing status
 */
exports.getBookStatus = async (req, res, next) => {
  try {
    const { id } = req.params;

    const { Book } = require("../models");
    const book = await Book.findById(id).select("title status totalPages ocrCompleted ocrError");

    if (!book) {
      return res.status(404).json({
        success: false,
        message: "Book not found"
      });
    }

    res.status(200).json({
      success: true,
      data: book
    });
  } catch (error) {
    logger.error("Get book status error:", error);
    next(error);
  }
};
