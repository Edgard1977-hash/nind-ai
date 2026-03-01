import requests
import sys
import json
import time
from datetime import datetime

class VideoAPITester:
    def __init__(self, base_url="https://ai-format-studio.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=10):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else type(response_data)}")
                except:
                    print("Response is not JSON")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response text: {response.text[:500]}")

            return success, response.json() if response.status_code < 500 and response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET", 
            "api/",
            200
        )
        return success

    def test_get_formats(self):
        """Test getting video formats"""
        success, response = self.run_test(
            "Get Video Formats",
            "GET",
            "api/formats",
            200
        )
        
        if success and response:
            # Validate response structure
            if 'formats' in response and 'categories' in response:
                formats = response['formats']
                categories = response['categories']
                print(f"  📊 Found {len(formats)} formats and {len(categories)} categories")
                
                # Check if we have expected format fields
                if formats and len(formats) > 0:
                    format_sample = formats[0]
                    required_fields = ['id', 'name', 'name_ru', 'description', 'category']
                    missing_fields = [field for field in required_fields if field not in format_sample]
                    if missing_fields:
                        print(f"  ⚠️ Missing fields in format: {missing_fields}")
                    else:
                        print(f"  ✅ Format structure is valid")
                else:
                    print(f"  ❌ No formats found")
                    return False
            else:
                print(f"  ❌ Invalid response structure - missing 'formats' or 'categories'")
                return False
        
        return success

    def test_generate_video(self):
        """Test video generation"""
        success, response = self.run_test(
            "Generate Video",
            "POST",
            "api/video/generate",
            200,
            data={
                "prompt": "Топ-5 самых интересных фактов о космосе",
                "format_id": "news", 
                "language": "auto"
            },
            timeout=15
        )
        
        if success and response:
            if 'id' in response and 'status' in response:
                self.project_id = response['id']
                print(f"  📝 Created project ID: {self.project_id}")
                print(f"  📊 Initial status: {response['status']}")
            else:
                print(f"  ❌ Invalid response - missing 'id' or 'status'")
                return False
        
        return success

    def test_get_video_project(self):
        """Test getting video project status"""
        if not self.project_id:
            print("❌ No project ID to test with")
            return False
        
        success, response = self.run_test(
            "Get Video Project",
            "GET",
            f"api/video/{self.project_id}",
            200
        )
        
        if success and response:
            status = response.get('status', 'unknown')
            progress = response.get('progress', 0)
            message = response.get('progress_message', 'No message')
            print(f"  📊 Status: {status}, Progress: {progress}%, Message: {message}")
            
            # Check required fields
            required_fields = ['id', 'prompt', 'format_id', 'status', 'progress']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"  ⚠️ Missing project fields: {missing_fields}")
            else:
                print(f"  ✅ Project structure is valid")
        
        return success

    def test_get_all_videos(self):
        """Test getting all video projects"""
        success, response = self.run_test(
            "Get All Video Projects", 
            "GET",
            "api/videos",
            200
        )
        
        if success and response:
            if 'projects' in response:
                projects = response['projects']
                print(f"  📊 Found {len(projects)} total projects")
            else:
                print(f"  ❌ Invalid response - missing 'projects' field")
                return False
        
        return success

def main():
    print("🚀 Starting Video Generation API Tests")
    print("=" * 50)
    
    # Setup
    tester = VideoAPITester()
    
    # Run tests in sequence
    test_results = []
    
    # Test 1: Root endpoint
    result1 = tester.test_root_endpoint()
    test_results.append(("Root API", result1))
    
    # Test 2: Get formats
    result2 = tester.test_get_formats()
    test_results.append(("Get Formats", result2))
    
    # Test 3: Generate video
    result3 = tester.test_generate_video()
    test_results.append(("Generate Video", result3))
    
    # Test 4: Get video project (only if generation succeeded)
    if result3:
        result4 = tester.test_get_video_project()
        test_results.append(("Get Video Project", result4))
        
        # Wait a bit and check again to see progress
        print("\n⏳ Waiting 3 seconds to check progress...")
        time.sleep(3)
        result5 = tester.test_get_video_project()
        test_results.append(("Check Progress", result5))
    
    # Test 5: Get all videos
    result6 = tester.test_get_all_videos()
    test_results.append(("Get All Videos", result6))
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 Final Test Results:")
    print("=" * 50)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED" 
        print(f"{test_name:<20} | {status}")
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Return appropriate exit code
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())