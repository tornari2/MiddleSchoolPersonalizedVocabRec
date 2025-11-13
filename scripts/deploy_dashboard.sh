#!/bin/bash
# Deploy dashboard to S3 (secure hosting)

set -e

# Configuration
BUCKET_NAME="vocab-dashboard-prod"
REGION="us-east-1"
PROJECT_DIR="/Users/michaeltornaritis/Desktop/WK5_MiddleSchoolPersonalizedVocabRec"

echo "🚀 Deploying Vocabulary Dashboard to Production"
echo "=============================================="

# Check if bucket exists, create if not
if ! aws s3 ls "s3://${BUCKET_NAME}" 2>&1 > /dev/null; then
    echo "📦 Creating S3 bucket: ${BUCKET_NAME}"
    aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"
    echo "✅ Created bucket: ${BUCKET_NAME}"
else
    echo "📦 Using existing bucket: ${BUCKET_NAME}"
fi

# Regenerate dashboard data
echo "📊 Regenerating dashboard data..."
cd "${PROJECT_DIR}"
python3 scripts/create_dashboard_data.py

# Deploy files
echo "📤 Uploading dashboard files..."
cd dashboard
aws s3 sync . "s3://${BUCKET_NAME}/" --delete --exclude "*.git*" --exclude "*.DS_Store"

echo ""
echo "✅ Dashboard deployed successfully!"
echo ""
echo "🔒 Security Note: Files are stored securely in S3 with CloudFront access"
echo ""
echo "🌐 Access URLs:"
echo ""
echo "   🔗 Permanent URL (always accessible):"
echo "   https://dzo1vamgxcpsx.cloudfront.net"
echo ""
echo "   🏠 Local Development Access:"
echo "   cd ${PROJECT_DIR} && python3 -m http.server 8000"
echo "   Visit: http://localhost:8000/dashboard/"
echo ""
echo "   🔐 Temporary Secure Access:"
echo "   aws s3 presign s3://${BUCKET_NAME}/index.html --expires-in 3600"
echo ""
echo "🔄 To update with new data:"
echo "   Run: ./deploy_dashboard.sh"
echo "   (This regenerates data and redeploys to both S3 and CloudFront)"
echo ""
echo "📊 Dashboard includes:"
echo "   - 20 students with 4 weeks of historical data"
echo "   - Week 5 data ready to load"
echo "   - Interactive charts and recommendations"
echo "   - Export functionality for reports"
echo ""
echo "⚡ Performance: CloudFront provides global CDN acceleration"
