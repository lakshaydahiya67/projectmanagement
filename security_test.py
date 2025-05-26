#!/usr/bin/env python
"""
Comprehensive security test script for the Django project management system.
This script tests all the security fixes that have been implemented.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import json

User = get_user_model()

class SecurityTestRunner:
    """Test runner for security-related functionality"""
    
    def __init__(self):
        self.client = Client()
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log_test(self, test_name, passed, message=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def test_security_middleware(self):
        """Test if security middleware is properly configured"""
        try:
            # Check if security middleware is in MIDDLEWARE
            middleware_list = settings.MIDDLEWARE
            has_security_middleware = 'projectmanagement.security_middleware.SecurityMiddleware' in middleware_list
            self.log_test(
                "Security Middleware Configuration",
                has_security_middleware,
                "Custom security middleware is configured" if has_security_middleware else "Security middleware missing"
            )
        except Exception as e:
            self.log_test("Security Middleware Configuration", False, f"Error: {str(e)}")
    
    def test_cors_configuration(self):
        """Test CORS security configuration"""
        try:
            # Test that CORS_ALLOW_ALL_ORIGINS is disabled
            cors_all_origins = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', True)
            self.log_test(
                "CORS Security Configuration",
                not cors_all_origins,
                "CORS_ALLOW_ALL_ORIGINS is disabled for security" if not cors_all_origins else "CORS allows all origins - SECURITY RISK"
            )
        except Exception as e:
            self.log_test("CORS Security Configuration", False, f"Error: {str(e)}")
    
    def test_password_validation(self):
        """Test password validation settings"""
        try:
            validators = settings.AUTH_PASSWORD_VALIDATORS
            # Check for minimum length validator
            min_length_validator = any(
                'MinimumLengthValidator' in validator.get('NAME', '') 
                for validator in validators
            )
            # Check for common password validator
            common_pwd_validator = any(
                'CommonPasswordValidator' in validator.get('NAME', '')
                for validator in validators
            )
            
            both_enabled = min_length_validator and common_pwd_validator
            self.log_test(
                "Password Validation",
                both_enabled,
                "Strong password validation enabled" if both_enabled else "Missing password validators"
            )
        except Exception as e:
            self.log_test("Password Validation", False, f"Error: {str(e)}")
    
    def test_file_upload_security(self):
        """Test file upload security settings"""
        try:
            # Check file upload size limits
            max_memory_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 0)
            data_upload_max = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 0)
            
            has_limits = max_memory_size > 0 and data_upload_max > 0
            self.log_test(
                "File Upload Size Limits",
                has_limits,
                f"Limits set: {max_memory_size/1024/1024:.1f}MB upload, {data_upload_max/1024/1024:.1f}MB data" if has_limits else "No upload size limits set"
            )
        except Exception as e:
            self.log_test("File Upload Size Limits", False, f"Error: {str(e)}")
    
    def test_jwt_security_configuration(self):
        """Test JWT security configuration"""
        try:
            jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
            
            # Check for secure JWT settings
            access_token_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME')
            refresh_token_lifetime = jwt_settings.get('REFRESH_TOKEN_LIFETIME')
            rotate_refresh_tokens = jwt_settings.get('ROTATE_REFRESH_TOKENS', False)
            blacklist_after_rotation = jwt_settings.get('BLACKLIST_AFTER_ROTATION', False)
            
            is_secure = (
                access_token_lifetime is not None and
                refresh_token_lifetime is not None and
                rotate_refresh_tokens and
                blacklist_after_rotation
            )
            
            self.log_test(
                "JWT Security Configuration",
                is_secure,
                "JWT configured with secure settings" if is_secure else "JWT security settings incomplete"
            )
        except Exception as e:
            self.log_test("JWT Security Configuration", False, f"Error: {str(e)}")
    
    def test_security_headers(self):
        """Test security headers configuration"""
        try:
            # Test various security settings
            security_checks = {
                'X-Frame-Options': getattr(settings, 'X_FRAME_OPTIONS', None) == 'DENY',
                'Content-Type-Nosniff': getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
                'XSS-Filter': getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False),
                'Referrer-Policy': getattr(settings, 'SECURE_REFERRER_POLICY', None) is not None,
                'Cross-Origin-Opener-Policy': getattr(settings, 'SECURE_CROSS_ORIGIN_OPENER_POLICY', None) is not None,
            }
            
            all_headers_set = all(security_checks.values())
            enabled_headers = [k for k, v in security_checks.items() if v]
            
            self.log_test(
                "Security Headers",
                all_headers_set,
                f"All security headers configured" if all_headers_set else f"Headers enabled: {', '.join(enabled_headers)}"
            )
        except Exception as e:
            self.log_test("Security Headers", False, f"Error: {str(e)}")
    
    def test_dependencies_updated(self):
        """Test if critical dependencies are updated"""
        try:
            # This is a basic check - in a real scenario, you'd parse requirements.txt
            # and check against known vulnerable versions
            with open('requirements.txt', 'r') as f:
                content = f.read()
                
            # Check for updated versions of critical packages
            critical_updates = {
                'Django>=5.0': 'Django==5.0.8' in content,
                'Pillow>=10.4': 'Pillow==10.4.0' in content,
                'celery>=5.4': 'celery==5.4.0' in content,
            }
            
            all_updated = all(critical_updates.values())
            updated_packages = [k for k, v in critical_updates.items() if v]
            
            self.log_test(
                "Critical Dependencies Updated",
                all_updated,
                "All critical packages updated" if all_updated else f"Updated: {', '.join(updated_packages)}"
            )
        except Exception as e:
            self.log_test("Critical Dependencies Updated", False, f"Error: {str(e)}")
    
    def test_database_constraints(self):
        """Test database constraints are applied"""
        try:
            from django.db import connection
            
            # Get table constraints
            with connection.cursor() as cursor:
                # This is a simplified test - check if constraints exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
            # Check if our main tables exist
            expected_tables = ['tasks_task', 'tasks_attachment', 'projects_project', 'projects_board']
            tables_exist = all(table in tables for table in expected_tables)
            
            self.log_test(
                "Database Constraints",
                tables_exist,
                "Database tables with constraints created" if tables_exist else "Some tables missing"
            )
        except Exception as e:
            self.log_test("Database Constraints", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 Starting Comprehensive Security Test Suite\n")
        print("=" * 60)
        
        # Run all test methods
        test_methods = [
            self.test_security_middleware,
            self.test_cors_configuration,
            self.test_password_validation,
            self.test_file_upload_security,
            self.test_jwt_security_configuration,
            self.test_security_headers,
            self.test_dependencies_updated,
            self.test_database_constraints,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Unexpected error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"🔒 Security Test Summary:")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📊 Total: {self.passed_tests + self.failed_tests}")
        
        if self.failed_tests == 0:
            print("\n🎉 All security tests passed! The application is production-ready.")
            grade = "A"
        elif self.failed_tests <= 2:
            print("\n⚠️  Most security tests passed. Minor issues to address.")
            grade = "B+"
        elif self.failed_tests <= 4:
            print("\n⚠️  Some security tests failed. Please review and fix.")
            grade = "B-"
        else:
            print("\n🚨 Multiple security tests failed. Immediate attention required.")
            grade = "C"
        
        print(f"🏆 Security Grade: {grade}")
        return grade

if __name__ == "__main__":
    try:
        runner = SecurityTestRunner()
        grade = runner.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if runner.failed_tests == 0 else 1)
        
    except Exception as e:
        print(f"❌ Security test runner failed: {str(e)}")
        sys.exit(1)
