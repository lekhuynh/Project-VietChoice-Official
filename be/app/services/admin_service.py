# app/services/admin_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, distinct, desc, and_, or_
from sqlalchemy.orm import Session

from ..models.users import Users
from ..models.products import Products
from ..models.search_history import Search_History
from ..models.user_reviews import User_Reviews
from ..models.favorites import Favorites
from ..models.product_view import Product_Views
from ..models.categories import Categories

def _safe_scalar(value):
    if value is None:
        return 0
    try:
        return int(value)
    except Exception:
        try:
            return float(value)
        except Exception:
            return 0

def _safe_float(value, default: float = 0.0, ndigits: Optional[int] = None):
    if value is None:
        return default
    try:
        v = float(value)
        return round(v, ndigits) if ndigits is not None else v
    except Exception:
        return default

def get_dashboard_stats(db: Session) -> Dict:
    """Dashboard stats - chính function bạn đã có"""
    try:
        total_products = _safe_scalar(db.query(func.count(Products.Product_ID)).scalar())
        total_users = _safe_scalar(db.query(func.count(Users.User_ID)).scalar())
        
        # Đếm số brand distinct từ bảng Products thay vì từ Brands
        total_brands = _safe_scalar(
            db.query(func.count(distinct(Products.Brand))).filter(Products.Brand.isnot(None)).scalar()
        )

        # Today's products using datetime range
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_products = _safe_scalar(
            db.query(func.count(Products.Product_ID)).filter(
                Products.Created_At >= today_start,
                Products.Created_At < today_end
            ).scalar()
        )

        # Active users (last 30 days)
        since_30d = datetime.utcnow() - timedelta(days=30)
        active_users = _safe_scalar(
            db.query(func.count(distinct(Search_History.User_ID)))
            .filter(Search_History.Created_At >= since_30d)
            .scalar()
        )

        # Pending reviews - count products without sentiment
        pending_reviews = _safe_scalar(
            db.query(func.count(Products.Product_ID))
            .filter(
                Products.Sentiment_Score.is_(None),
                Products.Sentiment_Label.is_(None)
            )
            .scalar()
        )

        # Average positive percentage
        avg_positive = db.query(func.avg(Products.Positive_Percent)).filter(
            Products.Positive_Percent.isnot(None)
        ).scalar()
        positive_ratio = _safe_float(avg_positive, default=0.0, ndigits=1)

        result = {
            "totalProducts": int(total_products),
            "totalUsers": int(total_users),
            "totalBrands": int(total_brands),
            "positiveRatio": positive_ratio,
            "todayProducts": int(today_products),
            "activeUsers": int(active_users),
            "pendingReviews": int(pending_reviews),
        }
        print(f"Dashboard stats calculated: {result}")
        return result
    except Exception as e:
        import traceback
        error_msg = f"Error in get_dashboard_stats: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return {
            "totalProducts": 0,
            "totalUsers": 0,
            "totalBrands": 0,
            "positiveRatio": 0.0,
            "todayProducts": 0,
            "activeUsers": 0,
            "pendingReviews": 0,
        }

def get_sentiment_chart_data(db: Session) -> List[Dict]:
    """Sentiment chart data by category - sử dụng Positive_Percent từ Products"""
    try:
        results = (
            db.query(
                Categories.Category_Lv1,
                func.avg(Products.Positive_Percent).label("positive"),
                func.count(Products.Product_ID).label("total")
            )
            .outerjoin(Products, Products.Category_ID == Categories.Category_ID)
            .filter(Products.Positive_Percent.isnot(None))
            .group_by(Categories.Category_Lv1)
            .order_by(desc(func.count(Products.Product_ID)))
            .limit(10)
            .all()
        )

        chart_data = []
        for cat, pos, total in results:
            if not cat:
                continue
            positive = _safe_float(pos, 0.0, ndigits=1)
            # Tính neutral và negative dựa trên phần còn lại
            rem = max(0.0, 100.0 - positive)
            neutral = round(rem * 0.3, 1)  # 30% của phần còn lại là neutral
            negative = round(rem * 0.7, 1)  # 70% của phần còn lại là negative
            
            chart_data.append({
                "name": cat,
                "positive": positive,
                "neutral": neutral,
                "negative": negative
            })
        
        return chart_data
    except Exception as e:
        print(f"Error in get_sentiment_chart_data: {e}")
        return []

