create extension if not exists pgcrypto;

create table if not exists public.official_assets (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  hashes jsonb not null,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.detections (
  id uuid primary key default gen_random_uuid(),
  reddit_url text not null,
  reddit_post_title text not null,
  classification text not null check (classification in ('Piracy', 'Meme', 'Transformative')),
  risk_score integer not null check (risk_score >= 0 and risk_score <= 100),
  reasoning text not null,
  matched_asset_id uuid references public.official_assets(id) on delete set null,
  matched_asset_filename text,
  thumbnail_hash text not null,
  distance integer not null,
  scanned_at timestamptz not null default timezone('utc', now())
);

create index if not exists official_assets_created_at_idx
  on public.official_assets (created_at desc);

create index if not exists detections_scanned_at_idx
  on public.detections (scanned_at desc);

create index if not exists detections_classification_idx
  on public.detections (classification);
