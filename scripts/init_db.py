"""
数据库初始化脚本
用于初始化关系型数据库和向量数据库
"""

import os
import sys
import json
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import init_db, get_engine
from rag.vector_store import TCMVectorStore


def init_relational_db():
    """初始化关系型数据库"""
    print("Initializing relational database...")
    
    # 使用SQLite作为默认数据库
    database_url = "sqlite:///./data/tcm_chatbot.db"
    engine = get_engine(database_url, echo=False)
    
    # 创建表
    init_db(engine)
    
    print("Relational database initialized successfully!")
    print(f"Database file: ./data/tcm_chatbot.db")
    
    return engine


def init_vector_db():
    """初始化向量数据库"""
    print("Initializing vector database...")
    
    vector_store = TCMVectorStore(
        persist_directory="./data/vector_db",
        embedding_model="BAAI/bge-large-zh-v1.5"
    )
    
    stats = vector_store.get_collection_stats()
    print(f"Vector database initialized successfully!")
    print(f"Collection: {stats['collection_name']}")
    print(f"Total documents: {stats['total_documents']}")
    
    return vector_store


def load_sample_data(engine):
    """加载示例数据"""
    print("Loading sample data...")
    
    from sqlalchemy.orm import sessionmaker
    from db.models import Acupoint, Herb, ShangHanFormula, JinKuiFormula, Meridian
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 读取示例数据
    with open("./data/sample_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 插入经络数据
    meridians = {
        "足阳明胃经": 1,
        "手阳明大肠经": 2,
        "手厥阴心包经": 3
    }
    
    for name, mid in meridians.items():
        existing = session.query(Meridian).filter_by(name=name).first()
        if not existing:
            meridian = Meridian(id=mid, name=name)
            session.add(meridian)
    
    session.commit()
    
    # 插入穴位数据
    for item in data.get("acupoints", []):
        existing = session.query(Acupoint).filter_by(name=item["name"]).first()
        if not existing:
            acupoint = Acupoint(
                name=item["name"],
                code=item.get("code"),
                pinyin=item.get("pinyin"),
                meridian_id=meridians.get(item.get("meridian")),
                location_description=item.get("location_description"),
                main_indications=item.get("main_indications"),
                functions=item.get("functions"),
                acupuncture_method=item.get("acupuncture_method"),
                moxibustion=item.get("moxibustion"),
                source=item.get("source")
            )
            session.add(acupoint)
    
    # 插入中药数据
    for item in data.get("herbs", []):
        existing = session.query(Herb).filter_by(name=item["name"]).first()
        if not existing:
            herb = Herb(
                name=item["name"],
                pinyin=item.get("pinyin"),
                alias=json.dumps(item.get("alias", []), ensure_ascii=False),
                nature=item.get("nature"),
                flavor=item.get("flavor"),
                meridian_tropism=item.get("meridian_tropism"),
                functions=item.get("functions"),
                main_indications=item.get("main_indications"),
                usage_dosage=item.get("usage_dosage"),
                precautions=item.get("precautions"),
                source=item.get("source")
            )
            session.add(herb)
    
    # 插入伤寒论方剂
    for item in data.get("shanghan_formulas", []):
        existing = session.query(ShangHanFormula).filter_by(name=item["name"]).first()
        if not existing:
            formula = ShangHanFormula(
                name=item["name"],
                number=item.get("number"),
                composition=item.get("composition"),
                composition_json=item.get("composition_json"),
                preparation=item.get("preparation"),
                functions=item.get("functions"),
                main_indications=item.get("main_indications"),
                symptoms_detail=item.get("symptoms_detail"),
                pathogenesis=item.get("pathogenesis"),
                formula_analysis=item.get("formula_analysis"),
                key_points=item.get("key_points"),
                source_chapter=item.get("source_chapter")
            )
            session.add(formula)
    
    # 插入金匮要略方剂
    for item in data.get("jinkui_formulas", []):
        existing = session.query(JinKuiFormula).filter_by(name=item["name"]).first()
        if not existing:
            formula = JinKuiFormula(
                name=item["name"],
                number=item.get("number"),
                chapter=item.get("chapter"),
                disease_category=item.get("disease_category"),
                composition=item.get("composition"),
                composition_json=item.get("composition_json"),
                preparation=item.get("preparation"),
                functions=item.get("functions"),
                main_indications=item.get("main_indications"),
                symptoms_detail=item.get("symptoms_detail"),
                original_text=item.get("original_text")
            )
            session.add(formula)
    
    session.commit()
    session.close()
    
    print("Sample data loaded successfully!")


def main():
    """主函数"""
    print("=" * 50)
    print("TCM Chatbot Database Initialization")
    print("=" * 50)
    print()
    
    # 初始化关系型数据库
    engine = init_relational_db()
    
    # 加载示例数据
    try:
        load_sample_data(engine)
    except Exception as e:
        print(f"Warning: Failed to load sample data: {e}")
    
    print()
    
    # 初始化向量数据库
    try:
        init_vector_db()
    except Exception as e:
        print(f"Warning: Failed to initialize vector database: {e}")
        print("This is normal if you haven't installed sentence-transformers yet.")
    
    print()
    print("=" * 50)
    print("Initialization completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
