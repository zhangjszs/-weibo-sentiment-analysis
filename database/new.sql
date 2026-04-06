-- --------------------------------------------------------
-- 主机:                           127.0.0.1
-- 服务器版本:                        5.7.40 - MySQL Community Server (GPL)
-- 服务器操作系统:                      Win64
-- HeidiSQL 版本:                  12.3.0.6589
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */; -- 默认连接使用 utf8mb4
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- 导出 wb 的数据库结构, 设置默认字符集为 utf8mb4
CREATE DATABASE IF NOT EXISTS `wb` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `wb`;

-- 导出 表 wb.article 结构
-- 删掉旧表（如果存在），确保使用新结构创建
DROP TABLE IF EXISTS `article`;
CREATE TABLE `article` (
                           `id` bigint(20) NOT NULL, -- 假设 ID 是主键且不为空
                           `likeNum` bigint(20) DEFAULT NULL,
                           `commentsLen` bigint(20) DEFAULT NULL,
                           `reposts_count` bigint(20) DEFAULT NULL,
                           `region` text COLLATE utf8mb4_unicode_ci,
                           `content` mediumtext COLLATE utf8mb4_unicode_ci, -- 修改为 MEDIUMTEXT 以支持更长内容
                           `contentLen` bigint(20) DEFAULT NULL,
                           `created_at` date DEFAULT NULL, -- 修改为 DATE 类型
                           `type` text COLLATE utf8mb4_unicode_ci,
                           `detailUrl` text COLLATE utf8mb4_unicode_ci,
                           `authorAvatar` text COLLATE utf8mb4_unicode_ci,
                           `authorName` text COLLATE utf8mb4_unicode_ci,
                           `authorDetail` text COLLATE utf8mb4_unicode_ci,
                           `isVip` tinyint(1) DEFAULT 0, -- 修改为 TINYINT(1) 并设置默认值
                           PRIMARY KEY (`id`), -- 添加主键 (假设 id 是唯一的)
                           INDEX `idx_created_at` (`created_at`) -- 为日期添加索引，便于按时间查询
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 导出 表 wb.comments 结构
-- 删掉旧表（如果存在），确保使用新结构创建
DROP TABLE IF EXISTS `comments`;
CREATE TABLE `comments` (
                            `comment_id` int(11) NOT NULL AUTO_INCREMENT, -- 添加自增主键
                            `articleId` bigint(20) DEFAULT NULL,
                            `created_at` date DEFAULT NULL, -- 修改为 DATE 类型
                            `like_counts` bigint(20) DEFAULT NULL,
                            `region` text COLLATE utf8mb4_unicode_ci,
                            `content` mediumtext COLLATE utf8mb4_unicode_ci, -- 修改为 MEDIUMTEXT
                            `authorName` text COLLATE utf8mb4_unicode_ci,
                            `authorGender` varchar(1) COLLATE utf8mb4_unicode_ci DEFAULT NULL, -- 修改为 VARCHAR(1)
                            `authorAddress` text COLLATE utf8mb4_unicode_ci,
                            `authorAvatar` text COLLATE utf8mb4_unicode_ci,
                            PRIMARY KEY (`comment_id`), -- 设置主键
                            INDEX `idx_articleId` (`articleId`) -- 为 articleId 添加索引，加速评论查找
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 导出 表 wb.user 结构
-- 删掉旧表（如果存在），确保使用新结构创建
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
                        `id` int(11) NOT NULL AUTO_INCREMENT,
                        `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    -- 严重警告: 密码绝不应明文存储！应用程序应存储密码的哈希值。
                        `password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                        `createTime` date DEFAULT NULL, -- 修改为 DATE 类型
                        `is_admin` tinyint(1) DEFAULT 0 COMMENT '是否为管理员: 0-否, 1-是',
                        `nickname` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户昵称',
                        `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
                        `bio` text COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '个人简介',
                        `avatar_color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#3B82F6' COMMENT '头像颜色',
                        PRIMARY KEY (`id`),
                        UNIQUE KEY `idx_username` (`username`),
                        KEY `idx_is_admin` (`is_admin`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- 修改表字符集为 utf8mb4

-- 重新插入 user 数据 (注意 createTime 格式现在是 YYYY-MM-DD)
INSERT INTO `user` (`id`, `username`, `password`, `createTime`, `is_admin`, `nickname`, `email`) VALUES
                                                                    (2, 'Edward', '123123', '2023-03-06', 0, 'Edward', 'edward@example.com'),
                                                                    (3, 'EdwardD', '123123', '2023-08-08', 0, 'EdwardD', 'edwardd@example.com'),
                                                                    (4, '19123', '19123', '2024-03-18', 0, '19123', '19123@example.com'),
                                                                    (5, 'qwd', '123', '2024-03-18', 0, 'qwd', 'qwd@example.com');

-- --------------------------------------------------------
-- 导出 表 wb.reposts 结构 (用于传播分析)
-- --------------------------------------------------------
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

-- --------------------------------------------------------
-- 导出 表 wb.audit_log 结构 (审计日志)
-- --------------------------------------------------------
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

-- --------------------------------------------------------
-- 导出 表 wb.user_favorites 结构 (用户收藏)
-- --------------------------------------------------------
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

-- --------------------------------------------------------
-- 插入演示用的转发数据 (用于传播分析测试)
-- --------------------------------------------------------
INSERT INTO `reposts` (`article_id`, `user_id`, `user_name`, `content`, `repost_count`, `comment_count`, `like_count`, `depth`, `parent_id`, `created_at`) VALUES
(1, 'user_001', '科技观察家', '这条微博说得很有道理，值得关注！', 50, 20, 150, 0, NULL, NOW() - INTERVAL 24 HOUR),
(1, 'user_002', '互联网分析师', '转发微博，进行了深入分析', 30, 15, 80, 1, 1, NOW() - INTERVAL 23 HOUR),
(1, 'user_003', '微博大V', '同意楼上的观点', 20, 10, 60, 2, 2, NOW() - INTERVAL 22 HOUR),
(1, 'user_004', '普通用户A', 'mark一下', 5, 2, 10, 1, 1, NOW() - INTERVAL 21 HOUR),
(1, 'user_005', '普通用户B', '学习了', 3, 1, 5, 2, 2, NOW() - INTERVAL 20 HOUR),
(1, 'user_006', '媒体账号', '对此事进行跟踪报道', 100, 50, 300, 0, NULL, NOW() - INTERVAL 18 HOUR),
(1, 'user_007', '行业专家', '从专业角度分析', 40, 25, 120, 1, 6, NOW() - INTERVAL 17 HOUR),
(1, 'user_008', '热心网友', '转发支持', 2, 0, 8, 1, 6, NOW() - INTERVAL 16 HOUR),
(1, 'user_009', '资讯博主', '最新进展更新', 60, 30, 200, 2, 7, NOW() - INTERVAL 15 HOUR),
(1, 'user_010', '路人甲', '围观中', 1, 0, 3, 3, 9, NOW() - INTERVAL 14 HOUR);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;