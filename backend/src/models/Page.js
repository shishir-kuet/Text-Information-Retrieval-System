const mongoose = require("mongoose");

const PageSchema = new mongoose.Schema(
  {
    bookId: { 
      type: mongoose.Schema.Types.ObjectId, 
      ref: "Book", 
      required: true,
      index: true 
    },
    pageNumber: { 
      type: Number, 
      required: true,
      min: 1 
    },
    text: { 
      type: String, 
      required: true 
    },
    tokenCount: { 
      type: Number, 
      default: 0 
    },
    ocrConfidence: {
      type: Number,
      default: null,
      min: 0,
      max: 100
    }
  },
  { 
    timestamps: true 
  }
);

// Compound index to prevent duplicate pages per book
PageSchema.index({ bookId: 1, pageNumber: 1 }, { unique: true });

// Index for efficient page lookups
PageSchema.index({ bookId: 1, pageNumber: 1 });

module.exports = mongoose.model("Page", PageSchema);
