import React, { useState } from 'react';
import './SearchBar.css';

function SearchBar({ onSearch, loading }) {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      onSearch(searchTerm);
    }
  };

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search for products at HEB (e.g., 'chicken', 'bread', 'milk')..."
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