def get_trend_data(db: Session, months: int = 6) -> List[Dict]:
    """Trend data với categories động từ database"""
    try:
        print("=== GETTING TREND DATA ===")
        now = datetime.utcnow()
        
        # Lấy top 3 categories có nhiều products nhất
        top_categories = db.query(
            Categories.Category_Lv1,
            func.count(Products.Product_ID).label('product_count')
        ).join(Products)\
         .group_by(Categories.Category_Lv1)\
         .order_by(func.count(Products.Product_ID).desc())\
         .limit(3)\
         .all()
        
        # Lấy tên categories
        category_names = [cat for cat, count in top_categories if cat]
        print(f"Top categories: {category_names}")
        
        # Nếu không có đủ categories, lấy tất cả categories có data
        if len(category_names) < 3:
            all_categories = db.query(Categories.Category_Lv1).distinct().all()
            category_names = [cat[0] for cat in all_categories if cat[0]]
            category_names = category_names[:3]  # Lấy tối đa 3 categories
        
        results = []
        
        for i in range(months - 1, -1, -1):
            # Calculate month start and end
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            for _ in range(i):
                if month_start.month == 1:
                    month_start = month_start.replace(year=month_start.year - 1, month=12)
                else:
                    month_start = month_start.replace(month=month_start.month - 1)
            
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            
            month_data = {"month": f"T{month_start.month}"}
            
            # Lấy data cho từng category
            for category_name in category_names:
                avg_pos = db.query(func.avg(Products.Positive_Percent)).join(Categories).filter(
                    Categories.Category_Lv1 == category_name,
                    Products.Created_At >= month_start,
                    Products.Created_At < month_end,
                    Products.Positive_Percent.isnot(None)
                ).scalar()
                
                avg_pos_val = _safe_float(avg_pos, 0.0, ndigits=1)
                
                # Tạo key an toàn từ category name
                safe_key = _make_safe_key(category_name)
                month_data[safe_key] = avg_pos_val
            
            results.append(month_data)
        
        print(f"Final trend data: {results}")
        return results
        
    except Exception as e:
        print(f"Error in get_trend_data: {e}")
        import traceback
        traceback.print_exc()
        return []

def _make_safe_key(category_name: str) -> str:
    """Chuyển category name thành key an toàn cho JSON"""
    if not category_name:
        return "unknown"
    
    # Chuyển thành lowercase, thay thế khoảng trắng và ký tự đặc biệt
    safe_key = category_name.lower().strip()
    safe_key = safe_key.replace(' ', '_')
    safe_key = safe_key.replace('-', '_')
    safe_key = safe_key.replace('&', 'and')
    safe_key = safe_key.replace('/', '_')
    safe_key = safe_key.replace('\\', '_')
    safe_key = ''.join(c for c in safe_key if c.isalnum() or c == '_')
    
    # Đảm bảo không rỗng
    if not safe_key:
        return "unknown"
    
    return safe_key

def get_featured_products(db: Session, limit: int = 3) -> List[Dict]:
    """Featured products - sử dụng logic từ function của bạn"""
    try:
        products = (
            db.query(Products)
            .filter(
                Products.Is_Active == True,
                Products.Avg_Rating.isnot(None),
                Products.Positive_Percent.isnot(None)
            )
            .order_by(desc(Products.Avg_Rating), desc(Products.Positive_Percent))
            .limit(max(1, limit))
            .all()
        )

        featured = []
        for p in products:
            views = _safe_scalar(
                db.query(func.count(Product_Views.Product_ID)).filter(Product_Views.Product_ID == p.Product_ID).scalar()
            )
            featured.append({
                "Product_ID": p.Product_ID,
                "Product_Name": p.Product_Name,
                "Brand": p.Brand,
                "Avg_Rating": _safe_float(p.Avg_Rating, 0.0, ndigits=2),
                "Positive_Percent": _safe_float(p.Positive_Percent, 0.0, ndigits=1),
                "views": int(views)
            })
        return featured
    except Exception as e:
        print(f"Error in get_featured_products: {e}")
        return []

