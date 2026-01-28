# Ingredient Extraction Plan

## Current Situation
- Search results return products with URLs pointing to full product pages
- Product pages contain ingredients in a specific HEB structure
- Current `get_product_details()` uses `requests` which fails due to bot protection
- Ingredients need to be extracted from product pages to filter unhealthy items

## Target Structure
HEB product pages have ingredients in this structure:
```html
<div class="sc-578c3839-3 frvaxi">
  <h4 class="sc-578c3839-2 ksAvle">Ingredients</h4>
  <span>artisan base dough(bakery flour(...))</span>
</div>
```

## Solution Plan

### 1. Update `get_product_details()` to use Selenium
   - Replace `requests.get()` with Selenium WebDriver
   - Use existing `create_selenium_driver()` function
   - Set quick timeouts (8-10 seconds) for fast ingredient fetching
   - Minimal wait times (1-2 seconds) since we only need ingredients

### 2. Target Specific HEB Ingredients Structure
   - Primary strategy: Look for `<div class="sc-578c3839-3 frvaxi">`
   - Find `<h4>` with "Ingredients" text
   - Extract text from `<span>` element within that div
   - Fallback strategies for other possible structures

### 3. Efficiency Optimizations
   - Use headless browser mode
   - Set page load timeout to 8-10 seconds
   - Minimal implicit waits (1-2 seconds)
   - Quick sleep after page load (1 second)
   - Parse page source directly instead of waiting for elements

### 4. Error Handling
   - Gracefully handle timeouts
   - Return None if ingredients can't be found
   - Log errors for debugging
   - Don't block search if ingredient fetching fails

### 5. Integration
   - Current flow already calls `get_product_details()` for each product
   - No changes needed to search endpoint
   - Products without ingredients will pass filter (assumed safe)

## Implementation Steps
1. Rewrite `get_product_details()` to use Selenium
2. Add specific HEB structure detection
3. Add fallback strategies
4. Test with real HEB product URLs
5. Commit changes
