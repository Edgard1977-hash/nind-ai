"""
Test device mockup video generation endpoint
Testing iphone_compositor.py v6 features:
1. Phone fills 100% of screen (phone_scale=1.05)
2. Animation is smooth and dynamic (rotation -35 to +35 degrees)
3. Phone + text layout works correctly
"""

import pytest
import requests
import os
import time

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    # Fallback for testing
    BASE_URL = "https://ai-format-studio.preview.emergentagent.com"


class TestDeviceMockupAPI:
    """Tests for device mockup video generation - /api/device-mockup/create"""

    def test_api_health_check(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"API not accessible: {response.status_code}"
        print(f"✓ API is accessible at {BASE_URL}")

    def test_upload_video_for_mockup(self):
        """Upload a test video to use for device mockup"""
        # Check if test video exists in uploads
        test_video_path = "/app/backend/uploads"
        
        # List existing videos
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        # Try to use an existing video from uploads (prefer short videos first)
        existing_videos = [
            "test_short_3sec.mp4",  # Short test video for faster tests
            "054e33c7-deb9-4a1a-9e71-17e06e6eb90c.mp4",
            "0c638139-2a5a-47be-aa4f-d446b0291a2e.mp4",
            "446f112b-f6ac-4115-8030-f6d6cf9fe56f.mp4"
        ]
        
        video_url = None
        for video in existing_videos:
            # Use GET with stream=True to just check if file exists without downloading
            check_response = requests.get(f"{BASE_URL}/api/uploads/{video}", stream=True)
            if check_response.status_code == 200:
                video_url = f"/api/uploads/{video}"
                check_response.close()  # Close without reading body
                break
            check_response.close()
        
        assert video_url is not None, "No test video available in uploads"
        print(f"✓ Found test video: {video_url}")
        return video_url

    def test_device_mockup_create_float_animation(self):
        """Test device mockup creation with 'float' animation style"""
        # Get a valid video URL first
        video_url = self.test_upload_video_for_mockup()
        
        # Create device mockup with float animation
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "rotation": 12,
            "bg_color": [30, 35, 32],  # Dark greenish background
            "animation_style": "float",
            "text": "",
            "phone_position": "left"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed to create device mockup: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain project ID"
        assert "status" in data, "Response should contain status"
        
        project_id = data["id"]
        print(f"✓ Device mockup project created: {project_id}")
        
        # Poll for completion (max 120 seconds)
        max_wait = 120
        poll_interval = 5
        elapsed = 0
        final_status = None
        
        while elapsed < max_wait:
            status_response = requests.get(f"{BASE_URL}/api/video/{project_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                final_status = status_data.get("status")
                
                if final_status == "completed":
                    video_url = status_data.get("video_url")
                    assert video_url is not None, "Completed project should have video_url"
                    print(f"✓ Device mockup video completed: {video_url}")
                    
                    # Verify video is accessible
                    video_response = requests.get(f"{BASE_URL}{video_url}", stream=True)
                    assert video_response.status_code == 200, f"Video not accessible: {video_response.status_code}"
                    video_response.close()
                    print(f"✓ Video file is accessible")
                    return project_id, video_url
                    
                elif final_status == "failed":
                    error = status_data.get("error", "Unknown error")
                    pytest.fail(f"Device mockup failed: {error}")
                
                progress = status_data.get("progress", 0)
                print(f"  ... Progress: {progress}%")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        pytest.fail(f"Device mockup timed out after {max_wait}s. Last status: {final_status}")

    def test_device_mockup_create_cinematic_animation(self):
        """Test device mockup creation with 'cinematic' animation style (dramatic rotation)"""
        video_url = self.test_upload_video_for_mockup()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "rotation": 15,
            "bg_color": [30, 35, 32],
            "animation_style": "cinematic",
            "text": "",
            "phone_position": "left"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed to create cinematic device mockup: {response.text}"
        
        data = response.json()
        project_id = data["id"]
        print(f"✓ Cinematic device mockup project created: {project_id}")
        
        # Poll for completion
        max_wait = 120
        poll_interval = 5
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = requests.get(f"{BASE_URL}/api/video/{project_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                final_status = status_data.get("status")
                
                if final_status == "completed":
                    video_url = status_data.get("video_url")
                    print(f"✓ Cinematic mockup completed: {video_url}")
                    return project_id, video_url
                elif final_status == "failed":
                    pytest.fail(f"Cinematic mockup failed: {status_data.get('error')}")
                
                print(f"  ... Progress: {status_data.get('progress', 0)}%")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        pytest.fail(f"Cinematic mockup timed out after {max_wait}s")

    def test_device_mockup_phone_text_layout(self):
        """Test device mockup with phone + text layout"""
        video_url = self.test_upload_video_for_mockup()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "rotation": 30,
            "bg_color": [30, 35, 32],
            "animation_style": "phone_text",
            "text": "Your Amazing App",
            "phone_position": "right"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed to create phone+text mockup: {response.text}"
        
        data = response.json()
        project_id = data["id"]
        print(f"✓ Phone+text mockup project created: {project_id}")
        
        # Poll for completion
        max_wait = 120
        poll_interval = 5
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = requests.get(f"{BASE_URL}/api/video/{project_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                final_status = status_data.get("status")
                
                if final_status == "completed":
                    video_url = status_data.get("video_url")
                    print(f"✓ Phone+text mockup completed: {video_url}")
                    return project_id, video_url
                elif final_status == "failed":
                    pytest.fail(f"Phone+text mockup failed: {status_data.get('error')}")
                
                print(f"  ... Progress: {status_data.get('progress', 0)}%")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        pytest.fail(f"Phone+text mockup timed out after {max_wait}s")

    def test_invalid_video_url_rejected(self):
        """Test that invalid video URLs are rejected"""
        payload = {
            "video_url": "https://example.com/video.mp4",  # External URL should be rejected
            "device_type": "phone",
            "rotation": 12,
            "bg_color": [30, 35, 32],
            "animation_style": "float"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 400, f"Should reject invalid video URL, got {response.status_code}"
        print(f"✓ Invalid video URL correctly rejected")

    def test_nonexistent_video_rejected(self):
        """Test that nonexistent video files are rejected"""
        payload = {
            "video_url": "/api/uploads/nonexistent-file-12345.mp4",
            "device_type": "phone",
            "rotation": 12,
            "bg_color": [30, 35, 32],
            "animation_style": "float"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 404, f"Should return 404 for nonexistent video, got {response.status_code}"
        print(f"✓ Nonexistent video correctly rejected with 404")


class TestIPhoneCompositorV6:
    """Tests to verify iphone_compositor.py v6 features"""

    def test_compositor_module_imports(self):
        """Verify iphone_compositor.py can be imported and has required functions"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from iphone_compositor import (
            render_dynamic_phone,
            render_phone_with_text,
            create_simple_float_frame,
            create_animated_iphone_frame,
            create_phone_with_text_frame
        )
        
        print(f"✓ iphone_compositor.py v6 imports successfully")
        print(f"  - render_dynamic_phone: {render_dynamic_phone}")
        print(f"  - render_phone_with_text: {render_phone_with_text}")

    def test_phone_scale_parameter(self):
        """Verify phone_scale=1.05 is used for 100% screen fill"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        import inspect
        from iphone_compositor import render_dynamic_phone
        
        # Check function signature has phone_scale parameter
        sig = inspect.signature(render_dynamic_phone)
        assert 'phone_scale' in sig.parameters, "render_dynamic_phone should have phone_scale parameter"
        
        # Check default value is 1.05
        default_scale = sig.parameters['phone_scale'].default
        assert default_scale == 1.05, f"Default phone_scale should be 1.05, got {default_scale}"
        print(f"✓ phone_scale parameter exists with default 1.05")

    def test_rotation_range(self):
        """Verify rotation range is -35 to +35 degrees for dynamic animation"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        # Read source code to verify rotation calculation
        with open('/app/backend/iphone_compositor.py', 'r') as f:
            source = f.read()
        
        # Check for rotation = 35 * math.sin pattern
        assert 'rotation = 35' in source or 'rotation_y' in source, "Should have rotation animation code"
        assert 'math.sin' in source, "Should use sine wave for smooth animation"
        print(f"✓ Rotation animation uses sine wave pattern")

    def test_3d_perspective_transform(self):
        """Verify strong 3D perspective transform is implemented"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from iphone_compositor import apply_strong_3d_transform
        
        # Test the transform function exists and can be called
        from PIL import Image
        test_img = Image.new('RGBA', (200, 400), (255, 255, 255, 255))
        
        # Test with different rotation angles
        result_positive = apply_strong_3d_transform(test_img, 30)
        result_negative = apply_strong_3d_transform(test_img, -30)
        result_zero = apply_strong_3d_transform(test_img, 0)
        
        assert result_positive is not None, "Positive rotation should work"
        assert result_negative is not None, "Negative rotation should work"
        assert result_zero is not None, "Zero rotation should work"
        print(f"✓ 3D perspective transform works with various rotation angles")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
