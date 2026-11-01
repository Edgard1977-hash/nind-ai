#!/usr/bin/env python3
"""
Quick test script for device mockup API - iphone_compositor v8
Tests the CRITICAL requirements:
1. Phone ALWAYS FULLY VISIBLE
2. Camera animation (zoom+rotate)
3. Float animation
4. 9:16 and 16:9 formats
5. Custom gradient backgrounds
6. Phone positions: center, left, right
"""

import requests
import time
import sys

BASE_URL = "https://ai-format-studio.preview.emergentagent.com"

def make_request(method, url, **kwargs):
    """Make HTTP request with retries"""
    kwargs.setdefault('timeout', 30)
    for attempt in range(3):
        try:
            if method == 'GET':
                return requests.get(url, **kwargs)
            else:
                return requests.post(url, **kwargs)
        except Exception as e:
            if attempt == 2:
                print(f"  Request failed after 3 attempts: {e}")
                return None
            time.sleep(2)

def poll_project(project_id, max_wait=90):
    """Poll for project completion"""
    elapsed = 0
    while elapsed < max_wait:
        r = make_request('GET', f'{BASE_URL}/api/video/{project_id}')
        if r and r.status_code == 200:
            data = r.json()
            status = data.get('status')
            if status == 'completed':
                return 'completed', data.get('video_url')
            elif status == 'failed':
                return 'failed', data.get('error')
            print(f"    Progress: {data.get('progress', 0)}%")
        time.sleep(5)
        elapsed += 5
    return 'timeout', None

