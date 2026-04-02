-- 图审云平台 MySQL 初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS tushen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tushen;

-- 用户已通过环境变量创建：tushen / tushen_pass_2026
-- 如果需要额外用户，在这里添加
