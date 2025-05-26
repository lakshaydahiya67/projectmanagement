#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.urls import get_resolver

def show_urls(urllist, depth=0):
    for entry in urllist:
        print("  " * depth, entry.pattern, entry.name if hasattr(entry, 'name') else '')
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

# Check API v1 URLs
from django.conf.urls import include
from projectmanagement.urls import api_patterns

print("=== API v1 URL Patterns ===")
resolver = get_resolver()
print("ROOT PATTERNS:")
for pattern in resolver.url_patterns:
    if 'api/v1/' in str(pattern.pattern):
        print("Found API v1 pattern:", pattern.pattern)
        if hasattr(pattern, 'url_patterns'):
            show_urls(pattern.url_patterns, 1)

print("\n=== Checking specific endpoints ===")

# Test URLs we expect
test_urls = [
    '/api/v1/tasks/',
    '/api/v1/projects/',
    '/api/v1/projects/12345/boards/',
    '/api/v1/projects/12345/boards/67890/columns/',
    '/api/v1/projects/12345/boards/67890/columns/abcdef/tasks/',
]

from django.urls import reverse, resolve, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured

for url in test_urls:
    try:
        resolved = resolve(url)
        print(f"✓ {url} -> {resolved.view_name} ({resolved.func})")
    except Exception as e:
        print(f"✗ {url} -> {type(e).__name__}: {e}")
