// Central export point for all models
const Book = require("./Book");
const Page = require("./Page");
const User = require("./User");
const SearchLog = require("./SearchLog");
const IndexTerm = require("./IndexTerm");

module.exports = {
  Book,
  Page,
  User,
  SearchLog,
  IndexTerm
};
