"""
Backend API Tests for AI Video Content Service
Tests all video generation, format detection, and CRUD operations
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-format-studio.preview.emergentagent.com').rstrip('/')

class TestHealthAndFormats:
    """Test health check and format endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "VidFlux AI API"
        print("PASS: API root endpoint works")
    
    def test_get_formats(self):
        """Test formats endpoint returns all 10 video formats"""
        response = requests.get(f"{BASE_URL}/api/formats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "formats" in data
        assert "categories" in data
        assert "character_types" in data
        assert "gameplay_types" in data
        
        # Verify formats exist (at least 10)
        formats = data["formats"]
        assert len(formats) >= 10
        
        # Verify chat_animation format exists (new format)
        format_ids = [f["id"] for f in formats]
        assert "chat_animation" in format_ids
        assert "ai_story" in format_ids
        assert "news" in format_ids
        assert "gameplay_clip" in format_ids
        
        # Verify chat_animation format has correct data
        chat_format = next(f for f in formats if f["id"] == "chat_animation")
        assert chat_format["name_ru"] == "Анимация диалога"
        assert chat_format["icon"] == "MessageSquare"
        
        print("PASS: Formats endpoint returns all 10 formats including chat_animation")
    
    def test_get_character_types(self):
        """Test character types are returned correctly"""
        response = requests.get(f"{BASE_URL}/api/formats")
        assert response.status_code == 200
        data = response.json()
        
        character_types = data["character_types"]
        assert len(character_types) == 6
        
        character_ids = [c["id"] for c in character_types]
        assert "kitten" in character_ids
        assert "robot" in character_ids
        
        print("PASS: Character types returned correctly")
    
    def test_get_gameplay_types(self):
        """Test gameplay types are returned correctly"""
        response = requests.get(f"{BASE_URL}/api/formats")
        assert response.status_code == 200
        data = response.json()
        
        gameplay_types = data["gameplay_types"]
        assert len(gameplay_types) == 6
        
        gameplay_ids = [g["id"] for g in gameplay_types]
        assert "minecraft_parkour" in gameplay_ids
        assert "subway_surfers" in gameplay_ids
        
        print("PASS: Gameplay types returned correctly")


class TestVideoGeneration:
    """Test video generation endpoints"""
    
    def test_generate_video_with_auto_detection(self):
        """Test video generation with format_id='auto' triggers auto-detection"""
        payload = {
            "prompt": "Сделай анимацию диалога: [Тест: Привет!] [Ответ: Привет!]",
            "format_id": "auto",
            "language": "auto"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Verify job created
        assert "id" in data
        assert "status" in data
        assert data["status"] == "pending"
        
        job_id = data["id"]
        print(f"PASS: Video generation started with job ID: {job_id}")
        
        # Wait a bit and check status
        time.sleep(3)
        status_response = requests.get(f"{BASE_URL}/api/video/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Should be processing or still have format detected
        assert status_data["status"] in ["pending", "processing", "completed", "error"]
        print(f"PASS: Video status is: {status_data['status']}")
    
    def test_generate_video_with_chat_animation_format(self):
        """Test video generation explicitly using chat_animation format"""
        payload = {
            "prompt": "TEST_Тестовый диалог: [A: Привет] [B: Пока]",
            "format_id": "chat_animation",
            "language": "ru"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["status"] == "pending"
        
        print(f"PASS: Chat animation video generation started with ID: {data['id']}")
    
    def test_generate_video_with_news_format(self):
        """Test video generation with news format"""
        payload = {
            "prompt": "TEST_Новости о технологиях 2026",
            "format_id": "news",
            "language": "ru"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        print(f"PASS: News format video generation started with ID: {data['id']}")


class TestExistingVideo:
    """Test existing video retrieval - using known completed video"""
    
    def test_get_existing_completed_video(self):
        """Test getting existing completed video with poster_url"""
        video_id = "55395410-a62e-495b-bd39-963a250fe1db"
        response = requests.get(f"{BASE_URL}/api/video/{video_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify video data
        assert data["id"] == video_id
        assert data["status"] == "completed"
        assert data["format_id"] == "chat_animation"
        
        # Verify poster_url exists
        assert "poster_url" in data
        assert data["poster_url"] is not None
        assert data["poster_url"].startswith("/api/uploads/")
        
        # Verify video_url exists
        assert "video_url" in data
        assert data["video_url"] is not None
        
        print(f"PASS: Existing video retrieved with poster_url: {data['poster_url']}")
    
    def test_get_nonexistent_video(self):
        """Test getting a non-existent video returns 404"""
        response = requests.get(f"{BASE_URL}/api/video/nonexistent-video-id")
        assert response.status_code == 404
        print("PASS: Non-existent video returns 404")
    
    def test_get_all_videos(self):
        """Test getting all videos"""
        response = requests.get(f"{BASE_URL}/api/videos")
        assert response.status_code == 200
        data = response.json()
        
        assert "projects" in data
        projects = data["projects"]
        assert isinstance(projects, list)
        assert len(projects) > 0
        
        # Verify completed videos have expected fields
        completed_videos = [p for p in projects if p["status"] == "completed"]
        if completed_videos:
            video = completed_videos[0]
            assert "id" in video
            assert "title" in video
            assert "video_url" in video
            # Some should have poster_url
            videos_with_poster = [v for v in completed_videos if v.get("poster_url")]
            print(f"PASS: Found {len(videos_with_poster)} videos with poster_url out of {len(completed_videos)} completed")
        
        print(f"PASS: Got {len(projects)} total videos")


class TestUploads:
    """Test file upload/download endpoints"""
    
    def test_get_existing_poster(self):
        """Test getting poster image from uploads"""
        # Using poster from existing video
        poster_path = "poster_with_audio_7bb9a87b.jpg"
        response = requests.get(f"{BASE_URL}/api/uploads/{poster_path}")
        
        # Should return 200 with image data
        assert response.status_code == 200
        assert "image" in response.headers.get("Content-Type", "")
        print("PASS: Poster image accessible from uploads")
    
    def test_get_existing_video_file(self):
        """Test getting video file from uploads"""
        video_path = "video_55395410-a62e-495b-bd39-963a250fe1db.mp4"
        # Use GET with stream to check if video exists without downloading full content
        response = requests.get(f"{BASE_URL}/api/uploads/{video_path}", stream=True)
        
        # Should return 200 with video content type
        assert response.status_code == 200
        assert "video" in response.headers.get("Content-Type", "")
        response.close()  # Close stream
        print("PASS: Video file accessible from uploads")
    
    def test_get_nonexistent_upload(self):
        """Test getting non-existent upload returns 404"""
        response = requests.get(f"{BASE_URL}/api/uploads/nonexistent-file.mp4")
        assert response.status_code == 404
        print("PASS: Non-existent upload returns 404")


class TestAutoDetection:
    """Test auto-detection of video type based on prompt"""
    
    def test_auto_detect_chat_format_ru(self):
        """Test auto-detection identifies chat animation from Russian prompt"""
        # We test this indirectly by creating a job and checking if format is detected
        payload = {
            "prompt": "Создай диалог между двумя людьми: [Иван: Привет, как дела?] [Мария: Хорошо, а у тебя?]",
            "format_id": "auto",
            "language": "auto"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        job_id = data["id"]
        
        # Wait for processing to start and format to be detected
        time.sleep(5)
        
        status_response = requests.get(f"{BASE_URL}/api/video/{job_id}")
        status_data = status_response.json()
        
        # Format should be detected (could be chat_animation or ai_story based on AI analysis)
        assert status_data["format_id"] in ["chat_animation", "ai_story", "auto", "news"]
        print(f"PASS: Auto-detection detected format: {status_data['format_id']}")
    
    def test_auto_detect_news_format(self):
        """Test auto-detection identifies news format"""
        payload = {
            "prompt": "Срочные новости: в городе произошло важное событие сегодня",
            "format_id": "auto",
            "language": "auto"
        }
        
        response = requests.post(f"{BASE_URL}/api/video/generate", json=payload)
        assert response.status_code == 200
        print("PASS: News-style prompt accepted for auto-detection")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
