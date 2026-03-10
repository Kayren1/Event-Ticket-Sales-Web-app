# Vercel Deployment Checklist

Use this checklist to ensure your project is ready for Vercel deployment.

## ✅ Pre-Deployment Checklist

### Code Preparation
- [ ] All code is committed to Git
- [ ] No sensitive data (API keys, passwords) in committed code
- [ ] `.env.example` exists with all required variables documented
- [ ] `.gitignore` is properly configured
- [ ] `vercel.json` is present and configured
- [ ] `api/index.py` exists as the serverless entry point
- [ ] `requirements.txt` updated with:
  - [ ] `gunicorn`
  - [ ] `whitenoise`
  - [ ] `dj-database-url`

### Django Configuration
- [ ] `settings.py` updated for production:
  - [ ] Environment variables support (using `os.environ.get()`)
  - [ ] `DEBUG` set to use `DJANGO_DEBUG` environment variable
  - [ ] `SECRET_KEY` set to use `DJANGO_SECRET_KEY` environment variable
  - [ ] `ALLOWED_HOSTS` uses `ALLOWED_HOSTS` environment variable
  - [ ] `CSRF_TRUSTED_ORIGINS` includes Vercel and custom domains
  - [ ] WhiteNoise middleware added
  - [ ] Static files storage configured
  - [ ] Database configuration supports `DATABASE_URL`
  - [ ] Email backend configured with environment variables
  - [ ] Stripe keys use environment variables
  - [ ] Celery configuration uses environment variables

### Infrastructure Setup
- [ ] Cloud database created (Supabase recommended: supabase.com)
  - [ ] New Supabase project created
  - [ ] Database connection string obtained
  - [ ] Password set and confirmed
  - [ ] Connection tested locally

- [ ] Redis instance created (Redis Cloud: redis.com/cloud)
  - [ ] Redis URL obtained
  - [ ] Connection tested

- [ ] Stripe account configured
  - [ ] Test keys obtained (for staging)
  - [ ] Production keys obtained (for production)
  - [ ] Webhook endpoint configured

### Vercel Setup
- [ ] Vercel account created at [vercel.com](https://vercel.com)
- [ ] GitHub repository connected to Vercel
- [ ] Project created in Vercel dashboard

### Environment Variables in Vercel
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY=<generated-secure-key>`
- [ ] `ALLOWED_HOSTS=<your-domain>`
- [ ] `DATABASE_URL=<cloud-database-url>`
- [ ] `STRIPE_PUBLIC_KEY=<your-key>`
- [ ] `STRIPE_SECRET_KEY=<your-key>`
- [ ] `STRIPE_WEBHOOK_SECRET=<your-secret>`
- [ ] `CELERY_BROKER_URL=<your-redis-url>`
- [ ] `EMAIL_HOST=<your-smtp>`
- [ ] `EMAIL_PORT=587`
- [ ] `EMAIL_USE_TLS=True`
- [ ] `EMAIL_HOST_USER=<your-email>`
- [ ] `EMAIL_HOST_PASSWORD=<your-password>`
- [ ] `CSRF_TRUSTED_ORIGINS=<your-domains>`

### Security
- [ ] Generated a new `DJANGO_SECRET_KEY` (not the default)
- [ ] Stripe API keys are for the correct environment (test/production)
- [ ] Database password is strong
- [ ] No hardcoded secrets in code
- [ ] HTTPS will be enforced (`SECURE_SSL_REDIRECT=True`)
- [ ] Security headers are set

### Testing
- [ ] Local database migrations run successfully
- [ ] `python manage.py check` passes
- [ ] `python manage.py collectstatic` completes without errors
- [ ] Static files load correctly locally
- [ ] Stripe integration tested
- [ ] Email sending tested (if configured)
- [ ] Celery tasks tested locally (if using)

### Documentation
- [ ] `VERCEL_DEPLOYMENT.md` is in the repository
- [ ] `.env.example` has all required variables
- [ ] README.md includes deployment instructions
- [ ] Any deployment-specific scripts (build.sh) are documented

### Post-Deployment
- [ ] Verify deployment URLs are working
- [ ] Test all major features (auth, payments, etc.)
- [ ] Check error logs in Vercel dashboard
- [ ] Verify static files are serving correctly
- [ ] Set up custom domain (if applicable)
- [ ] Configure DNS records (if custom domain)
- [ ] Enable automatic deployments from Git (if desired)
- [ ] Set up monitoring/error tracking (Sentry, etc.)

## 🚀 Deployment Commands

### Local Testing Before Deploy
```bash
# Test local build
bash build.sh

# Or manually:
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
```

### Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy (staging)
vercel

# Deploy to production
vercel --prod
```

### Post-Deployment Migrations
```bash
# Create superuser on production database
python manage.py createsuperuser --settings=paperweight.settings
```

## ⚠️ Critical Security Notes

1. **NEVER** commit `.env` file or secrets to Git
2. **ALWAYS** use `DJANGO_SECRET_KEY=False` for Vercel SECRET_KEY, not the default
3. **USE PRODUCTION** Stripe keys in production environment
4. **TEST THOROUGHLY** before going live to production
5. **MONITOR** error logs and performance after deployment
6. **BACKUP** your database regularly
7. **ENABLE HTTPS** for custom domains

## 🆘 Need Help?

- Check deployment logs: Vercel Dashboard → Deployments → Logs
- Re-read: `VERCEL_DEPLOYMENT.md`
- Verify environment variables are set correctly
- Ensure database and Redis are accessible
- Check Django logs for errors

## 📋 Useful Links

- [Vercel Docs](https://vercel.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [PlanetScale Docs](https://docs.planetscale.com/)
- [Redis Cloud Docs](https://docs.redis.com/latest/)
- [Stripe Documentation](https://stripe.com/docs)

---

**Status**: Start with the checklist above to prepare your project for deployment. Once all items are checked, you're ready to deploy!
