-- SQL Schema for verified users on the Nigeria Construction AI Platform
-- This table is used to restrict access only to registered and verified identities.

CREATE TABLE IF NOT EXISTS public.app_verified_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    username TEXT,
    provider TEXT NOT NULL DEFAULT 'email', -- 'email', 'google', 'github', 'yahoo'
    role TEXT DEFAULT 'analyst',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast email lookups
CREATE INDEX IF NOT EXISTS idx_app_verified_users_email ON public.app_verified_users(email);

-- RLS (Row Level Security) - Restricted to authenticated reading
ALTER TABLE public.app_verified_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public registration" ON public.app_verified_users
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow users to read their own data" ON public.app_verified_users
    FOR SELECT USING (auth.jwt() ->> 'email' = email);
