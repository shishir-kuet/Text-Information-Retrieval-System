// Fix book status to allow indexing
require("dotenv").config();
const mongoose = require("mongoose");
const Book = require("./src/models/Book");

async function fixBookStatus() {
  try {
    await mongoose.connect(process.env.MONGODB_URI || "mongodb://localhost:27017/text_information_retrieval");
    console.log("✅ Connected to MongoDB");

    // Update the failed book to processed status
    const result = await Book.updateOne(
      { _id: "699cdb8f9beb92f3dcceb7e7" },
      { 
        $set: { 
          status: "processed",
          ocrError: null
        } 
      }
    );

    console.log("✅ Book status updated:", result);

    // Show all books
    const books = await Book.find({});
    console.log("\n📚 All books:");
    books.forEach(book => {
      console.log(`  - ${book.title} (${book._id}): ${book.status}`);
    });

    await mongoose.disconnect();
    console.log("\n✅ Done");
  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
}

fixBookStatus();
