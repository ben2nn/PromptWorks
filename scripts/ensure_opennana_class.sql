-- 确保 opennana 分类存在
-- 如果不存在则创建，如果存在则不做任何操作

INSERT INTO prompts_class (id, name, description, created_at, updated_at)
VALUES (
    4, 
    'opennana', 
    'OpenNana 提示词库 - 来自 opennana.com 的精选 AI 提示词',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- 验证分类是否存在
SELECT id, name, description, created_at 
FROM prompts_class 
WHERE id = 4;
