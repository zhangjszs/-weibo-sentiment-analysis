-- ===========================================
-- 用户数据初始化脚本
-- 注意：此脚本应与 new.sql 中的表结构保持一致
-- ===========================================

-- 添加普通用户
INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email) 
VALUES (6, 'kerwin zhang', '123', '2025-04-26', 0, 'Kerwin', 'kerwin@example.com');

-- 新增用户
INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email) 
VALUES (7, 'Alex', '123456', NOW(), 0, 'Alex User', 'alex@example.com');

INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email) 
VALUES (8, 'Sarah', '123456', NOW(), 0, 'Sarah User', 'sarah@example.com');

-- 新增管理员
INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email) 
VALUES (9, 'Admin', '123456', NOW(), 1, '系统管理员', 'admin@example.com');

-- 注意：生产环境应使用密码哈希值，而非明文密码！
-- 示例哈希值（bcrypt）:
-- INSERT INTO wb.user (id, username, password, createTime, is_admin) 
-- VALUES (9, 'Admin', '$2b$12$...', NOW(), 1);
