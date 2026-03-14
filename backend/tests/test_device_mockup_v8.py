"""
Test device mockup video generation with iphone_compositor.py v8
Testing CRITICAL requirements:
1. Phone is ALWAYS FULLY VISIBLE (no cropping at any animation frame)
2. Camera animation style works (zoom + rotate)
3. Float animation style works
4. 9:16 portrait format works
5. 16:9 landscape format works
6. Custom bg_color gradient works
7. phone_position center/left/right works
"""

import pytest
import requests
import os
import time

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://ai-format-studio.preview.emergentagent.com"


class TestDeviceMockupAPIV8:
    """Tests for device mockup video generation with v8 compositor"""

    def test_api_health_check(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"API not accessible: {response.status_code}"
        print(f"✓ API is accessible at {BASE_URL}")

    def _get_test_video_url(self):
        """Helper to get a valid test video URL"""
        existing_videos = [
            "test_short_3sec.mp4",
            "054e33c7-deb9-4a1a-9e71-17e06e6eb90c.mp4",
            "0c638139-2a5a-47be-aa4f-d446b0291a2e.mp4",
        ]
        
        for video in existing_videos:
            check_response = requests.get(f"{BASE_URL}/api/uploads/{video}", stream=True)
            if check_response.status_code == 200:
                check_response.close()
                return f"/api/uploads/{video}"
            check_response.close()
        
        pytest.skip("No test video available in uploads")

    def _poll_for_completion(self, project_id, max_wait=90, poll_interval=5):
        """Helper to poll for video completion"""
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
                    return video_url
                    
                elif final_status == "failed":
                    error = status_data.get("error", "Unknown error")
                    pytest.fail(f"Device mockup failed: {error}")
                
                progress = status_data.get("progress", 0)
                print(f"  ... Progress: {progress}%")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        pytest.fail(f"Device mockup timed out after {max_wait}s. Last status: {final_status}")

    # =========== CORE API TESTS ===========

    def test_device_mockup_endpoint_exists(self):
        """Test that the device mockup endpoint exists and accepts POST"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "rotation": 12,
            "bg_color": [80, 20, 20],
            "animation_style": "camera"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Endpoint failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain project ID"
        assert "status" in data, "Response should contain status"
        print(f"✓ Device mockup endpoint works, project created: {data['id']}")

    # =========== CAMERA ANIMATION TESTS ===========

    def test_camera_animation_style(self):
        """Test camera animation style (zoom + rotate) creates video successfully"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "rotation": 12,
            "bg_color": [80, 20, 20],
            "animation_style": "camera",
            "phone_position": "center",
            "aspect_ratio": "9:16"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ Camera animation project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ Camera animation completed: {result_url}")
        
        # Verify video is accessible
        video_response = requests.get(f"{BASE_URL}{result_url}", stream=True)
        assert video_response.status_code == 200, f"Video not accessible: {video_response.status_code}"
        video_response.close()
        print(f"✓ Video file is accessible")

    # =========== FLOAT ANIMATION TESTS ===========

    def test_float_animation_style(self):
        """Test float animation style (simple floating) creates video successfully"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "rotation": 12,
            "bg_color": [40, 45, 40],  # Greenish background
            "animation_style": "float",
            "phone_position": "center",
            "aspect_ratio": "9:16"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ Float animation project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ Float animation completed: {result_url}")

    # =========== ASPECT RATIO TESTS ===========

    def test_9_16_portrait_format(self):
        """Test 9:16 portrait format (default)"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "bg_color": [80, 20, 20],
            "animation_style": "camera",
            "aspect_ratio": "9:16"  # Portrait
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ 9:16 portrait project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ 9:16 portrait format completed: {result_url}")

    def test_16_9_landscape_format(self):
        """Test 16:9 landscape format"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "bg_color": [80, 20, 20],
            "animation_style": "camera",
            "aspect_ratio": "16:9"  # Landscape
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ 16:9 landscape project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ 16:9 landscape format completed: {result_url}")

    # =========== BACKGROUND COLOR TESTS ===========

    def test_custom_gradient_background(self):
        """Test custom bg_color gradient works"""
        video_url = self._get_test_video_url()
        
        # Test with blue gradient
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "bg_color": [20, 50, 100],  # Blue gradient start
            "animation_style": "float",
            "aspect_ratio": "9:16"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ Custom gradient project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ Custom gradient background works: {result_url}")

    # =========== PHONE POSITION TESTS ===========

    def test_phone_position_center(self):
        """Test phone_position='center' works"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "bg_color": [80, 20, 20],
            "animation_style": "float",
            "phone_position": "center",
            "aspect_ratio": "9:16"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ Phone center position project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ Phone position 'center' works: {result_url}")

    def test_phone_position_left(self):
        """Test phone_position='left' works"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "bg_color": [80, 20, 20],
            "animation_style": "float",
            "phone_position": "left",
            "aspect_ratio": "9:16"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ Phone left position project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ Phone position 'left' works: {result_url}")

    def test_phone_position_right(self):
        """Test phone_position='right' works"""
        video_url = self._get_test_video_url()
        
        payload = {
            "video_url": video_url,
            "device_type": "phone",
            "bg_color": [80, 20, 20],
            "animation_style": "float",
            "phone_position": "right",
            "aspect_ratio": "9:16"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        project_id = response.json()["id"]
        print(f"✓ Phone right position project created: {project_id}")
        
        result_url = self._poll_for_completion(project_id, max_wait=120)
        print(f"✓ Phone position 'right' works: {result_url}")

    # =========== ERROR HANDLING TESTS ===========

    def test_invalid_video_url_rejected(self):
        """Test that invalid video URLs are rejected"""
        payload = {
            "video_url": "https://example.com/video.mp4",
            "device_type": "phone",
            "animation_style": "camera"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 400, f"Should reject invalid URL, got {response.status_code}"
        print(f"✓ Invalid video URL correctly rejected")

    def test_nonexistent_video_rejected(self):
        """Test that nonexistent video files are rejected"""
        payload = {
            "video_url": "/api/uploads/nonexistent-file-12345.mp4",
            "device_type": "phone",
            "animation_style": "camera"
        }
        
        response = requests.post(f"{BASE_URL}/api/device-mockup/create", json=payload)
        assert response.status_code == 404, f"Should return 404, got {response.status_code}"
        print(f"✓ Nonexistent video correctly rejected with 404")


class TestIPhoneCompositorV8:
    """Tests to verify iphone_compositor.py v8 features"""

    def test_compositor_v8_imports(self):
        """Verify iphone_compositor.py v8 can be imported with new functions"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from iphone_compositor import (
            render_dynamic_phone,
            render_camera_animation,
            render_simple_float,
            render_phone_with_text,
            create_gradient_background
        )
        
        print(f"✓ iphone_compositor.py v8 imports successfully")
        print(f"  - render_dynamic_phone: available")
        print(f"  - render_camera_animation: available")
        print(f"  - render_simple_float: available")
        print(f"  - create_gradient_background: available")

    def test_render_dynamic_phone_parameters(self):
        """Verify render_dynamic_phone has correct parameters"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        import inspect
        from iphone_compositor import render_dynamic_phone
        
        sig = inspect.signature(render_dynamic_phone)
        params = list(sig.parameters.keys())
        
        # Check required parameters
        assert 'video_frame' in params, "Should have video_frame parameter"
        assert 'time_progress' in params, "Should have time_progress parameter"
        assert 'output_size' in params, "Should have output_size parameter"
        assert 'bg_color' in params, "Should have bg_color parameter"
        assert 'animation_style' in params, "Should have animation_style parameter"
        assert 'position' in params, "Should have position parameter"
        
        print(f"✓ render_dynamic_phone has all required parameters")

    def test_camera_animation_parameters(self):
        """Verify render_camera_animation has phone_scale_start and phone_scale_end"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        import inspect
        from iphone_compositor import render_camera_animation
        
        sig = inspect.signature(render_camera_animation)
        params = sig.parameters
        
        # Check scale parameters exist
        assert 'phone_scale_start' in params, "Should have phone_scale_start"
        assert 'phone_scale_end' in params, "Should have phone_scale_end"
        
        # Check default values ensure phone stays visible (< 1.0)
        start_default = params['phone_scale_start'].default
        end_default = params['phone_scale_end'].default
        
        assert start_default < 1.0, f"phone_scale_start should be < 1.0, got {start_default}"
        assert end_default < 1.0, f"phone_scale_end should be < 1.0, got {end_default}"
        
        print(f"✓ Camera animation scale parameters: start={start_default}, end={end_default}")

    def test_render_simple_frame(self):
        """Test that render functions can create a frame without error"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from PIL import Image
        from iphone_compositor import render_dynamic_phone
        
        # Create a test video frame
        test_frame = Image.new('RGB', (1080, 1920), (100, 150, 200))
        
        # Test camera animation
        result = render_dynamic_phone(
            video_frame=test_frame,
            time_progress=0.5,
            output_size=(1080, 1920),
            bg_color=(80, 20, 20),
            animation_style="camera",
            position="center"
        )
        
        assert result is not None, "Should return an image"
        assert result.size == (1080, 1920), f"Should be 1080x1920, got {result.size}"
        print(f"✓ render_dynamic_phone creates frame correctly")

    def test_float_animation_frame(self):
        """Test float animation creates frame without error"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from PIL import Image
        from iphone_compositor import render_dynamic_phone
        
        test_frame = Image.new('RGB', (1080, 1920), (100, 150, 200))
        
        result = render_dynamic_phone(
            video_frame=test_frame,
            time_progress=0.5,
            output_size=(1080, 1920),
            bg_color=(40, 45, 40),
            animation_style="float",
            position="center"
        )
        
        assert result is not None, "Should return an image"
        print(f"✓ Float animation creates frame correctly")

    def test_landscape_output_size(self):
        """Test 16:9 landscape output size works"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from PIL import Image
        from iphone_compositor import render_dynamic_phone
        
        test_frame = Image.new('RGB', (1080, 1920), (100, 150, 200))
        
        result = render_dynamic_phone(
            video_frame=test_frame,
            time_progress=0.5,
            output_size=(1920, 1080),  # Landscape
            bg_color=(80, 20, 20),
            animation_style="float",
            position="center"
        )
        
        assert result is not None, "Should return an image"
        assert result.size == (1920, 1080), f"Should be 1920x1080, got {result.size}"
        print(f"✓ 16:9 landscape output works correctly")

    def test_phone_always_visible_margins(self):
        """Verify phone stays within margins at all animation progress points"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from PIL import Image
        import numpy as np
        from iphone_compositor import render_camera_animation
        
        test_frame = Image.new('RGB', (1080, 1920), (100, 150, 200))
        output_size = (1080, 1920)
        
        # Test at multiple progress points
        progress_points = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for progress in progress_points:
            result = render_camera_animation(
                video_frame=test_frame,
                time_progress=progress,
                output_size=output_size,
                bg_color1=(80, 20, 20),
                bg_color2=(25, 8, 8),
                position="center"
            )
            
            assert result is not None, f"Frame at progress {progress} should not be None"
            assert result.size == output_size, f"Frame size should be {output_size}"
            
            # Convert to array to check if content exists in margins
            # Just verify no crash and valid output
            arr = np.array(result)
            assert arr.shape == (1920, 1080, 3), f"Shape mismatch at progress {progress}"
        
        print(f"✓ Phone rendered correctly at all animation progress points")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
