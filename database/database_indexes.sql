-- 数据库索引优化脚本
-- 功能：为常用查询字段添加索引，提升查询性能
-- 作者：微博舆情分析系统
-- 执行方式：mysql -u root -p wb < database_indexes.sql

-- ===== 文章表索引 =====

-- 为created_at字段添加索引（用于时间排序和筛选）
CREATE INDEX IF NOT EXISTS idx_article_created_at ON article(created_at);

-- 为likeNum字段添加索引（用于按点赞数排序）
CREATE INDEX IF NOT EXISTS idx_article_like_num ON article(likeNum);

-- 为type字段添加索引（用于类型筛选）
CREATE INDEX IF NOT EXISTS idx_article_type ON article(type);

-- 为content字段添加前缀索引（用于内容搜索）
CREATE INDEX IF NOT EXISTS idx_article_content ON article(content(255));

-- ===== 评论表索引 =====

-- 为created_at字段添加索引（用于时间排序和筛选）
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at);

-- 为like_counts字段添加索引（用于按点赞数排序）
CREATE INDEX IF NOT EXISTS idx_comments_like_counts ON comments(like_counts);

-- 为articleId字段添加索引（用于关联查询）
CREATE INDEX IF NOT EXISTS idx_comments_article_id ON comments(articleId);

-- 为content字段添加前缀索引（用于内容搜索）
CREATE INDEX IF NOT EXISTS idx_comments_content ON comments(content(255));

-- 为authorName字段添加索引（用于作者查询）
CREATE INDEX IF NOT EXISTS idx_comments_author_name ON comments(authorName);

-- ===== 用户表索引 =====

-- 为username字段添加唯一索引（用于登录查询）
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_username ON user(username);

-- ===== 复合索引 =====

-- 文章表复合索引：类型+创建时间
CREATE INDEX IF NOT EXISTS idx_article_type_created ON article(type, created_at);

-- 评论表复合索引：文章ID+创建时间
CREATE INDEX IF NOT EXISTS idx_comments_article_created ON comments(articleId, created_at);

-- ===== 查看索引 =====

-- 查看所有索引
SHOW INDEX FROM article;
SHOW INDEX FROM comments;
SHOW INDEX FROM user;

-- ===== 性能分析 =====

-- 分析表以更新统计信息
ANALYZE TABLE article;
ANALYZE TABLE comments;
ANALYZE TABLE user;

-- 查看表大小和索引使用情况
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS total_size_mb,
    ROUND((index_length / 1024 / 1024), 2) AS index_size_mb
FROM information_schema.tables
WHERE table_schema = 'wb'
ORDER BY (data_length + index_length) DESC;