def get_products_needing_attention(db: Session, limit: int = 5) -> List[Dict]:
    """Products that need attention - low rating or missing sentiment"""
    try:
        # Sản phẩm có rating thấp hoặc chưa có sentiment
        products = (
            db.query(Products)
            .filter(
                Products.Is_Active == True,
                or_(
                    Products.Avg_Rating < 3.0,
                    Products.Sentiment_Label.is_(None),
                    Products.Positive_Percent < 70.0
                )
            )
            .order_by(Products.Avg_Rating.asc())
            .limit(max(1, limit))
            .all()
        )

        attention_products = []
        for p in products:
            issues = []
            if p.Avg_Rating and p.Avg_Rating < 3.0:
                issues.append(f"Rating thấp ({p.Avg_Rating}/5)")
            if p.Sentiment_Label is None:
                issues.append("Chưa phân tích sentiment")
            if p.Positive_Percent and p.Positive_Percent < 70.0:
                issues.append(f"Tỷ lệ tích cực thấp ({p.Positive_Percent}%)")
            
            attention_products.append({
                "Product_ID": p.Product_ID,
                "Product_Name": p.Product_Name,
                "Brand": p.Brand,
                "Avg_Rating": _safe_float(p.Avg_Rating, 0.0, ndigits=1),
                "Positive_Percent": _safe_float(p.Positive_Percent, 0.0, ndigits=1),
                "issues": ", ".join(issues) if issues else "Cần kiểm tra"
            })
        
        return attention_products
    except Exception as e:
        print(f"Error in get_products_needing_attention: {e}")
        return []

def get_admin_products(db: Session, search: Optional[str] = None) -> List[Dict]:
    """Get products for admin management"""
    try:
        query = db.query(Products)
        
        if search:
            query = query.filter(
                or_(
                    Products.Product_Name.ilike(f"%{search}%"),
                    Products.Brand.ilike(f"%{search}%")
                )
            )
        
        products = query.order_by(desc(Products.Created_At)).all()
        
        result = []
        for p in products:
            result.append({
                "Product_ID": p.Product_ID,
                "Product_Name": p.Product_Name,
                "Brand": p.Brand,
                "Category_ID": p.Category_ID,
                "Price": _safe_float(p.Price, None),
                "Avg_Rating": _safe_float(p.Avg_Rating, None, 1),
                "Review_Count": _safe_scalar(p.Review_Count),
                "Positive_Percent": _safe_float(p.Positive_Percent, None, 1),
                "Sentiment_Label": p.Sentiment_Label,
                "Is_Active": bool(p.Is_Active),
                "Created_At": p.Created_At.isoformat() if p.Created_At else None,
                "Updated_At": p.Updated_At.isoformat() if p.Updated_At else None,
                "Description": p.Description
            })
        
        return result
    except Exception as e:
        print(f"Error in get_admin_products: {e}")
        return []

def get_admin_users(db: Session, search: Optional[str] = None) -> List[Dict]:
    """Get users for admin management"""
    try:
        query = db.query(Users)
        
        if search:
            query = query.filter(
                or_(
                    Users.User_Name.ilike(f"%{search}%"),
                    Users.User_Email.ilike(f"%{search}%"),
                    Users.Role.ilike(f"%{search}%")
                )
            )
        
        users = query.order_by(desc(Users.Created_At)).all()
        
        result = []
        for u in users:
            # Tìm last active từ search history
            last_active = db.query(Search_History.Created_At).filter(
                Search_History.User_ID == u.User_ID
            ).order_by(desc(Search_History.Created_At)).first()
            
            result.append({
                "User_ID": u.User_ID,
                "User_Name": u.User_Name,
                "User_Email": u.User_Email,
                "Role": u.Role,
                "Created_At": u.Created_At.isoformat() if u.Created_At else None,
                "lastActive": last_active[0].isoformat() if last_active and last_active[0] else None
            })
        
        return result
    except Exception as e:
        print(f"Error in get_admin_users: {e}")
        return []

def get_activity_logs(db: Session, limit: int = 50) -> List[Dict]:
    """Get activity logs from various sources"""
    try:
        logs = []
        
        # Recent product creations
        recent_products = db.query(Products).order_by(desc(Products.Created_At)).limit(10).all()
        for p in recent_products:
            logs.append({
                "id": p.Product_ID,
                "user": "System",
                "action": "Tạo sản phẩm",
                "details": p.Product_Name,
                "timestamp": p.Created_At.isoformat() if p.Created_At else None,
                "type": "create"
            })
        
        # Recent reviews
        recent_reviews = db.query(User_Reviews).order_by(desc(User_Reviews.Created_At)).limit(10).all()
        for r in recent_reviews:
            logs.append({
                "id": r.Review_ID,
                "user": f"User_{r.User_ID}",
                "action": "Đánh giá sản phẩm",
                "details": f"Rating: {r.Rating}",
                "timestamp": r.Created_At.isoformat() if r.Created_At else None,
                "type": "create"
            })
        
        # Sort by timestamp and limit
        logs.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return logs[:limit]
        
    except Exception as e:
        print(f"Error in get_activity_logs: {e}")
        return []