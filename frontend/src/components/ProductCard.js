import React, { useState } from 'react';
import './ProductCard.css';

function ProductCard({ product }) {
  const [addingToCart, setAddingToCart] = useState(false);

  const handleAddToCart = async () => {
    setAddingToCart(true);
    try {
      const response = await fetch('/api/cart/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_url: product.url
        }),
      });

      const data = await response.json();
      
      if (data.success && product.url) {
        // Open Kroger product page in new tab so user can add to cart
        window.open(product.url, '_blank');
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('Error adding to cart. Please try again.');
    } finally {
      setAddingToCart(false);
    }
  };

  return (
    <div className="product-card">
      {product.image && (
        <div className="product-image">
          <img src={product.image} alt={product.name} />
        </div>
      )}
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        {product.price && product.price !== 'N/A' && (
          <p className="product-price">{product.price}</p>
        )}
        {product.ingredients && (
          <div className="product-ingredients">
            <strong>Ingredients:</strong>
            <p className="ingredients-text">{product.ingredients}</p>
          </div>
        )}
        <div className="product-actions">
          {product.url && (
            <button
              className="add-to-cart-button"
              onClick={handleAddToCart}
              disabled={addingToCart}
            >
              {addingToCart ? 'Opening...' : 'View on Kroger'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProductCard;
