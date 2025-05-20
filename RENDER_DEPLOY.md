# Deploying to Render.com

This project is configured to be deployed on Render.com using their free tier.

## What Gets Deployed

1. Django Backend
2. React Frontend
3. PostgreSQL Database
4. Redis Instance

## How to Deploy

### Prerequisites

1. Create a Render.com account
2. Have your code in a GitHub repository

### Deployment Steps

1. **Connect your GitHub repository to Render**
   - Log in to your Render dashboard
   - Click "New" -> "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing this project

2. **Configure the Blueprint**
   - Render will automatically detect the `render.yaml` file
   - Review the services that will be created
   - Click "Apply" to start the deployment

3. **Monitor the Deployment**
   - Render will create all the services defined in `render.yaml`
   - It will run the build scripts and set up the database
   - You can monitor the progress in the dashboard

4. **Access Your Application**
   - Once deployment is complete, access your frontend at:
     `https://projectmanagement-frontend.onrender.com`
   - The backend API is available at:
     `https://projectmanagement-backend.onrender.com`

## Environment Variables

The following environment variables are automatically set up by Render:

- `DATABASE_URL`: Connection string for PostgreSQL
- `DJANGO_SECRET_KEY`: Auto-generated secure key
- `DJANGO_SUPERUSER_PASSWORD`: Auto-generated admin password

## Troubleshooting

If you encounter issues:

1. Check the service logs in the Render dashboard
2. Ensure the health check endpoint is accessible
3. Verify that all required dependencies are in `requirements.txt`
4. Make sure the frontend build process completes successfully

## Making Updates

To update your application:

1. Push changes to your GitHub repository
2. Render will automatically redeploy the affected services

## Further Customization

To customize your deployment:
1. Edit the `render.yaml` file
2. Update environment variables in the Render dashboard
3. Configure custom domains in the Render dashboard
