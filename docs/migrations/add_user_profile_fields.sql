-- Migration: Add profile fields to user table
-- Run this SQL against your MySQL database before using the profile feature

ALTER TABLE `user` ADD COLUMN `nickname` VARCHAR(50) DEFAULT NULL;
ALTER TABLE `user` ADD COLUMN `email` VARCHAR(100) DEFAULT NULL;
ALTER TABLE `user` ADD COLUMN `bio` VARCHAR(200) DEFAULT NULL;
ALTER TABLE `user` ADD COLUMN `avatar_color` VARCHAR(7) DEFAULT '#2563EB';
