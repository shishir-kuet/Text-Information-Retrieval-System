const mongoose = require("mongoose");

async function connectDB() {
  const uri = process.env.MONGO_URI;
  
  if (!uri) {
    throw new Error("MONGO_URI is missing in environment variables");
  }

  mongoose.set("strictQuery", true);
  await mongoose.connect(uri);
  
  console.log("✅ Connected to MongoDB");
  console.log(`📁 Database: ${mongoose.connection.name}`);
}

module.exports = connectDB;
