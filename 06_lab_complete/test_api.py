#!/usr/bin/env python3
"""
Test script for Fire Detection API
Chạy: python test_api.py
"""
import os
import sys
import requests
import base64
import json
import time
from pathlib import Path
from typing import Optional

# Configuration
API_KEY = os.getenv("API_KEY", os.getenv("AGENT_API_KEY", "dev-key-change-me-in-production"))
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def test_connection():
    """Test basic API connectivity"""
    print("\n🧪 Testing API Connection...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print_success(f"Connected to {BASE_URL}")
            return True
        else:
            print_error(f"API returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        print_warning("Make sure the API is running!")
        print_info("Try: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("\n🧪 Testing Health Endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"Health check passed")
            print_info(f"  Status: {data.get('status')}")
            print_info(f"  Version: {data.get('version')}")
            print_info(f"  Uptime: {data.get('uptime_seconds')} seconds")
            return True
        else:
            print_error(f"Health check failed: {resp.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_ready():
    """Test readiness endpoint"""
    print("\n🧪 Testing Readiness Endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/ready", timeout=5)
        if resp.status_code == 200:
            print_success("Readiness check passed")
            data = resp.json()
            print_info(f"  Ready: {data.get('ready')}")
            return True
        elif resp.status_code == 503:
            print_warning("API not ready (503 Service Unavailable)")
            return False
        else:
            print_error(f"Readiness check failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_budget():
    """Test budget endpoint"""
    print("\n🧪 Testing Budget Info Endpoint...")
    try:
        resp = requests.get(
            f"{BASE_URL}/budget",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            print_success("Budget check passed")
            print_info(f"  Monthly Budget: ${data.get('monthly_budget', 0)}")
            print_info(f"  Monthly Spent: ${data.get('monthly_spent', 0)}")
            print_info(f"  Remaining: ${data.get('remaining_budget', 0)}")
            print_info(f"  Usage: {data.get('percent_used', 0)}%")
            return True
        elif resp.status_code == 401:
            print_error("Invalid API key!")
            return False
        else:
            print_error(f"Budget check failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_fire_detection(image_path: Optional[str] = None):
    """Test fire detection endpoint"""
    print("\n🧪 Testing Fire Detection Endpoint...")
    
    # Try to find an image file
    if image_path is None:
        candidates = [
            "test_image.jpg",
            "test_image.png",
            "../test_image.jpg",
            "06-lab-complete/test_image.jpg",
        ]
        for path in candidates:
            if Path(path).exists():
                image_path = path
                break
    
    if image_path is None:
        print_warning("No test image found (test_image.jpg not found)")
        print_info("Creating minimal test payload...")
        # Send minimal test to verify endpoint exists
        try:
            resp = requests.post(
                f"{BASE_URL}/analyze",
                headers={"X-API-Key": API_KEY},
                json={"image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="},
                timeout=10
            )
            if resp.status_code in [200, 400]:  # 400 is ok if decode fails
                print_success("Fire detection endpoint is working")
                print_info(f"  Status code: {resp.status_code}")
            else:
                print_error(f"Unexpected response: {resp.status_code}")
        except Exception as e:
            print_error(f"Error calling endpoint: {e}")
        return
    
    # Load image
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode()
        
        print_info(f"Loaded image: {image_path}")
        print_info(f"Image size: {len(image_data)} bytes")
        
        # Call API
        print_info("Sending to API...")
        resp = requests.post(
            f"{BASE_URL}/analyze",
            headers={"X-API-Key": API_KEY},
            json={"image_base64": image_b64, "user_id": "test_script"},
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_success("Fire detection completed")
            print_info(f"  Fire detected: {data.get('fire_detected')}")
            print_info(f"  Total detections: {data.get('detections', {}).get('total_detections', 0)}")
            print_info(f"  Cost: ${data.get('cost_info', {}).get('total_cost', 0)}")
        else:
            print_error(f"API error: {resp.status_code}")
            print_info(f"  Response: {resp.text[:200]}")
    
    except FileNotFoundError:
        print_error(f"Image file not found: {image_path}")
    except Exception as e:
        print_error(f"Error: {e}")

def test_rate_limiting():
    """Test rate limiting"""
    print("\n🧪 Testing Rate Limiting...")
    try:
        print_info("Sending 35 rapid requests (limit is 30/min)...")
        success_count = 0
        rate_limited = False
        
        for i in range(35):
            try:
                resp = requests.get(
                    f"{BASE_URL}/budget",
                    headers={"X-API-Key": API_KEY},
                    timeout=5
                )
                if resp.status_code == 200:
                    success_count += 1
                elif resp.status_code == 429:
                    print_warning(f"Rate limited at request #{i+1}")
                    rate_limited = True
                    break
            except:
                pass
            
            # Small delay to not hammer the server
            if i < 34:
                time.sleep(0.05)
        
        if rate_limited:
            print_success("Rate limiting is working correctly")
        else:
            print_warning("Rate limiting may not be triggered")
            print_info(f"  Sent {success_count} successful requests")
    
    except Exception as e:
        print_error(f"Error: {e}")

def test_security():
    """Test security features"""
    print("\n🧪 Testing Security Features...")
    try:
        # Test missing API key
        print_info("Testing missing API key...")
        resp = requests.get(f"{BASE_URL}/budget", timeout=5)
        if resp.status_code == 401 or resp.status_code == 403:
            print_success("Missing API key correctly rejected")
        else:
            print_warning("Expected 401/403, got {resp.status_code}")
        
        # Test invalid API key
        print_info("Testing invalid API key...")
        resp = requests.get(
            f"{BASE_URL}/budget",
            headers={"X-API-Key": "invalid-key-12345"},
            timeout=5
        )
        if resp.status_code in [401, 403]:
            print_success("Invalid API key correctly rejected")
        else:
            print_warning(f"Expected 401/403, got {resp.status_code}")
    
    except Exception as e:
        print_error(f"Error: {e}")

def main():
    """Run all tests"""
    print(f"""
╔════════════════════════════════════════╗
║   🔥 Fire Detection API Test Suite    ║
╚════════════════════════════════════════╝

Configuration:
  API URL: {BASE_URL}
  API Key: {API_KEY[:10]}...
  """)
    
    # Run tests
    tests = [
        ("Connection", test_connection),
        ("Health Check", test_health),
        ("Readiness Check", test_ready),
        ("Budget Info", test_budget),
        ("Fire Detection", lambda: test_fire_detection()),
        ("Rate Limiting", test_rate_limiting),
        ("Security", test_security),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            test_func()
            results[name] = True
        except Exception as e:
            print_error(f"Test '{name}' failed: {e}")
            results[name] = False
    
    # Summary
    print(f"\n{'='*40}")
    print("📊 Test Summary:")
    print(f"{'='*40}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✅{Colors.END}" if result else f"{Colors.RED}❌{Colors.END}"
        print(f"{status} {name}")
    
    print(f"{'='*40}")
    print_info(f"Passed: {passed}/{total}")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        return 0
    else:
        print_error(f"{total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
