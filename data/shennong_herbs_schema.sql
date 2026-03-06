-- 神农本草经药物表
CREATE TABLE shennong_herbs (
    id SERIAL PRIMARY KEY,
    drug_name VARCHAR(100) NOT NULL,           -- 药物名称
    original_text TEXT,                         -- 本经原文
    origin TEXT,                                -- 产地
    indications TEXT,                           -- 主治
    properties TEXT,                            -- 性味
    dosage TEXT,                                -- 用量
    contraindications TEXT,                     -- 禁忌
    other1 TEXT,                -- 其他1内容
    other1_name VARCHAR(50),    -- 其他1名称
    other2 TEXT,                -- 其他2内容
    other2_name VARCHAR(50),    -- 其他2名称
    other3 TEXT,                -- 其他3内容
    other3_name VARCHAR(50),    -- 其他3名称
    other4 TEXT,                -- 其他4内容
    other4_name VARCHAR(50),    -- 其他4名称
    other5 TEXT,                -- 其他5内容
    other5_name VARCHAR(50),    -- 其他5名称
    other6 TEXT,                -- 其他6内容
    other6_name VARCHAR(50),    -- 其他6名称
    other7 TEXT,                -- 其他7内容
    other7_name VARCHAR(50),    -- 其他7名称
    other8 TEXT,                -- 其他8内容
    other8_name VARCHAR(50),    -- 其他8名称
    other9 TEXT,                -- 其他9内容
    other9_name VARCHAR(50),    -- 其他9名称
    other10 TEXT,                -- 其他10内容
    other10_name VARCHAR(50),    -- 其他10名称
    other11 TEXT,                -- 其他11内容
    other11_name VARCHAR(50),    -- 其他11名称
    source_file VARCHAR(100),                   -- 源文件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_herbs_name ON shennong_herbs(drug_name);

-- 注释
COMMENT ON TABLE shennong_herbs IS '神农本草经上经药物数据';
