import requests
import unittest
import os
import json
from datetime import datetime

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

class CatalogFilterSearchTest(unittest.TestCase):
    """Test suite for the catalog filter and search functionality"""

    def setUp(self):
        """Initialize test data"""
        # Initialize sample data
        try:
            requests.post(f"{API_URL}/init-data")
        except Exception as e:
            print(f"Error initializing data: {e}")
        
    def test_01_get_all_products(self):
        """Test getting all products"""
        print("\n🔍 Testing products endpoint...")
        response = requests.get(f"{API_URL}/products")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
        print(f"✅ Products endpoint returned {len(products)} products")
        
        # Verify we have 6 products as specified in the sample data
        self.assertEqual(len(products), 6, "Expected 6 products in the catalog")
        print("✅ Catalog has the expected 6 products")
        
        return products
    
    def test_02_product_specifications(self):
        """Test that products have the required specifications for filtering"""
        products = self.test_01_get_all_products()
        
        # Check that all products have specifications
        for product in products:
            self.assertIn('specifications', product)
            specs = product['specifications']
            
            # Check for required specification fields
            required_specs = ['Мощность охлаждения', 'Площадь помещения', 'Класс энергоэффективности']
            for spec in required_specs:
                self.assertIn(spec, specs, f"Product {product['name']} missing specification: {spec}")
        
        print("✅ All products have the required specifications for filtering")
        
        # Verify specific products have the expected specifications
        # Test case 1: Mitsubishi product
        mitsubishi = next((p for p in products if 'Mitsubishi' in p['name']), None)
        self.assertIsNotNone(mitsubishi, "Mitsubishi product not found")
        self.assertEqual(mitsubishi['specifications']['Мощность охлаждения'], "3.5 кВт")
        self.assertEqual(mitsubishi['specifications']['Площадь помещения'], "35 м²")
        self.assertEqual(mitsubishi['specifications']['Класс энергоэффективности'], "A+++")
        
        # Test case 2: Samsung product
        samsung = next((p for p in products if 'Samsung' in p['name']), None)
        self.assertIsNotNone(samsung, "Samsung product not found")
        
        print("✅ Products have the correct specifications for filtering")
        
    def test_03_verify_product_brands(self):
        """Verify that all required brands are present"""
        products = self.test_01_get_all_products()
        
        # Extract brands from product names
        brands = set()
        for product in products:
            brand_match = product['name'].split()[0]
            brands.add(brand_match)
        
        # Check that all required brands are present
        required_brands = {'Mitsubishi', 'Daikin', 'LG', 'Samsung', 'Panasonic', 'Haier'}
        for brand in required_brands:
            self.assertIn(brand, brands, f"Brand {brand} not found in products")
        
        print(f"✅ All required brands are present: {', '.join(required_brands)}")
    
    def test_04_verify_power_options(self):
        """Verify that all required power options are present"""
        products = self.test_01_get_all_products()
        
        # Extract power values
        power_values = set()
        for product in products:
            power = product['specifications'].get('Мощность охлаждения', '')
            if power:
                power_value = power.replace(' кВт', '')
                power_values.add(power_value)
        
        # Check that all required power options are present
        required_powers = {'2.5', '2.6', '3.5', '5.0'}
        for power in required_powers:
            self.assertIn(power, power_values, f"Power option {power} kW not found in products")
        
        print(f"✅ All required power options are present: {', '.join(required_powers)} kW")
    
    def test_05_verify_area_options(self):
        """Verify that all required area options are present"""
        products = self.test_01_get_all_products()
        
        # Extract area values
        area_values = set()
        for product in products:
            area = product['specifications'].get('Площадь помещения', '')
            if area:
                area_value = area.replace(' м²', '')
                area_values.add(area_value)
        
        # Check that all required area options are present
        required_areas = {'25', '26', '35', '50'}
        for area in required_areas:
            self.assertIn(area, area_values, f"Area option {area} m² not found in products")
        
        print(f"✅ All required area options are present: {', '.join(required_areas)} m²")
    
    def test_06_verify_efficiency_classes(self):
        """Verify that all required efficiency classes are present"""
        products = self.test_01_get_all_products()
        
        # Extract efficiency classes
        efficiency_classes = set()
        for product in products:
            efficiency = product['specifications'].get('Класс энергоэффективности', '')
            if efficiency:
                efficiency_classes.add(efficiency)
        
        # Check that all required efficiency classes are present
        required_classes = {'A++', 'A+++'}
        for cls in required_classes:
            self.assertIn(cls, efficiency_classes, f"Efficiency class {cls} not found in products")
        
        print(f"✅ All required efficiency classes are present: {', '.join(required_classes)}")
    
    def test_07_verify_price_ranges(self):
        """Verify that products have a range of prices for filtering"""
        products = self.test_01_get_all_products()
        
        # Extract prices
        prices = [product['price'] for product in products]
        min_price = min(prices)
        max_price = max(prices)
        
        # Check that we have a good range of prices
        self.assertGreater(max_price - min_price, 10000, "Price range is too small for meaningful filtering")
        
        # Check that we have products in different price ranges
        price_ranges = {
            'under_30000': 0,
            '30000_to_40000': 0,
            'over_40000': 0
        }
        
        for price in prices:
            if price < 30000:
                price_ranges['under_30000'] += 1
            elif 30000 <= price <= 40000:
                price_ranges['30000_to_40000'] += 1
            else:
                price_ranges['over_40000'] += 1
        
        # Ensure we have at least one product in each price range
        for range_name, count in price_ranges.items():
            self.assertGreater(count, 0, f"No products found in price range: {range_name}")
        
        print(f"✅ Products have a good distribution of prices for filtering")
        print(f"   Price range: {min_price} to {max_price} ₽")
        print(f"   Under 30,000₽: {price_ranges['under_30000']} products")
        print(f"   30,000₽ to 40,000₽: {price_ranges['30000_to_40000']} products")
        print(f"   Over 40,000₽: {price_ranges['over_40000']} products")

if __name__ == '__main__':
    print(f"🚀 Testing Catalog Filter and Search at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)