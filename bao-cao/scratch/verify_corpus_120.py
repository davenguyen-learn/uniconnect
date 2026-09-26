import asyncio
import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def verify():
    eng = create_async_engine(settings.DATABASE_URL)
    async with eng.connect() as conn:
        print("=" * 70)
        print("📊 KIỂM TRA ĐỘC LẬP DỮ LIỆU CORPUS 120 HOẠT ĐỘNG TRONG POSTGRESQL")
        print("=" * 70)
        
        # 1. Total records
        total = (await conn.execute(text('SELECT COUNT(*) FROM activities'))).scalar()
        print(f"1. Tổng số hoạt động (Total Activities): {total}")
        
        # 2. Embeddings count & dimensionality
        emb_count = (await conn.execute(text('SELECT COUNT(*) FROM activities WHERE embedding IS NOT NULL'))).scalar()
        sample_dim = (await conn.execute(text('SELECT vector_dims(embedding) FROM activities LIMIT 1'))).scalar()
        print(f"2. Số vector embeddings 768 chiều: {emb_count}/{total} (Độ dài vector: {sample_dim})")
        
        # 3. Domain distribution
        print("\n3. Phân bố theo 7 Miền nghiệp vụ (Domain Distribution):")
        res = await conn.execute(text('SELECT category, COUNT(*) as c FROM activities GROUP BY category ORDER BY c DESC'))
        for row in res.fetchall():
            print(f"   • {row[0]}: {row[1]} hoạt động")
            
        # 4. Multi-constraint distribution
        print("\n4. Phân bổ các trường Ràng buộc Đa chiều (Multi-Constraints):")
        ctxh_gt0 = (await conn.execute(text('SELECT COUNT(*) FROM activities WHERE social_work_days > 0'))).scalar()
        ctxh_eq0 = (await conn.execute(text('SELECT COUNT(*) FROM activities WHERE social_work_days = 0 OR social_work_days IS NULL'))).scalar()
        print(f"   • Hoạt động CÓ tính ngày CTXH (>0d): {ctxh_gt0} hoạt động (0.5d - 2.0d)")
        print(f"   • Hoạt động KHÔNG tính ngày CTXH (=0d): {ctxh_eq0} hoạt động")
        
        cs1_cnt = (await conn.execute(text("SELECT COUNT(*) FROM activities WHERE meeting_location LIKE '%CS1%' OR meeting_location LIKE '%Lý Thường Kiệt%' OR meeting_location LIKE '%497%' OR meeting_location LIKE '%B4%' OR meeting_location LIKE '%A5%' OR meeting_location LIKE '%C1%' OR meeting_location LIKE '%C3%' OR meeting_location LIKE '%C5%' OR meeting_location LIKE '%B1%'"))).scalar()
        cs2_cnt = (await conn.execute(text("SELECT COUNT(*) FROM activities WHERE meeting_location LIKE '%CS2%' OR meeting_location LIKE '%Dĩ An%' OR meeting_location LIKE '%H6%' OR meeting_location LIKE '%H1%' OR meeting_location LIKE '%H3%' OR meeting_location LIKE '%Hồ Tiền Phong%' OR meeting_location LIKE '%Khu B%' OR meeting_location LIKE '%Khu A%'"))).scalar()
        print(f"   • Địa điểm tại Cơ sở 1 (Lý Thường Kiệt, Q.10): {cs1_cnt} hoạt động")
        print(f"   • Địa điểm tại Cơ sở 2 (Dĩ An, Bình Dương): {cs2_cnt} hoạt động")
        
        # 5. Semantic neighbor pairs verification
        print("\n5. Kiểm chứng Cụm Ngữ nghĩa Gần (Semantic Neighbors & Distractors):")
        semantic_checks = [
            ("Cụm AI / Machine Learning / Vision", ["Machine Learning", "Deep Learning", "Computer Vision", "Generative AI", "Data Science"]),
            ("Cụm Hạ tầng / Cloud / Container", ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux"]),
            ("Cụm Toán học & Khoa học Đại cương", ["Giải tích 1", "Giải tích 2", "Đại số tuyến tính", "Xác suất"]),
            ("Cụm Thể thao Bóng đá & Sân bãi", ["Sân 7", "Sân 5", "Cúp Khoa", "Futsal"]),
            ("Cụm Kỹ năng mềm & Hội nhập", ["Thuyết trình", "Quản lý thời gian", "Tân Sinh viên", "Đàm phán"]),
        ]
        for cluster_name, keywords in semantic_checks:
            print(f"   [{cluster_name}]:")
            for kw in keywords:
                cnt = (await conn.execute(text(f"SELECT COUNT(*) FROM activities WHERE title ILIKE '%{kw}%' OR description ILIKE '%{kw}%'"))).scalar()
                print(f"     - Hoạt động chứa \"{kw}\": {cnt} activities")

    await eng.dispose()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(verify())
