import requests
import json

def test_formats_api():
    """Quick test of the formats API"""
    url = "https://ai-format-studio.preview.emergentagent.com/api/formats"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check structure
        if 'formats' not in data or 'character_types' not in data or 'gameplay_types' not in data:
            print("❌ Missing required fields in response")
            return False
        
        formats = data['formats']
        character_types = data['character_types']
        gameplay_types = data['gameplay_types']
        
        print(f"✅ Found {len(formats)} formats")
        print(f"✅ Found {len(character_types)} character types")  
        print(f"✅ Found {len(gameplay_types)} gameplay types")
        
        # Check for new formats
        format_ids = [f['id'] for f in formats]
        new_formats = ['gameplay_clip', 'ai_story', 'character_explainer']
        
        for fmt in new_formats:
            if fmt in format_ids:
                print(f"✅ New format '{fmt}' found")
            else:
                print(f"❌ New format '{fmt}' missing")
                return False
        
        # Check counts
        if len(formats) == 9:
            print("✅ Correct number of formats (9)")
        else:
            print(f"❌ Expected 9 formats, got {len(formats)}")
            return False
            
        if len(character_types) == 6:
            print("✅ Correct number of character types (6)")
        else:
            print(f"❌ Expected 6 character types, got {len(character_types)}")
            return False
            
        if len(gameplay_types) == 6:
            print("✅ Correct number of gameplay types (6)")
        else:
            print(f"❌ Expected 6 gameplay types, got {len(gameplay_types)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_video_generation():
    """Quick test of video generation"""
    url = "https://ai-format-studio.preview.emergentagent.com/api/video/generate"
    
    # Test regular format
    data = {
        "prompt": "Test video",
        "format_id": "news",
        "language": "auto"
    }
    
    try:
        response = requests.post(url, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if 'id' in result and 'status' in result:
                print("✅ Video generation API working")
                return True
            else:
                print("❌ Invalid response structure")
                return False
        else:
            print(f"❌ Video generation failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in video generation: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Backend API Test")
    print("=" * 40)
    
    success1 = test_formats_api()
    success2 = test_video_generation()
    
    print("\n" + "=" * 40)
    if success1 and success2:
        print("✅ All critical backend tests passed!")
    else:
        print("❌ Some backend tests failed")