import React from 'react';
import './ProductList.css';
import ProductCard from './ProductCard';

function ProductList({ products, loading }) {
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Searching for healthy products...</p>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="empty-state">
        <p>No products found. Try searching for something!</p>
      </div>
    );
  }

  return (
    <div className="product-list">
      {products.map((product, index) => (
        <ProductCard key={index} product={product} />
      ))}
    </div>
  );
}

export default ProductList;
