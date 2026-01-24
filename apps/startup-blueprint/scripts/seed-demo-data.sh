#!/bin/bash
# Seed demo data into D1 database

set -euo pipefail

DB_NAME="${1:-startup_blueprint_db}"

echo "📦 Seeding demo data into ${DB_NAME}..."

# Check if demo user already exists
EXISTING=$(wrangler d1 execute "${DB_NAME}" \
  --command="SELECT COUNT(*) as count FROM users WHERE id='demo-user-1'" \
  --json | jq -r '.[0].count' || echo "0")

if [ "${EXISTING}" -gt 0 ]; then
  echo "⚠ Demo data already exists, skipping..."
  exit 0
fi

# Insert demo user
wrangler d1 execute "${DB_NAME}" --command="
INSERT INTO users (id, email, name, picture_url)
VALUES (
  'demo-user-1',
  'demo@example.com',
  'Demo User',
  'https://placehold.co/100x100'
)
" || true

# Insert demo activity
wrangler d1 execute "${DB_NAME}" --command="
INSERT INTO activity (user_id, action, details)
VALUES 
  ('demo-user-1', 'Account created', 'Welcome to Startup Blueprint'),
  ('demo-user-1', 'Demo data seeded', 'Initial setup completed')
" || true

echo "✓ Demo data seeded successfully"
