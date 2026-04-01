-- Vetted Carpet Cleaners starter schema for Supabase/Postgres

create extension if not exists pgcrypto;

create table if not exists cleaners (
  id uuid primary key default gen_random_uuid(),
  business_name text not null,
  slug text unique,
  owner_name text,
  email text not null,
  phone text,
  website text,
  description text,
  county text,
  town text,
  postcode text,
  approved_status text not null default 'pending',
  featured_status boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists services (
  id bigserial primary key,
  name text unique not null
);

create table if not exists cleaner_services (
  cleaner_id uuid not null references cleaners(id) on delete cascade,
  service_id bigint not null references services(id) on delete cascade,
  primary key (cleaner_id, service_id)
);

create table if not exists badges (
  id bigserial primary key,
  badge_name text unique not null,
  badge_description text
);

create table if not exists cleaner_badges (
  cleaner_id uuid not null references cleaners(id) on delete cascade,
  badge_id bigint not null references badges(id) on delete cascade,
  verified_at timestamptz,
  expires_at timestamptz,
  primary key (cleaner_id, badge_id)
);

create table if not exists applications (
  id uuid primary key default gen_random_uuid(),
  cleaner_id uuid references cleaners(id) on delete set null,
  status text not null default 'submitted',
  notes text,
  submitted_at timestamptz not null default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  cleaner_id uuid not null references cleaners(id) on delete cascade,
  doc_type text not null,
  file_url text,
  expiry_date date,
  checked_at timestamptz,
  checked_by text,
  created_at timestamptz not null default now()
);

create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  cleaner_id uuid not null references cleaners(id) on delete cascade,
  reviewer_name text,
  rating numeric(2,1) check (rating >= 0 and rating <= 5),
  review_text text,
  review_date date,
  approved boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  cleaner_id uuid not null references cleaners(id) on delete cascade,
  customer_name text,
  customer_email text,
  customer_phone text,
  message text,
  postcode text,
  lead_status text not null default 'new',
  created_at timestamptz not null default now()
);

insert into services (name) values
('Carpet Cleaning'),
('Upholstery Cleaning'),
('Rug Cleaning'),
('Commercial Cleaning'),
('Stain Removal')
on conflict (name) do nothing;

insert into badges (badge_name, badge_description) values
('Insurance Verified', 'Cleaner has supplied evidence of valid insurance'),
('Business Reviewed', 'Core trading information has been manually reviewed'),
('Identity Checked', 'Identity documentation has been checked where applicable'),
('Commercial Capable', 'Cleaner states they can handle commercial work'),
('Wool Safe Aware', 'Cleaner indicates knowledge of wool and delicate fibre handling'),
('Specialist Stain Removal', 'Cleaner states specialist stain treatment capability')
on conflict (badge_name) do nothing;
