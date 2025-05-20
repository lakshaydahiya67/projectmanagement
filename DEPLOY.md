# Deployment Guide for Render.com

This guide will walk you through deploying the Project Management application to Render.com.

## Prerequisites

1. A Render.com account (sign up at https://render.com/)
2. A GitHub/GitLab account with your code pushed to a repository
3. Docker installed locally (for testing)

## Deployment Steps

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Prepare for deployment"
git push origin main  # or your branch name
```

### 2. Create a New Web Service on Render

1. Go to your Render dashboard
2. Click "New +" and select "Web Service"
3. Connect your GitHub/GitLab repository
4. Configure the service:
   - **Name**: projectmanagement (or your preferred name)
   - **Region**: Choose the one closest to your users
   - **Branch**: main (or your deployment branch)
   - **Runtime**: Docker
   - **Build Command**: (leave empty, we're using a Dockerfile)
   - **Start Command**: `gunicorn projectmanagement.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: Free

### 3. Configure Environment Variables

Add these environment variables in the Render dashboard under Environment:

```
DJANGO_SETTINGS_MODULE=projectmanagement.settings
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here  # Generate a strong secret key
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Database
DATABASE_PATH=/opt/render/project/src/db.sqlite3

# Email settings (configure as needed)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 4. Deploy the Application

1. Click "Create Web Service"
2. Render will build and deploy your application
3. Monitor the logs for any issues

### 5. Set Up the Database

After the first deployment:

1. Go to the Render shell or connect via SSH
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
4. Collect static files (should be handled by the build script):
   ```bash
   python manage.py collectstatic --noinput
   ```

## Post-Deployment

1. Access the admin panel at `https://your-render-app.onrender.com/admin/`
2. Set up your domain (if needed) in the Render dashboard

## Troubleshooting

- **Build Fails**: Check the logs in the Render dashboard
- **Static Files Not Loading**: Ensure `collectstatic` ran successfully
- **Database Issues**: Verify your database file is writable by the application

## Monitoring

- Monitor your application in the Render dashboard
- Set up alerts for errors and downtime
- Check the logs for any issues

## Scaling

- Upgrade your plan if you need more resources
- Consider adding a CDN for static files
- Set up monitoring and alerting for production use
