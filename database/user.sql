-- ===========================================
-- 用户数据初始化脚本
-- 注意：此脚本应与 new.sql 中的表结构保持一致
-- 密码已使用 bcrypt 哈希（rounds=12），原始明文仅供开发演示：
--   kerwin zhang / 123, Alex / 123456, Sarah / 123456, Admin / 123456
-- ===========================================

-- 添加普通用户
INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email)
VALUES (6, 'kerwin zhang', '$2b$12$gaW6YWbWVBSgc1m9cH/4OuWHVekDHl733nqhQtqaMYEnCBeV6HGQm', '2025-04-26', 0, 'Kerwin', 'kerwin@example.com');

-- 新增用户
INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email)
VALUES (7, 'Alex', '$2b$12$jUS./uWfpcNjrqQHNkoKIO/4kFAL5dVOl/abobS6u4MB3i8LoR1/W', NOW(), 0, 'Alex User', 'alex@example.com');

INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email)
VALUES (8, 'Sarah', '$2b$12$jUS./uWfpcNjrqQHNkoKIO/4kFAL5dVOl/abobS6u4MB3i8LoR1/W', NOW(), 0, 'Sarah User', 'sarah@example.com');

-- 新增管理员
INSERT INTO wb.user (id, username, password, createTime, is_admin, nickname, email)
VALUES (9, 'Admin', '$2b$12$jUS./uWfpcNjrqQHNkoKIO/4kFAL5dVOl/abobS6u4MB3i8LoR1/W', NOW(), 1, '系统管理员', 'admin@example.com');
