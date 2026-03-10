#!/bin/bash
# Local build script for testing Vercel deployment locally

echo "=== Vercel Build Simulation ==="
echo ""

# Step 1: Install dependencies
echo "Step 1: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies"
    exit 1
fi

# Step 2: Check Django setup
echo ""
echo "Step 2: Checking Django setup..."
python manage.py check
if [ $? -ne 0 ]; then
    echo "Django check failed"
    exit 1
fi

# Step 3: Migrate database
echo ""
echo "Step 3: Running migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Migrations failed"
    exit 1
fi

# Step 4: Collect static files
echo ""
echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo "Static files collection failed"
    exit 1
fi

echo ""
echo "=== Build Success ==="
echo ""
echo "Next steps:"
echo "1. Set up a cloud database (PlanetScale, AWS RDS, etc.)"
echo "2. Configure environment variables in Vercel"
echo "3. Deploy with: vercel --prod"
echo ""
