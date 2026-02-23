const mongoose = require("mongoose");

const SearchLogSchema = new mongoose.Schema(
  {
    userId: { 
      type: mongoose.Schema.Types.ObjectId, 
      ref: "User", 
      default: null,
      index: true 
    },
    query: { 
      type: String, 
      required: true,
      trim: true 
    },
    topResults: [
      {
        bookId: { 
          type: mongoose.Schema.Types.ObjectId, 
          ref: "Book" 
        },
        pageId: { 
          type: mongoose.Schema.Types.ObjectId, 
          ref: "Page" 
        },
        score: { 
          type: Number 
        }
      }
    ],
    resultCount: {
      type: Number,
      default: 0
    },
    executionTimeMs: {
      type: Number,
      default: 0
    }
  },
  { 
    timestamps: true 
  }
);

// Index for recent searches
SearchLogSchema.index({ createdAt: -1 });

// Index for user search history
SearchLogSchema.index({ userId: 1, createdAt: -1 });

module.exports = mongoose.model("SearchLog", SearchLogSchema);
