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

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
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
                character_types = response.get('character_types', [])
                gameplay_types = response.get('gameplay_types', [])
                
                print(f"  📊 Found {len(formats)} formats, {len(categories)} categories")
                print(f"  📊 Found {len(character_types)} character types, {len(gameplay_types)} gameplay types")
                
                # Check if we have exactly 9 formats
                if len(formats) != 9:
                    print(f"  ❌ Expected 9 formats, found {len(formats)}")
                    return False
                else:
                    print(f"  ✅ Correct number of formats (9)")
                
                # Check for new formats specifically
                format_ids = [f['id'] for f in formats]
                new_formats = ['gameplay_clip', 'ai_story', 'character_explainer']
                missing_new_formats = [f for f in new_formats if f not in format_ids]
                if missing_new_formats:
                    print(f"  ❌ Missing new formats: {missing_new_formats}")
                    return False
                else:
                    print(f"  ✅ All new formats found: {new_formats}")
                
                # Check character types (should be 6)
                if len(character_types) != 6:
                    print(f"  ❌ Expected 6 character types, found {len(character_types)}")
                    return False
                else:
                    print(f"  ✅ Correct number of character types (6)")
                    char_ids = [c['id'] for c in character_types]
                    print(f"  📝 Character types: {char_ids}")
                
                # Check gameplay types (should be 6)
                if len(gameplay_types) != 6:
                    print(f"  ❌ Expected 6 gameplay types, found {len(gameplay_types)}")
                    return False
                else:
                    print(f"  ✅ Correct number of gameplay types (6)")
                    gameplay_ids = [g['id'] for g in gameplay_types]
                    print(f"  📝 Gameplay types: {gameplay_ids}")
                
                # Check format fields
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

    def test_generate_gameplay_clip(self):
        """Test gameplay clip generation with YouTube URL and gameplay type"""
        success, response = self.run_test(
            "Generate Gameplay Clip",
            "POST",
            "api/video/generate",
            200,
            data={
                "prompt": "Смешные моменты из стрима",
                "format_id": "gameplay_clip",
                "language": "auto",
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "gameplay_type": "minecraft_parkour"
            },
            timeout=15
        )
        
        if success and response:
            if 'id' in response and 'status' in response:
                print(f"  📝 Created gameplay clip project ID: {response['id']}")
                print(f"  📊 Initial status: {response['status']}")
            else:
                print(f"  ❌ Invalid response - missing 'id' or 'status'")
                return False
        
        return success

    def test_generate_character_explainer(self):
        """Test character explainer generation with character type"""
        success, response = self.run_test(
            "Generate Character Explainer",
            "POST",
            "api/video/generate",
            200,
            data={
                "prompt": "Как заработать деньги",
                "format_id": "character_explainer",
                "language": "auto",
                "character_type": "kitten"
            },
            timeout=15
        )
        
        if success and response:
            if 'id' in response and 'status' in response:
                print(f"  📝 Created character explainer project ID: {response['id']}")
                print(f"  📊 Initial status: {response['status']}")
            else:
                print(f"  ❌ Invalid response - missing 'id' or 'status'")
                return False
        
        return success

    def test_generate_ai_story(self):
        """Test AI story generation"""
        success, response = self.run_test(
            "Generate AI Story",
            "POST",
            "api/video/generate",
            200,
            data={
                "prompt": "Страшная история про заброшенный дом",
                "format_id": "ai_story",
                "language": "auto"
            },
            timeout=15
        )
        
        if success and response:
            if 'id' in response and 'status' in response:
                print(f"  📝 Created AI story project ID: {response['id']}")
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
    
    # Test 2: Get formats (most critical test for new formats)
    result2 = tester.test_get_formats()
    test_results.append(("Get Formats", result2))
    
    # Test 3: Generate regular video
    result3 = tester.test_generate_video()
    test_results.append(("Generate Video", result3))
    
    # Test 4: Generate gameplay clip (new format)
    result4 = tester.test_generate_gameplay_clip()
    test_results.append(("Generate Gameplay Clip", result4))
    
    # Test 5: Generate character explainer (new format)
    result5 = tester.test_generate_character_explainer()
    test_results.append(("Generate Character Explainer", result5))
    
    # Test 6: Generate AI story (new format)
    result6 = tester.test_generate_ai_story()
    test_results.append(("Generate AI Story", result6))
    
    # Test 7: Get video project (only if generation succeeded)
    if result3:
        result7 = tester.test_get_video_project()
        test_results.append(("Get Video Project", result7))
        
        # Wait a bit and check again to see progress
        print("\n⏳ Waiting 3 seconds to check progress...")
        time.sleep(3)
        result8 = tester.test_get_video_project()
        test_results.append(("Check Progress", result8))
    
    # Test 8: Get all videos
    result9 = tester.test_get_all_videos()
    test_results.append(("Get All Videos", result9))
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 Final Test Results:")
    print("=" * 50)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED" 
        print(f"{test_name:<30} | {status}")
    
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