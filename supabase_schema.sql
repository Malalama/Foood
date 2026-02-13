-- Supabase Schema for Fridge to Recipe App
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table to store recipe search history
CREATE TABLE IF NOT EXISTS recipe_searches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ingredients_detected TEXT NOT NULL,
    recipes_suggested TEXT NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store saved/favorite recipes
CREATE TABLE IF NOT EXISTS saved_recipes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    recipe_name TEXT NOT NULL,
    recipe_content TEXT NOT NULL,
    ingredients TEXT[],
    tags TEXT[],
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store user preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    dietary_restrictions TEXT[],
    preferred_cuisines TEXT[],
    skill_level TEXT CHECK (skill_level IN ('beginner', 'intermediate', 'advanced')),
    household_size INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_recipe_searches_user_id ON recipe_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_recipe_searches_created_at ON recipe_searches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_recipes_user_id ON saved_recipes(user_id);

-- Row Level Security (RLS) Policies
ALTER TABLE recipe_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own recipe searches
CREATE POLICY "Users can view own recipe searches" ON recipe_searches
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert own recipe searches" ON recipe_searches
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Policy: Users can only see their own saved recipes
CREATE POLICY "Users can view own saved recipes" ON saved_recipes
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own saved recipes" ON saved_recipes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own saved recipes" ON saved_recipes
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved recipes" ON saved_recipes
    FOR DELETE USING (auth.uid() = user_id);

-- Policy: Users can only manage their own preferences
CREATE POLICY "Users can view own preferences" ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_recipe_searches_updated_at
    BEFORE UPDATE ON recipe_searches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Allow anonymous access for demo purposes (remove for production)
-- This allows the app to work without user authentication
CREATE POLICY "Allow anonymous inserts" ON recipe_searches
    FOR INSERT WITH CHECK (user_id IS NULL);

CREATE POLICY "Allow anonymous reads" ON recipe_searches
    FOR SELECT USING (user_id IS NULL);
