-- =====================================================
-- 数据库索引优化脚本
-- 功能：为常用查询字段添加索引，提升查询性能
-- 执行方式：在 MySQL 中执行此脚本
-- =====================================================

USE `wb`;

-- =====================================================
-- 1. article 表索引优化
-- =====================================================

-- 检查并添加 authorName 索引（按作者查询）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'article' 
                     AND index_name = 'idx_author_name');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `article` ADD INDEX `idx_author_name` (`authorName`(100))', 
              'SELECT "索引 idx_author_name 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 likeNum 索引（按点赞数排序）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'article' 
                     AND index_name = 'idx_like_num');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `article` ADD INDEX `idx_like_num` (`likeNum`)', 
              'SELECT "索引 idx_like_num 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 commentsLen 索引（按评论数排序）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'article' 
                     AND index_name = 'idx_comments_len');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `article` ADD INDEX `idx_comments_len` (`commentsLen`)', 
              'SELECT "索引 idx_comments_len 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加复合索引（时间+点赞数，用于热门文章查询）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'article' 
                     AND index_name = 'idx_created_likes');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `article` ADD INDEX `idx_created_likes` (`created_at`, `likeNum`)', 
              'SELECT "索引 idx_created_likes 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 2. comments 表索引优化
-- =====================================================

-- 检查并添加 created_at 索引（按时间查询评论）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'comments' 
                     AND index_name = 'idx_created_at');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `comments` ADD INDEX `idx_created_at` (`created_at`)', 
              'SELECT "索引 idx_created_at 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 authorName 索引（按作者查询评论）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'comments' 
                     AND index_name = 'idx_author_name');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `comments` ADD INDEX `idx_author_name` (`authorName`(100))', 
              'SELECT "索引 idx_author_name 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 like_counts 索引（按点赞数排序）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'comments' 
                     AND index_name = 'idx_like_counts');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `comments` ADD INDEX `idx_like_counts` (`like_counts`)', 
              'SELECT "索引 idx_like_counts 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加复合索引（文章ID+时间，用于文章评论列表）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'comments' 
                     AND index_name = 'idx_article_created');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `comments` ADD INDEX `idx_article_created` (`articleId`, `created_at`)', 
              'SELECT "索引 idx_article_created 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 3. user 表索引优化
-- =====================================================

-- 检查并添加 username 索引（登录查询）
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                     WHERE table_schema = 'wb' 
                     AND table_name = 'user' 
                     AND index_name = 'idx_username');
SET @sql = IF(@index_exists = 0, 
              'ALTER TABLE `user` ADD INDEX `idx_username` (`username`)', 
              'SELECT "索引 idx_username 已存在"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 4. 分析表（更新统计信息）
-- =====================================================
ANALYZE TABLE `article`;
ANALYZE TABLE `comments`;
ANALYZE TABLE `user`;

-- =====================================================
-- 5. 显示索引信息
-- =====================================================
SELECT '=== article 表索引 ===' AS info;
SHOW INDEX FROM `article`;

SELECT '=== comments 表索引 ===' AS info;
SHOW INDEX FROM `comments`;

SELECT '=== user 表索引 ===' AS info;
SHOW INDEX FROM `user`;

SELECT '数据库索引优化完成！' AS result;
