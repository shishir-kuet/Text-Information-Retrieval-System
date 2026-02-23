const mongoose = require("mongoose");

const BookSchema = new mongoose.Schema(
  {
    title: { 
      type: String, 
      required: true, 
      trim: true,
      index: true 
    },
    author: { 
      type: String, 
      default: "Unknown", 
      trim: true,
      index: true 
    },
    year: { 
      type: Number, 
      default: null 
    },
    source: { 
      type: String, 
      default: "", 
      trim: true 
    },
    fileName: { 
      type: String, 
      required: true, 
      trim: true,
      unique: true 
    },
    totalPages: { 
      type: Number, 
      default: 0 
    },
    status: {
      type: String,
      enum: ["uploaded", "processing", "processed", "indexed", "failed"],
      default: "uploaded",
      index: true
    },
    ocrCompleted: {
      type: Boolean,
      default: false
    },
    ocrError: {
      type: String,
      default: null
    }
  },
  { 
    timestamps: true 
  }
);

// Index for search by title/author
BookSchema.index({ title: "text", author: "text" });

module.exports = mongoose.model("Book", BookSchema);
