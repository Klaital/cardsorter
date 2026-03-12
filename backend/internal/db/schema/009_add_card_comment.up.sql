-- Add comment field to cards table
ALTER TABLE cards ADD COLUMN comment TEXT NOT NULL DEFAULT '';
