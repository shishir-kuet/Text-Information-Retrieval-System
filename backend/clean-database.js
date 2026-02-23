// Clean database and start fresh
require("dotenv").config();
const mongoose = require("mongoose");
const { Book, Page, IndexTerm } = require("./src/models");

async function cleanDatabase() {
  try {
    await mongoose.connect(process.env.MONGODB_URI || "mongodb://localhost:27017/text_information_retrieval");
    console.log("✅ Connected to MongoDB");

    // Delete all data
    await Book.deleteMany({});
    await Page.deleteMany({});
    await IndexTerm.deleteMany({});

    console.log("✅ Deleted all books, pages, and index terms");

    await mongoose.disconnect();
    console.log("✅ Done - Database is clean");
  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
}

cleanDatabase();
