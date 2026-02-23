const Tesseract = require("tesseract.js");
const { createWorker } = Tesseract;
const logger = require("../utils/logger");

class OCRService {
  constructor() {
    this.worker = null;
  }

  /**
   * Initialize Tesseract worker
   */
  async initialize() {
    if (this.worker) return;

    try {
      logger.info("Initializing Tesseract OCR worker...");
      this.worker = await createWorker("eng");
      logger.info("Tesseract OCR worker initialized");
    } catch (error) {
      logger.error("Failed to initialize OCR worker:", error);
      throw error;
    }
  }

  /**
   * Extract text from an image buffer
   * @param {Buffer} imageBuffer - Image buffer to process
   * @returns {Promise<{text: string, confidence: number}>}
   */
  async extractText(imageBuffer) {
    try {
      if (!this.worker) {
        await this.initialize();
      }

      const result = await this.worker.recognize(imageBuffer);
      
      return {
        text: result.data.text.trim(),
        confidence: result.data.confidence
      };
    } catch (error) {
      logger.error("OCR extraction failed:", error);
      throw error;
    }
  }

  /**
   * Terminate the OCR worker
   */
  async terminate() {
    if (this.worker) {
      await this.worker.terminate();
      this.worker = null;
      logger.info("Tesseract OCR worker terminated");
    }
  }
}

// Export singleton instance
module.exports = new OCRService();
