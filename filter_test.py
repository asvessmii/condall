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

class FilterFunctionalityTest(unittest.TestCase):
    """Test suite for the filter functionality in the catalog"""

    def setUp(self):
        """Initialize test data"""
        # Initialize sample data
        requests.post(f"{API_URL}/init-data")
        # Get all products for testing
        response = requests.get(f"{API_URL}/products")
        self.products = response.json()
        self.assertEqual(len(self.products), 6, "Expected 6 products in the test data")
        
    def test_01_product_specifications(self):
        """Test that products have the required specifications for filtering"""
        print("\n🔍 Testing product specifications...")
        
        # Check each product has the required specifications
        required_specs = ['Мощность охлаждения', 'Площадь помещения', 'Класс энергоэффективности']
        
        for product in self.products:
            self.assertIn('specifications', product)
            specs = product['specifications']
            
            for spec in required_specs:
                self.assertIn(spec, specs, f"Product {product['name']} is missing specification: {spec}")
            
            # Check power format (e.g., "3.5 кВт")
            power = specs['Мощность охлаждения']
            self.assertRegex(power, r'\d+(\.\d+)? кВт', f"Invalid power format: {power}")
            
            # Check area format (e.g., "35 м²")
            area = specs['Площадь помещения']
            self.assertRegex(area, r'\d+ м²', f"Invalid area format: {area}")
            
            # Check energy efficiency class format (e.g., "A+++")
            efficiency = specs['Класс энергоэффективности']
            self.assertRegex(efficiency, r'A\+{2,3}', f"Invalid efficiency format: {efficiency}")
        
        print("✅ All products have the required specifications in the correct format")
    
    def test_02_manufacturer_distribution(self):
        """Test the distribution of manufacturers in the test data"""
        print("\n🔍 Testing manufacturer distribution...")
        
        manufacturers = {}
        for product in self.products:
            brand_match = product['name'].split()[0]
            manufacturers[brand_match] = manufacturers.get(brand_match, 0) + 1
        
        print(f"Manufacturer distribution: {manufacturers}")
        
        # Check that we have the required manufacturers
        expected_manufacturers = ['Mitsubishi', 'Daikin', 'LG', 'Samsung', 'Panasonic', 'Haier']
        for manufacturer in expected_manufacturers:
            self.assertIn(manufacturer, manufacturers, f"Missing manufacturer: {manufacturer}")
        
        print("✅ All required manufacturers are present in the test data")
    
    def test_03_power_values(self):
        """Test the distribution of power values in the test data"""
        print("\n🔍 Testing power values distribution...")
        
        power_values = {}
        for product in self.products:
            power = product['specifications']['Мощность охлаждения'].replace(' кВт', '')
            power_values[power] = power_values.get(power, 0) + 1
        
        print(f"Power values distribution: {power_values}")
        
        # Check that we have the required power values
        expected_powers = ['2.5', '2.6', '3.5', '5.0']
        for power in expected_powers:
            self.assertTrue(any(p == power for p in power_values), f"Missing power value: {power}")
        
        print("✅ Required power values are present in the test data")
    
    def test_04_area_values(self):
        """Test the distribution of area values in the test data"""
        print("\n🔍 Testing area values distribution...")
        
        area_values = {}
        for product in self.products:
            area = product['specifications']['Площадь помещения'].replace(' м²', '')
            area_values[area] = area_values.get(area, 0) + 1
        
        print(f"Area values distribution: {area_values}")
        
        # Check that we have the required area values
        expected_areas = ['25', '26', '35', '50']
        for area in expected_areas:
            self.assertTrue(any(a == area for a in area_values), f"Missing area value: {area}")
        
        print("✅ Required area values are present in the test data")
    
    def test_05_efficiency_classes(self):
        """Test the distribution of efficiency classes in the test data"""
        print("\n🔍 Testing efficiency classes distribution...")
        
        efficiency_classes = {}
        for product in self.products:
            efficiency = product['specifications']['Класс энергоэффективности']
            efficiency_classes[efficiency] = efficiency_classes.get(efficiency, 0) + 1
        
        print(f"Efficiency classes distribution: {efficiency_classes}")
        
        # Check that we have the required efficiency classes
        expected_classes = ['A++', 'A+++']
        for cls in expected_classes:
            self.assertIn(cls, efficiency_classes, f"Missing efficiency class: {cls}")
        
        print("✅ Required efficiency classes are present in the test data")
    
    def test_06_price_range(self):
        """Test the price range in the test data"""
        print("\n🔍 Testing price range...")
        
        prices = [product['price'] for product in self.products]
        min_price = min(prices)
        max_price = max(prices)
        
        print(f"Price range: {min_price} - {max_price}")
        
        # Check that we have a reasonable price range
        self.assertGreater(max_price - min_price, 10000, "Price range is too narrow")
        
        print("✅ Price range is sufficient for testing filters")

if __name__ == '__main__':
    print(f"🚀 Testing filter functionality with API at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)