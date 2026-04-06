-- ===========================================
-- 微博舆情分析系统 - 完整数据库初始化脚本
-- ===========================================
-- 此脚本包含所有表结构和初始数据
-- 执行方式: mysql -u root -p < init_database.sql
-- ===========================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库
DROP DATABASE IF EXISTS `wb`;
CREATE DATABASE `wb` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `wb`;

-- ===========================================
-- 1. 用户表 (user)
-- ===========================================
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生产环境应使用哈希值',
    `createTime` date DEFAULT NULL,
    `is_admin` tinyint(1) DEFAULT 0 COMMENT '是否为管理员: 0-否, 1-是',
    `nickname` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户昵称',
    `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
    `bio` text COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '个人简介',
    `avatar_color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#3B82F6' COMMENT '头像颜色',
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_username` (`username`),
    KEY `idx_is_admin` (`is_admin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ===========================================
-- 2. 文章表 (article)
-- ===========================================
DROP TABLE IF EXISTS `article`;
CREATE TABLE `article` (
    `id` bigint(20) NOT NULL,
    `likeNum` bigint(20) DEFAULT NULL COMMENT '点赞数',
    `commentsLen` bigint(20) DEFAULT NULL COMMENT '评论数',
    `reposts_count` bigint(20) DEFAULT NULL COMMENT '转发数',
    `region` text COLLATE utf8mb4_unicode_ci COMMENT '地区',
    `content` mediumtext COLLATE utf8mb4_unicode_ci COMMENT '内容',
    `contentLen` bigint(20) DEFAULT NULL COMMENT '内容长度',
    `created_at` date DEFAULT NULL COMMENT '创建日期',
    `type` text COLLATE utf8mb4_unicode_ci COMMENT '类型',
    `detailUrl` text COLLATE utf8mb4_unicode_ci COMMENT '详情链接',
    `authorAvatar` text COLLATE utf8mb4_unicode_ci COMMENT '作者头像',
    `authorName` text COLLATE utf8mb4_unicode_ci COMMENT '作者名称',
    `authorDetail` text COLLATE utf8mb4_unicode_ci COMMENT '作者详情',
    `isVip` tinyint(1) DEFAULT 0 COMMENT '是否VIP',
    PRIMARY KEY (`id`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_like_num` (`likeNum`),
    INDEX `idx_type` (`type`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章表';

-- ===========================================
-- 3. 评论表 (comments)
-- ===========================================
DROP TABLE IF EXISTS `comments`;
CREATE TABLE `comments` (
    `comment_id` int(11) NOT NULL AUTO_INCREMENT,
    `articleId` bigint(20) DEFAULT NULL COMMENT '文章ID',
    `created_at` date DEFAULT NULL COMMENT '创建日期',
    `like_counts` bigint(20) DEFAULT NULL COMMENT '点赞数',
    `region` text COLLATE utf8mb4_unicode_ci COMMENT '地区',
    `content` mediumtext COLLATE utf8mb4_unicode_ci COMMENT '内容',
    `authorName` text COLLATE utf8mb4_unicode_ci COMMENT '作者名称',
    `authorGender` varchar(1) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '性别',
    `authorAddress` text COLLATE utf8mb4_unicode_ci COMMENT '地址',
    `authorAvatar` text COLLATE utf8mb4_unicode_ci COMMENT '头像',
    PRIMARY KEY (`comment_id`),
    INDEX `idx_articleId` (`articleId`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_authorName` (`authorName`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- ===========================================
-- 4. 转发传播表 (reposts)
-- ===========================================
DROP TABLE IF EXISTS `reposts`;
CREATE TABLE `reposts` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `article_id` bigint(20) NOT NULL COMMENT '原文ID',
    `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '转发用户ID',
    `user_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '转发用户名',
    `content` text COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '转发内容',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '转发时间',
    `repost_count` int(11) DEFAULT 0 COMMENT '转发数',
    `comment_count` int(11) DEFAULT 0 COMMENT '评论数',
    `like_count` int(11) DEFAULT 0 COMMENT '点赞数',
    `depth` int(11) DEFAULT 0 COMMENT '传播深度',
    `parent_id` bigint(20) DEFAULT NULL COMMENT '父转发ID',
    PRIMARY KEY (`id`),
    KEY `idx_article_id` (`article_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='转发传播表';

-- ===========================================
-- 5. 用户收藏表 (user_favorites)
-- ===========================================
DROP TABLE IF EXISTS `user_favorites`;
CREATE TABLE `user_favorites` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `user_id` int(11) NOT NULL COMMENT '用户ID',
    `article_id` bigint(20) NOT NULL COMMENT '文章ID',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_user_article` (`user_id`, `article_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_article_id` (`article_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏表';

-- ===========================================
-- 6. 审计日志表 (audit_log)
-- ===========================================
DROP TABLE IF EXISTS `audit_log`;
CREATE TABLE `audit_log` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `user_id` int(11) DEFAULT NULL COMMENT '操作用户ID',
    `action` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型',
    `detail` text COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作详情',
    `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
    `user_agent` text COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_action` (`action`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';

-- ===========================================
-- 插入初始数据
-- ===========================================

-- 初始用户数据
INSERT INTO `user` (`id`, `username`, `password`, `createTime`, `is_admin`, `nickname`, `email`) VALUES
(1, 'admin', '123456', CURDATE(), 1, '系统管理员', 'admin@example.com'),
(2, 'Edward', '123123', '2023-03-06', 0, 'Edward', 'edward@example.com'),
(3, 'EdwardD', '123123', '2023-08-08', 0, 'EdwardD', 'edwardd@example.com'),
(4, 'test_user', '123456', CURDATE(), 0, '测试用户', 'test@example.com');

SET FOREIGN_KEY_CHECKS = 1;

-- 初始化完成
SELECT '数据库初始化完成!' AS message;
SELECT CONCAT('用户表记录数: ', (SELECT COUNT(*) FROM user)) AS info;
