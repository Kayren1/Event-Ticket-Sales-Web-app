# Vercel Deployment Guide

This guide walks you through deploying your Django Event Ticket Sales Web App to Vercel.

## Prerequisites

Before deploying to Vercel, ensure you have:

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Git Repository**: Your code pushed to GitHub, GitLab, or Bitbucket
3. **Cloud Database**: A MySQL database hosted on a service like:
   - [PlanetScale](https://planetscale.com/) (recommended for MySQL)
   - [AWS RDS](https://aws.amazon.com/rds/)
   - [DigitalOcean Managed Databases](https://www.digitalocean.com/products/managed-databases/)
4. **Redis Instance** (for Celery):
   - [Redis Cloud](https://redis.com/cloud/overview/) (recommended)
   - [Upstash Redis](https://upstash.com/)
   - [AWS ElastiCache](https://aws.amazon.com/elasticache/)

## Step 1: Set Up Cloud Database

### Using PlanetScale (Highly Recommended for MySQL)

1. Create a PlanetScale account at [planetscale.com](https://planetscale.com)
2. Create a new database called "paperweight"
3. Create a password and generate a connection string
4. The connection string will look like: `mysql://username:password@aws.connect.psdb.cloud/paperweight?sslaccept=strict`

## Step 2: Set Up Redis (For Celery)

1. Create an account at [redis.com/cloud](https://redis.com/cloud/overview/)
2. Create a new database
3. Get the connection URL (typically: `redis://default:password@host:port`)

## Step 3: Prepare Your Repository

1. Ensure all files are committed to git:
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. Verify these files exist in your repository:
   - `vercel.json` - Vercel configuration
   - `api/index.py` - Serverless entry point
   - `.env.example` - Environment variables template
   - `requirements.txt` - Updated with gunicorn, whitenoise, dj-database-url

## Step 4: Deploy to Vercel

### Option A: Using Vercel CLI (Recommended)

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Deploy your project:
   ```bash
   vercel
   ```

3. Follow the prompts to link your Git repository

### Option B: Using Vercel Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Select your Git repository
4. Click "Import"

## Step 5: Configure Environment Variables

In your Vercel project dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add the following variables (copy from `.env.example`):

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generate-a-new-secure-key>
ALLOWED_HOSTS=your-domain.vercel.app,your-custom-domain.com
DATABASE_URL=<your-planetscale-connection-string>
STRIPE_PUBLIC_KEY=<your-stripe-key>
STRIPE_SECRET_KEY=<your-stripe-secret>
STRIPE_WEBHOOK_SECRET=<your-stripe-webhook>
CELERY_BROKER_URL=<your-redis-url>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<your-email>
EMAIL_HOST_PASSWORD=<your-app-password>
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://your-domain.vercel.app
```

### Generating a Secure SECRET_KEY

Generate a new secret key by running:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use a quick Python one-liner:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 6: Set Up Database Migrations

After deployment, run migrations on your cloud database:

```bash
python manage.py migrate --settings=paperweight.settings
python manage.py createsuperuser --settings=paperweight.settings
```

Or, create a management command that runs on deployment.

## Step 7: Configure Stripe Webhooks

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Webhooks**
3. Add a new endpoint: `https://your-domain.com/api/payments/webhook/`
4. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
5. Copy the webhook signing secret to Vercel environment variables as `STRIPE_WEBHOOK_SECRET`

## Step 8: Set Up Celery Tasks (Optional but Recommended)

For background tasks, you'll need a separate Celery worker. Options:

### Option A: Use Vercel Cron (Simple, Free)

Add cron jobs in `vercel.json` for periodic tasks.

### Option B: Dedicated Celery Worker

Deploy a separate Celery worker instance on:
- [Render.com](https://render.com/)
- [Railway.app](https://railway.app/)
- [Heroku](https://www.heroku.com/) (paid)
- [DigitalOcean App Platform](https://www.digitalocean.com/products/app-platform/)

## Step 9: Configure Custom Domain (Optional)

1. In Vercel dashboard, go to **Settings** → **Domains**
2. Add your custom domain
3. Update DNS records as instructed

## Step 10: Monitor Deployment

Check your deployment status:
- Vercel Dashboard shows deployment status and logs
- Check Vercel Analytics for performance insights
- Monitor error logs in the **Logs** tab

## Troubleshooting

### Database Connection Errors

Make sure your `DATABASE_URL` is correct and the database is accessible:

```bash
mysql -h <host> -u <user> -p <database>
```

### Static Files Not Loading

Ensure `collectstatic` runs during build:
```bash
python manage.py collectstatic --noinput
```

### CORS/CSRF Issues

Verify `CSRF_TRUSTED_ORIGINS` includes your Vercel domain and custom domain.

### Celery Tasks Not Running

- Check Redis connection is working
- Verify `CELERY_BROKER_URL` is set correctly
- Deploy a separate Celery worker instance

### Memory Limit Issues

If hitting memory limits, increase in `vercel.json`:
```json
"functions": {
  "api/index.py": {
    "memory": 3008,
    "maxDuration": 60
  }
}
```

## Important Security Notes

⚠️ **CRITICAL**: Before going to production:

1. **Generate a new `DJANGO_SECRET_KEY`** - Never use the default hardcoded key
2. **Set `DEBUG=False`** in production
3. **Use HTTPS** - Enable `SECURE_SSL_REDIRECT=True`
4. **Rotate Stripe keys** - Use production keys, not test keys
5. **Set strong database passwords**
6. **Use environment variables** for all secrets
7. **Enable HTTPS** for all custom domains
8. **Review Django security checklist**: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

## Performance Optimization

1. **Enable static file caching** with WhiteNoise
2. **Use a CDN** for media files and static assets
3. **Optimize database queries** with Django ORM best practices
4. **Use database connection pooling** for cloud databases
5. **Monitor and optimize slow queries**

## Cost Considerations

- **Vercel**: Free tier available, charges for usage beyond limits
- **PlanetScale**: Free tier (3 branches), paid for additional resources
- **Redis Cloud**: Free tier (30 MB), paid for larger databases
- **Stripe**: 2.9% + $0.30 per transaction (US)

## Support

- Vercel Docs: https://vercel.com/docs
- Django Docs: https://docs.djangoproject.com/
- PlanetScale Help: https://planetscale.com/help
- Stripe Documentation: https://stripe.com/docs

## Next Steps After Deployment

1. Test all functionality on production
2. Set up monitoring and error tracking (e.g., Sentry)
3. Configure backup strategy for database
4. Set up analytics and logging
5. Plan for scaling as traffic grows
