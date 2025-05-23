"""
Test email functionality directly.
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .email import PasswordResetEmail
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

@csrf_exempt
def test_password_reset_email(request):
    """
    Test view to directly send a password reset email.
    This bypasses Djoser and sends the email directly.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        # Get email from request
        import json
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Log the test request
        logger.critical(f"Test password reset email requested for: {email}")
        
        # Find the user
        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Create context
        context = {
            'user': user,
            'domain': settings.SITE_URL.replace('http://', '').replace('https://', '').split(',')[0].strip(),
            'protocol': 'http' if 'localhost' in settings.SITE_URL or '127.0.0.1' in settings.SITE_URL else 'https',
            'site_name': settings.DJOSER.get('SITE_NAME', 'Project Management'),
        }
        
        # Create and send the email
        email_instance = PasswordResetEmail(request=request, context=context)
        result = email_instance.send([email])
        
        # Log the result
        logger.critical(f"Test email send result: {result}")
        
        return JsonResponse({'success': True, 'message': 'Password reset email sent successfully'})
    
    except Exception as e:
        logger.critical(f"Error in test_password_reset_email: {str(e)}")
        logger.exception("Exception details:")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def test_direct_email(request):
    """
    Test view to send a direct email using Django's send_mail function.
    This bypasses all custom email classes and sends a simple email directly.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        # Get email from request
        import json
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Log the test request
        logger.critical(f"Test direct email requested for: {email}")
        
        # Log email settings
        logger.critical(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        logger.critical(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        logger.critical(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        logger.critical(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        logger.critical(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        logger.critical(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Send a simple email
        result = send_mail(
            subject="Test Email from Project Management",
            message="This is a test email sent directly from Django's send_mail function.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        # Log the result
        logger.critical(f"Direct email send result: {result}")
        
        return JsonResponse({'success': True, 'message': 'Direct test email sent successfully'})
    
    except Exception as e:
        logger.critical(f"Error in test_direct_email: {str(e)}")
        logger.exception("Exception details:")
        return JsonResponse({'error': str(e)}, status=500)
