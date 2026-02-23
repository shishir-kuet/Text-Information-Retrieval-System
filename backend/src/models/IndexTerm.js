const mongoose = require("mongoose");

const IndexTermSchema = new mongoose.Schema(
  {
    term: { 
      type: String, 
      required: true, 
      unique: true, 
      index: true,
      lowercase: true,
      trim: true
    },
    df: { 
      type: Number, 
      required: true, 
      default: 0 
    },
    postings: [
      {
        pageId: { 
          type: mongoose.Schema.Types.ObjectId, 
          ref: "Page", 
          required: true 
        },
        tf: { 
          type: Number, 
          required: true 
        }
      }
    ]
  },
  { 
    timestamps: true 
  }
);

// Index for fast term lookup (primary use case)
IndexTermSchema.index({ term: 1 });

// Index for term search/autocomplete
IndexTermSchema.index({ term: "text" });

module.exports = mongoose.model("IndexTerm", IndexTermSchema);
