# Troubleshooting Guide

This guide provides solutions for common issues encountered when working with the Project Management application.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Development Environment Issues](#development-environment-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Docker Issues](#docker-issues)
- [WebSocket Issues](#websocket-issues)
- [Authentication Issues](#authentication-issues)
- [Database Issues](#database-issues)
- [Email Issues](#email-issues)
- [Performance Issues](#performance-issues)

## Installation Issues

### Package Installation Fails

**Problem**: `pip install -r requirements.txt` fails with dependency errors.

**Solution**:
1. Ensure you're using Python 3.8+ 
2. Try updating pip: `pip install --upgrade pip`
3. Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3-dev libpq-dev
   
   # macOS
   brew install python3
   ```
4. Try installing packages one by one to identify the problematic package

### Virtual Environment Issues

**Problem**: Cannot activate virtual environment or `venv` command not found.

**Solution**:
1. Ensure you have the venv module: `python -m venv --help`
2. If not available, install it:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-venv
   ```
3. Create a new virtual environment: `python -m venv venv`
4. Activate it:
   ```bash
   # Linux/macOS
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

## Development Environment Issues

### Redis Not Running

**Problem**: Django server fails with Redis connection errors.

**Solution**:
1. Check if Redis is running: `redis-cli ping`
2. If not running, start Redis:
   ```bash
   # Linux/macOS
   redis-server
   
   # Windows
   # Start Redis service or use WSL
   ```
3. If Redis isn't installed:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

### Port Already In Use

**Problem**: Django server or npm start fails with "port already in use" error.

**Solution**:
1. Find the process using the port:
   ```bash
   # Linux/macOS
   sudo lsof -i:8000  # For Django port
   sudo lsof -i:3000  # For React port
   
   # Windows
   netstat -ano | findstr :8000
   ```
2. Kill the process:
   ```bash
   # Linux/macOS
   kill -9 <PID>
   
   # Windows
   taskkill /F /PID <PID>
   ```
3. Start server with a different port:
   ```bash
   # Django
   python manage.py runserver 8001
   
   # React
   PORT=3001 npm start
   ```

## Backend Issues

### Migrations Failed

**Problem**: Django migrations fail with errors.

**Solution**:
1. Check for conflicting migrations:
   ```bash
   python manage.py showmigrations
   ```
2. If there are conflicts, try:
   ```bash
   python manage.py migrate --fake app_name zero
   python manage.py migrate app_name
   ```
3. For more complex issues, consider:
   - Deleting the database and recreating it
   - Using `--fake-initial` flag

### 500 Server Errors

**Problem**: API endpoints return 500 errors.

**Solution**:
1. Check the Django logs in the console or in `debug.log`
2. Enable DEBUG mode in settings if it's not already enabled
3. Look for traceback information
4. Common causes:
   - Database integrity errors
   - Missing environment variables
   - Mismatched Django and REST framework versions

### Permission Denied Errors

**Problem**: API endpoints return 403 Forbidden errors.

**Solution**:
1. Check if you're authenticated (login required)
2. Verify you have the correct permissions for the resource
3. Look at the permission classes in the view
4. Check organization membership if resource is organization-scoped

## Frontend Issues

### NPM Install Errors

**Problem**: `npm install` fails with dependency errors.

**Solution**:
1. Delete `node_modules` folder and `package-lock.json`
2. Clear npm cache: `npm cache clean --force`
3. Try again: `npm install`
4. If specific packages fail, try installing them individually
5. Update npm: `npm install -g npm`

### Blank Page in Browser

**Problem**: Frontend loads a blank page with no errors in the UI.

**Solution**:
1. Check browser console for JavaScript errors
2. Verify API connections (might be CORS issues)
3. Clear browser cache and reload
4. Check if the React app is rendering correctly:
   ```jsx
   // Add this to App.js temporarily
   console.log('App is rendering');
   ```

### Component Rendering Issues

**Problem**: React components don't render as expected.

**Solution**:
1. Check component props in React DevTools
2. Verify state is being updated correctly
3. Check for conditional rendering issues
4. Add console logging:
   ```jsx
   console.log('Component state:', this.state);
   // or for hooks
   console.log('Component state:', stateVariable);
   ```

## Docker Issues

### Container Won't Start

**Problem**: Docker containers fail to start.

**Solution**:
1. Check container logs:
   ```bash
   docker-compose logs backend
   ```
2. Look for specific error messages
3. Verify environment variables are set correctly
4. Check for port conflicts with other running services
5. Ensure Docker has enough resources allocated

### Volume Permission Issues

**Problem**: Container can't write to mounted volumes.

**Solution**:
1. Check volume permissions:
   ```bash
   ls -la /path/to/volume
   ```
2. Fix ownership:
   ```bash
   sudo chown -R $(id -u):$(id -g) /path/to/volume
   ```
3. Update the Dockerfile to use the same user ID as your host:
   ```dockerfile
   ARG USER_ID=1000
   ARG GROUP_ID=1000
   RUN groupadd -g $GROUP_ID appuser && \
       useradd -m -u $USER_ID -g appuser appuser
   ```

### Image Build Failures

**Problem**: Docker image build fails.

**Solution**:
1. Check the error message in the build log
2. Verify all required files are in the build context
3. Check network connectivity if pulling base images
4. Try building with no cache:
   ```bash
   docker-compose build --no-cache
   ```

## WebSocket Issues

### WebSocket Connection Fails

**Problem**: Frontend can't establish WebSocket connection.

**Solution**:
1. Check browser console for WebSocket errors
2. Verify the WebSocket URL in the frontend .env file:
   ```
   # Local development
   REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws
   
   # Docker
   REACT_APP_WEBSOCKET_URL=ws://localhost/ws
   ```
3. Ensure the Redis server is running
4. Verify that Daphne/Channels is configured correctly
5. Check server logs for WebSocket connection attempts

### Real-time Updates Not Working

**Problem**: Changes don't propagate in real-time to other clients.

**Solution**:
1. Check WebSocket connection status
2. Verify channel groups are configured correctly:
   ```python
   # consumers.py
   self.room_group_name = f'project_{self.project_id}'
   ```
3. Ensure signal handlers are sending to the correct channel:
   ```python
   # signals.py
   @receiver(post_save, sender=Task)
   def task_post_save(sender, instance, **kwargs):
       channel_layer = get_channel_layer()
       async_to_sync(channel_layer.group_send)(
           f'project_{instance.project_id}',
           {
               'type': 'task_update',
               'data': TaskSerializer(instance).data
           }
       )
   ```

## Authentication Issues

### JWT Token Issues

**Problem**: Authentication fails with JWT token errors.

**Solution**:
1. Check if token is expired:
   ```javascript
   // Browser console
   const token = localStorage.getItem('access_token');
   const payload = JSON.parse(atob(token.split('.')[1]));
   console.log('Expiry:', new Date(payload.exp * 1000));
   ```
2. Verify the `JWT_SIGNING_KEY` is set correctly in environment variables
3. Ensure refresh token flow is working correctly
4. Clear localStorage and re-login:
   ```javascript
   localStorage.clear();
   window.location.href = '/login';
   ```

### User Registration Fails

**Problem**: User registration endpoint returns errors.

**Solution**:
1. Check validation errors in the response
2. Verify email configuration if email verification is required
3. Look for duplicate username/email issues
4. Check Djoser settings if using Djoser for authentication
5. Ensure password meets complexity requirements:
   ```python
   # settings.py
   AUTH_PASSWORD_VALIDATORS = [
       {
           'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
           'OPTIONS': {
               'min_length': 8,
           }
       },
       # Other validators...
   ]
   ```

## Database Issues

### Migration Conflicts

**Problem**: Database migration conflicts or inconsistencies.

**Solution**:
1. Back up your database first
2. Reset the migration state and start fresh:
   ```bash
   # List all migrations
   python manage.py showmigrations
   
   # Zero out app migrations
   python manage.py migrate app_name zero
   
   # Recreate and apply migrations
   python manage.py makemigrations app_name
   python manage.py migrate app_name
   ```
3. For SQLite, consider:
   ```bash
   # Back up database
   cp db.sqlite3 db.sqlite3.bak
   
   # Remove and recreate
   rm db.sqlite3
   python manage.py migrate
   ```

### Database Locks (SQLite)

**Problem**: SQLite database locks during concurrent access.

**Solution**:
1. Reduce concurrent operations
2. Ensure you close connections properly
3. Consider using a more robust database like PostgreSQL
4. For development, try:
   ```python
   # settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
           'OPTIONS': {
               'timeout': 20,  # Increase timeout
           }
       }
   }
   ```

## Email Issues

### Emails Not Sending

**Problem**: Application doesn't send emails.

**Solution**:
1. Verify email configuration in `.env`:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```
2. For Gmail, ensure you're using an App Password if 2FA is enabled
3. Test email configuration:
   ```bash
   python -m email_test recipient@example.com
   ```
4. Check for firewall issues blocking outbound SMTP
5. Try a different email service like SendGrid

### Email Templates Not Rendering

**Problem**: Email templates render incorrectly or with missing context.

**Solution**:
1. Check template path: `templates/emails/notification.html`
2. Verify template context is passed correctly:
   ```python
   send_mail(
       subject='Notification',
       message=strip_tags(html_message),  # Fallback plain text
       from_email=settings.DEFAULT_FROM_EMAIL,
       recipient_list=[user.email],
       html_message=render_to_string('emails/notification.html', context),
   )
   ```
3. Ensure template syntax is correct
4. Try debugging with a simplified template

## Performance Issues

### Slow API Responses

**Problem**: API endpoints are slow to respond.

**Solution**:
1. Use Django Debug Toolbar to identify slow queries
2. Add database indexes to frequently queried fields:
   ```python
   class Task(models.Model):
       # ... other fields
       project = models.ForeignKey(Project, on_delete=models.CASCADE, db_index=True)
       due_date = models.DateField(db_index=True, null=True)
   ```
3. Use select_related and prefetch_related to reduce queries:
   ```python
   # Efficient
   tasks = Task.objects.select_related('project', 'assignee').prefetch_related('labels')
   ```
4. Implement caching for expensive operations:
   ```python
   from django.core.cache import cache
   
   def get_project_stats(project_id):
       cache_key = f'project_stats_{project_id}'
       stats = cache.get(cache_key)
       if stats is None:
           # Expensive calculation
           stats = calculate_project_stats(project_id)
           cache.set(cache_key, stats, 60 * 15)  # Cache for 15 minutes
       return stats
   ```

### High Memory Usage in Docker

**Problem**: Docker containers use excessive memory.

**Solution**:
1. Set memory limits in docker-compose.yml:
   ```yaml
   services:
     backend:
       # ...
       deploy:
         resources:
           limits:
             memory: 512M
   ```
2. Check for memory leaks in long-running processes
3. Adjust Python garbage collection thresholds:
   ```python
   # In a startup script
   import gc
   gc.set_threshold(700, 10, 5)
   ```
4. Optimize Celery worker concurrency:
   ```
   # entrypoint-celery.sh
   celery -A projectmanagement worker --concurrency=2 --loglevel=info
   ```

## Additional Help

If you encounter an issue not covered in this guide:

1. Check the project's issue tracker for similar issues
2. Search documentation for relevant terms
3. Review Django and React documentation for framework-specific issues
4. For urgent issues, contact the project maintainers

Remember to include the following when reporting issues:
- Exact error messages
- Steps to reproduce
- Environment details (OS, Python/Node versions, etc.)
- Log output
- Screenshots if relevant 