import React, { useState, useEffect } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import ProductList from './components/ProductList';
import FilterManager from './components/FilterManager';

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState({ total_found: 0, filtered_count: 0 });

  useEffect(() => {
    // Load user filters on mount
    loadFilters();
  }, []);

  const loadFilters = async () => {
    try {
      const response = await fetch('/api/filters?user_id=default');
      const data = await response.json();
      setFilters(data.filters || []);
    } catch (error) {
      console.error('Error loading filters:', error);
    }
  };

  const handleSearch = async (searchTerm, store = 'kroger') => {
    if (!searchTerm.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchTerm,
          user_id: 'default',
          store: store
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      if (data.products) {
        setProducts(data.products);
        setStats({
          total_found: data.total_found || 0,
          filtered_count: data.filtered_count || 0
        });
      } else {
        setProducts([]);
        setStats({ total_found: 0, filtered_count: 0 });
      }
    } catch (error) {
      console.error('Error searching products:', error);
      alert(`Error searching products: ${error.message || 'Please try again.'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddFilter = async (filterTerm) => {
    try {
      const response = await fetch('/api/filters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filter: filterTerm,
          user_id: 'default'
        }),
      });

      const data = await response.json();
      setFilters(data.filters || []);
    } catch (error) {
      console.error('Error adding filter:', error);
      alert('Error adding filter. Please try again.');
    }
  };

  const handleRemoveFilter = async (filterTerm) => {
    try {
      const response = await fetch('/api/filters', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filter: filterTerm,
          user_id: 'default'
        }),
      });

      const data = await response.json();
      setFilters(data.filters || []);
    } catch (error) {
      console.error('Error removing filter:', error);
      alert('Error removing filter. Please try again.');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🥗 Healthy Food Finder</h1>
        <p className="subtitle">Filter out unhealthy ingredients from HEB products</p>
      </header>

      <main className="App-main">
        <div className="controls">
          <button
            className="filter-toggle"
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Hide' : 'Show'} Filters ({filters.length})
          </button>
        </div>

        {showFilters && (
          <FilterManager
            filters={filters}
            onAddFilter={handleAddFilter}
            onRemoveFilter={handleRemoveFilter}
          />
        )}

        <SearchBar onSearch={handleSearch} loading={loading} />

        {stats.total_found > 0 && (
          <div className="stats">
            <p>
              Found {stats.filtered_count} healthy products out of {stats.total_found} total
            </p>
          </div>
        )}

        <ProductList products={products} loading={loading} />
      </main>
    </div>
  );
}

export default App;
