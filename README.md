# Vetted Carpet Cleaners starter kit

This is a starter website for a trust first lead generation platform for vetted carpet cleaners.

## What is included

- Public homepage
- Directory search page using sample JSON
- Apply to join page
- Vetting process page
- Example cleaner profile page
- Admin dashboard starter layout
- Supabase starter schema

## Recommended stack

- GitHub Pages for the public website
- Supabase for the database, auth, storage, and approval flow
- Cloudflare Turnstile for spam protection
- Optional Stripe later for subscriptions or featured listings

## Folder structure

- `index.html` main homepage
- `find.html` public search page
- `apply.html` cleaner application page
- `how-it-works.html` public trust process page
- `profile.html` example profile page
- `admin/admin.html` admin layout demo
- `data/cleaners.json` sample listings data
- `supabase/schema.sql` starter database schema

## How to use this on GitHub

1. Create a GitHub repository
2. Upload the contents of this folder
3. Enable GitHub Pages from the main branch
4. Your static public site will go live from GitHub Pages

## Important

GitHub Pages is static hosting.
The public site can live there, but the real application logic should live in Supabase.

## Suggested next build steps

1. Create the Supabase project
2. Run `supabase/schema.sql`
3. Replace sample JSON with live Supabase queries
4. Add cleaner login and admin login
5. Add document upload storage buckets
6. Add approval and renewal workflow
7. Add SEO town and service pages

## Good future features

- postcode search
- featured cleaner placements
- territory exclusivity
- lead routing
- review moderation
- expiring insurance alerts
- complaint and dispute handling