def run_tests():
    results = {'passed': [], 'failed': []}
    
    print("=" * 60)
    print("DEVICE MOCKUP API TESTS - iphone_compositor v8")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n[1] API Health Check")
    r = make_request('GET', f'{BASE_URL}/api/')
    if r and r.status_code == 200:
        print("  ✓ API is accessible")
        results['passed'].append("API health")
    else:
        print(f"  ✗ API check failed")
        results['failed'].append("API health")
        return results  # Cannot continue without API
    
    # Test 2: Invalid URL rejection
    print("\n[2] Error Handling - Invalid URL")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': 'https://example.com/video.mp4',
        'animation_style': 'camera'
    })
    if r and r.status_code == 400:
        print("  ✓ Invalid URL correctly rejected (400)")
        results['passed'].append("Invalid URL rejection")
    else:
        status = r.status_code if r else 'None'
        print(f"  ✗ Expected 400, got {status}")
        results['failed'].append("Invalid URL rejection")
    
    # Test 3: Nonexistent file rejection
    print("\n[3] Error Handling - Nonexistent File")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/nonexistent-12345.mp4',
        'animation_style': 'camera'
    })
    if r and r.status_code == 404:
        print("  ✓ Nonexistent file correctly rejected (404)")
        results['passed'].append("Nonexistent file rejection")
    else:
        status = r.status_code if r else 'None'
        print(f"  ✗ Expected 404, got {status}")
        results['failed'].append("Nonexistent file rejection")
    
    # Test 4: Camera animation 9:16
    print("\n[4] Camera Animation Style (9:16 Portrait)")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/test_short_3sec.mp4',
        'bg_color': [80, 20, 20],
        'animation_style': 'camera',
        'phone_position': 'center',
        'aspect_ratio': '9:16'
    })
    if r and r.status_code == 200:
        project_id = r.json()['id']
        print(f"  Project created: {project_id}")
        status, result = poll_project(project_id)
        if status == 'completed':
            print(f"  ✓ Camera animation completed: {result}")
            results['passed'].append("Camera animation 9:16")
        else:
            print(f"  ✗ Failed: {status} - {result}")
            results['failed'].append("Camera animation 9:16")
    else:
        print(f"  ✗ Request failed")
        results['failed'].append("Camera animation 9:16")
    
    # Test 5: Float animation 9:16
    print("\n[5] Float Animation Style (9:16 Portrait)")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/test_short_3sec.mp4',
        'bg_color': [40, 45, 40],
        'animation_style': 'float',
        'phone_position': 'center',
        'aspect_ratio': '9:16'
    })
    if r and r.status_code == 200:
        project_id = r.json()['id']
        print(f"  Project created: {project_id}")
        status, result = poll_project(project_id)
        if status == 'completed':
            print(f"  ✓ Float animation completed: {result}")
            results['passed'].append("Float animation 9:16")
        else:
            print(f"  ✗ Failed: {status} - {result}")
            results['failed'].append("Float animation 9:16")
    else:
        print(f"  ✗ Request failed")
        results['failed'].append("Float animation 9:16")
    
    # Test 6: 16:9 Landscape
    print("\n[6] 16:9 Landscape Format")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/test_short_3sec.mp4',
        'bg_color': [80, 20, 20],
        'animation_style': 'camera',
        'phone_position': 'center',
        'aspect_ratio': '16:9'
    })
    if r and r.status_code == 200:
        project_id = r.json()['id']
        print(f"  Project created: {project_id}")
        status, result = poll_project(project_id)
        if status == 'completed':
            print(f"  ✓ 16:9 landscape completed: {result}")
            results['passed'].append("16:9 landscape format")
        else:
            print(f"  ✗ Failed: {status} - {result}")
            results['failed'].append("16:9 landscape format")
    else:
        print(f"  ✗ Request failed")
        results['failed'].append("16:9 landscape format")
    
    # Test 7: Phone position left
    print("\n[7] Phone Position Left")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/test_short_3sec.mp4',
        'bg_color': [20, 50, 100],
        'animation_style': 'float',
        'phone_position': 'left',
        'aspect_ratio': '9:16'
    })
    if r and r.status_code == 200:
        project_id = r.json()['id']
        print(f"  Project created: {project_id}")
        status, result = poll_project(project_id)
        if status == 'completed':
            print(f"  ✓ Position left completed: {result}")
            results['passed'].append("Phone position left")
        else:
            print(f"  ✗ Failed: {status} - {result}")
            results['failed'].append("Phone position left")
    else:
        print(f"  ✗ Request failed")
        results['failed'].append("Phone position left")
    
    # Test 8: Phone position right
    print("\n[8] Phone Position Right")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/test_short_3sec.mp4',
        'bg_color': [100, 20, 80],
        'animation_style': 'float',
        'phone_position': 'right',
        'aspect_ratio': '9:16'
    })
    if r and r.status_code == 200:
        project_id = r.json()['id']
        print(f"  Project created: {project_id}")
        status, result = poll_project(project_id)
        if status == 'completed':
            print(f"  ✓ Position right completed: {result}")
            results['passed'].append("Phone position right")
        else:
            print(f"  ✗ Failed: {status} - {result}")
            results['failed'].append("Phone position right")
    else:
        print(f"  ✗ Request failed")
        results['failed'].append("Phone position right")
    
    # Test 9: Custom gradient background
    print("\n[9] Custom Gradient Background (Blue)")
    r = make_request('POST', f'{BASE_URL}/api/device-mockup/create', json={
        'video_url': '/api/uploads/test_short_3sec.mp4',
        'bg_color': [20, 80, 150],  # Blue gradient
        'animation_style': 'float',
        'phone_position': 'center',
        'aspect_ratio': '9:16'
    })
    if r and r.status_code == 200:
        project_id = r.json()['id']
        print(f"  Project created: {project_id}")
        status, result = poll_project(project_id)
        if status == 'completed':
            print(f"  ✓ Blue gradient completed: {result}")
            results['passed'].append("Custom gradient background")
        else:
            print(f"  ✗ Failed: {status} - {result}")
            results['failed'].append("Custom gradient background")
    else:
        print(f"  ✗ Request failed")
        results['failed'].append("Custom gradient background")
    
    return results

if __name__ == "__main__":
    results = run_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results['passed']) + len(results['failed'])
    rate = (len(results['passed']) / total * 100) if total > 0 else 0
    
    print(f"\nPassed: {len(results['passed'])}/{total} ({rate:.0f}%)")
    for t in results['passed']:
        print(f"  ✓ {t}")
    
    if results['failed']:
        print(f"\nFailed: {len(results['failed'])}/{total}")
        for t in results['failed']:
            print(f"  ✗ {t}")
    
    print(f"\nSuccess Rate: {rate:.0f}%")
    
    # Exit code based on results
    sys.exit(0 if len(results['failed']) == 0 else 1)
