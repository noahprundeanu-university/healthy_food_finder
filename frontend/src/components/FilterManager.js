import React, { useState } from 'react';
import './FilterManager.css';

function FilterManager({ filters, onAddFilter, onRemoveFilter }) {
  const [newFilter, setNewFilter] = useState('');

  const handleAddFilter = (e) => {
    e.preventDefault();
    if (newFilter.trim()) {
      onAddFilter(newFilter);
      setNewFilter('');
    }
  };

  return (
    <div className="filter-manager">
      <h2>Active Filters</h2>
      <p className="filter-description">
        Products containing these ingredients will be filtered out:
      </p>

      <form onSubmit={handleAddFilter} className="add-filter-form">
        <input
          type="text"
          value={newFilter}
          onChange={(e) => setNewFilter(e.target.value)}
          placeholder="Add a filter (e.g., 'sugar', 'preservatives')..."
          className="filter-input"
        />
        <button type="submit" className="add-filter-button">
          Add Filter
        </button>
      </form>

      <div className="filters-list">
        {filters.length === 0 ? (
          <p className="no-filters">No filters active</p>
        ) : (
          filters.map((filter, index) => (
            <div key={index} className="filter-tag">
              <span>{filter}</span>
              <button
                onClick={() => onRemoveFilter(filter)}
                className="remove-filter-button"
                aria-label={`Remove ${filter} filter`}
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default FilterManager;
