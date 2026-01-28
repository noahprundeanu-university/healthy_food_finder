import React, { useState } from 'react';
import './SearchBar.css';

function SearchBar({ onSearch, loading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStore, setSelectedStore] = useState('kroger');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      onSearch(searchTerm, selectedStore);
    }
  };

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="store-selector">
          <label htmlFor="store-select">Store: </label>
          <select
            id="store-select"
            value={selectedStore}
            onChange={(e) => setSelectedStore(e.target.value)}
            className="store-select"
            disabled={loading}
          >
            <option value="kroger">Kroger</option>
            <option value="heb">HEB</option>
          </select>
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search for products (e.g., 'chicken', 'bread', 'milk')..."
          className="search-input"
          disabled={loading}
        />
        <button
          type="submit"
          className="search-button"
          disabled={loading || !searchTerm.trim()}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
    </div>
  );
}

export default SearchBar;
