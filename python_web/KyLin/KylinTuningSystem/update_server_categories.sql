-- 为现有的服务器信息添加服务类型
-- 这个脚本用于更新已存在的服务器记录，为它们添加合适的服务类型

-- 首先添加server_category字段（如果还没有的话）
ALTER TABLE serveInfo ADD COLUMN server_category VARCHAR(32) DEFAULT '' COMMENT '服务类型';

-- 根据端口号和IP地址推断服务类型并更新现有数据
-- 更新端口7788的记录为监控代理
UPDATE serveInfo SET server_category = '监控代理' 
WHERE port = 7788 AND server_category = '';

-- 更新端口22的记录为SSH服务
UPDATE serveInfo SET server_category = 'SSH' 
WHERE port = 22 AND server_category = '';

-- 更新端口222的记录为SSH服务（非标准SSH端口）
UPDATE serveInfo SET server_category = 'SSH' 
WHERE port = 222 AND server_category = '';

-- 更新端口80的记录为Nginx
UPDATE serveInfo SET server_category = 'Nginx' 
WHERE port = 80 AND server_category = '';

-- 更新端口8080的记录为Tomcat
UPDATE serveInfo SET server_category = 'Tomcat' 
WHERE port = 8080 AND server_category = '';

-- 更新端口3306的记录为MySQL
UPDATE serveInfo SET server_category = 'MySQL' 
WHERE port = 3306 AND server_category = '';

-- 更新端口6379的记录为Redis
UPDATE serveInfo SET server_category = 'Redis' 
WHERE port = 6379 AND server_category = '';

-- 更新端口5432的记录为PostgreSQL
UPDATE serveInfo SET server_category = 'PostgreSQL' 
WHERE port = 5432 AND server_category = '';

-- 更新端口9200的记录为Elasticsearch
UPDATE serveInfo SET server_category = 'Elasticsearch' 
WHERE port = 9200 AND server_category = '';

-- 更新端口5672的记录为RabbitMQ
UPDATE serveInfo SET server_category = 'RabbitMQ' 
WHERE port = 5672 AND server_category = '';

-- 更新端口9092的记录为Kafka
UPDATE serveInfo SET server_category = 'Kafka' 
WHERE port = 9092 AND server_category = '';

-- 如果有其他常见端口，也可以添加相应的更新语句
-- 更新端口443的记录为HTTPS
UPDATE serveInfo SET server_category = 'Nginx' 
WHERE port = 443 AND server_category = '';

-- 更新端口21的记录为FTP
UPDATE serveInfo SET server_category = 'FTP' 
WHERE port = 21 AND server_category = '';

-- 更新端口23的记录为Telnet
UPDATE serveInfo SET server_category = 'Telnet' 
WHERE port = 23 AND server_category = '';

-- 更新端口53的记录为DNS
UPDATE serveInfo SET server_category = 'DNS' 
WHERE port = 53 AND server_category = '';

-- 查看更新结果
SELECT ip, port, server_category, remarks FROM serveInfo ORDER BY ip, port;
