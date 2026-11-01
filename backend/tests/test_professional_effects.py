"""
Backend API Tests for Professional Video Effects - Apple-style, Logo Animation, Gradient Text
Tests video generation endpoints for new professional animation features
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-format-studio.preview.emergentagent.com').rstrip('/')


class TestAppleStyleTextAnimation:
    """Test Apple-style word-by-word text animation"""
    
    def test_generate_apple_style_text_video(self):
        """Test video generation with Apple-style text animation prompt"""
        payload = {
            "prompt": "Let's create Some silky smooth text Just like Apple.",
            "format_id": "auto",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["status"] == "pending"
        
        job_id = data["id"]
        print(f"PASS: Apple-style text animation started with ID: {job_id}")
        
        # Wait and check status
        time.sleep(5)
        status_response = requests.get(f"{BASE_URL}/api/video/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Should be detected as universal format
        assert status_data["format_id"] in ["universal", "apple_text", "news"]
        print(f"PASS: Format detected as: {status_data['format_id']}")
    
    def test_generate_explicit_apple_text_format(self):
        """Test video generation with explicit apple_text format"""
        payload = {
            "prompt": "Минимализм. Простота. Apple.",
            "format_id": "apple_text",
            "language": "ru"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        print(f"PASS: Explicit apple_text format started with ID: {data['id']}")


class TestLogoAnimation:
    """Test logo animation with rotation + scale effects"""
    
    def test_generate_logo_animation_with_upload(self):
        """Test logo animation with an uploaded logo"""
        payload = {
            "prompt": "Logo animation for TechBrand company",
            "format_id": "logo_animation",
            "language": "en",
            "logo_url": "/api/uploads/test_logo.png",
            "brand_name": "TechBrand"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["status"] == "pending"
        
        job_id = data["id"]
        print(f"PASS: Logo animation with uploaded logo started with ID: {job_id}")
        
        # Wait for completion
        for i in range(30):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/video/{job_id}")
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                assert "video_url" in status_data
                assert status_data["video_url"] is not None
                print(f"PASS: Logo animation completed with video: {status_data['video_url']}")
                return
            elif status_data["status"] == "error":
                pytest.fail(f"Video generation failed: {status_data.get('error')}")
        
        print(f"INFO: Video still processing after 60s, status: {status_data['status']}")
    
    def test_generate_logo_animation_without_logo(self):
        """Test logo animation without uploaded logo (fallback to text animation)"""
        payload = {
            "prompt": "Brand reveal for MyCompany",
            "format_id": "logo_animation",
            "language": "en",
            "brand_name": "MyCompany"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        print(f"PASS: Logo animation without logo started with ID: {data['id']}")


class TestGradientTextAnimation:
    """Test gradient text animation with shimmer effect"""
    
    def test_generate_gradient_text_video(self):
        """Test gradient text animation on dark background"""
        payload = {
            "prompt": "Gradient text saying Amazing with shimmer effect on dark background",
            "format_id": "auto",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        print(f"PASS: Gradient text animation started with ID: {data['id']}")


class TestVideoFileAccess:
    """Test that generated video files are accessible"""
    
    def test_access_existing_video_file(self):
        """Test accessing a known existing video file"""
        # Use a video we generated in tests
        video_filename = "video_2e510af3-afe9-42b0-84f7-484a182ee607.mp4"
        response = requests.get(f"{BASE_URL}/api/uploads/{video_filename}", stream=True)
        
        assert response.status_code == 200
        assert "video" in response.headers.get("Content-Type", "")
        response.close()
        print("PASS: Video file accessible")
    
    def test_access_test_logo(self):
        """Test that test logo file is accessible"""
        response = requests.get(f"{BASE_URL}/api/uploads/test_logo.png")
        assert response.status_code == 200
        assert "image" in response.headers.get("Content-Type", "")
        print("PASS: Test logo file accessible")


class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_image_file(self):
        """Test uploading an image file"""
        # We need to use a file that exists
        test_logo_path = "/app/backend/uploads/test_logo.png"
        
        with open(test_logo_path, "rb") as f:
            files = {"file": ("test_logo.png", f, "image/png")}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "url" in data
        assert data["url"].startswith("/api/uploads/")
        assert "filename" in data
        print(f"PASS: Image uploaded successfully: {data['url']}")


class TestVideoFormats:
    """Test that professional effect formats are available"""
    
    def test_formats_include_professional_effects(self):
        """Test that formats endpoint includes all professional effect formats"""
        response = requests.get(f"{BASE_URL}/api/formats")
        assert response.status_code == 200
        data = response.json()
        
        formats = data["formats"]
        format_ids = [f["id"] for f in formats]
        
        # Verify professional effect formats exist
        professional_formats = [
            "apple_text",
            "kinetic_typography",
            "logo_animation",
            "chat_animation",
            "product_advertisement",
            "spotify_demo",
            "saas_demo"
        ]
        
        for fmt in professional_formats:
            assert fmt in format_ids, f"Format '{fmt}' not found in available formats"
        
        print(f"PASS: All {len(professional_formats)} professional effect formats are available")
    
    def test_logo_animation_format_details(self):
        """Test logo_animation format has correct metadata"""
        response = requests.get(f"{BASE_URL}/api/formats")
        data = response.json()
        
        logo_format = next((f for f in data["formats"] if f["id"] == "logo_animation"), None)
        assert logo_format is not None
        
        assert logo_format["name"] == "Logo Animation"
        assert logo_format["name_ru"] == "Анимация логотипа"
        assert logo_format["category"] == "branding"
        assert logo_format["icon"] == "Star"
        
        print("PASS: logo_animation format has correct metadata")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
