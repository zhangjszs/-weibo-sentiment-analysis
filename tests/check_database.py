#!/usr/bin/env python3


import pandas as pd
from sqlalchemy import create_engine


def check_database():
    """检查数据库中的数据"""
    # 配置数据库连接
    engine = create_engine("mysql+pymysql://root:123456@127.0.0.1/wb?charset=utf8mb4")

    try:
        # 查询文章表
        article_count_df = pd.read_sql("SELECT COUNT(*) as count FROM article", engine)
        article_count = article_count_df.iloc[0]["count"]
        print(f"📊 文章表记录数: {article_count}")

        # 查询评论表
        comment_count_df = pd.read_sql("SELECT COUNT(*) as count FROM comments", engine)
        comment_count = comment_count_df.iloc[0]["count"]
        print(f"📊 评论表记录数: {comment_count}")

        if article_count > 0:
            # 查看最新的几条文章记录
            latest_articles = pd.read_sql(
                "SELECT id, content, created_at, authorName, type FROM article ORDER BY created_at DESC LIMIT 5",
                engine,
            )
            print("\n📰 最新5条文章:")
            for idx, row in latest_articles.iterrows():
                content = (
                    str(row["content"])[:50] if pd.notna(row["content"]) else "无内容"
                )
                author = (
                    str(row["authorName"])
                    if pd.notna(row["authorName"])
                    else "未知作者"
                )
                article_type = str(row["type"]) if pd.notna(row["type"]) else "未知类型"
                created_at = (
                    str(row["created_at"])
                    if pd.notna(row["created_at"])
                    else "未知时间"
                )
                print(f"  • ID: {row['id']} | 作者: {author} | 类型: {article_type}")
                print(f"    内容: {content}...")
                print(f"    时间: {created_at}\n")

        if comment_count > 0:
            # 查看最新的几条评论记录
            latest_comments = pd.read_sql(
                "SELECT articleId, content, created_at, authorName FROM comments ORDER BY created_at DESC LIMIT 5",
                engine,
            )
            print("\n💬 最新5条评论:")
            for idx, row in latest_comments.iterrows():
                content = (
                    str(row["content"])[:50] if pd.notna(row["content"]) else "无内容"
                )
                author = (
                    str(row["authorName"])
                    if pd.notna(row["authorName"])
                    else "未知作者"
                )
                created_at = (
                    str(row["created_at"])
                    if pd.notna(row["created_at"])
                    else "未知时间"
                )
                print(f"  • 文章ID: {row['articleId']} | 评论者: {author}")
                print(f"    评论: {content}...")
                print(f"    时间: {created_at}\n")

        # 统计不同类型的文章
        if article_count > 0:
            type_stats = pd.read_sql(
                "SELECT type, COUNT(*) as count FROM article GROUP BY type", engine
            )
            print("\n📈 文章类型统计:")
            for idx, row in type_stats.iterrows():
                print(f"  • {row['type']}: {row['count']} 条")

        return article_count, comment_count

    except Exception as e:
        print(f"❌ 数据库查询错误: {e}")
        return 0, 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("🔍 正在检查数据库中的爬虫数据...")
    print("=" * 60)

    article_count, comment_count = check_database()

    print("\n" + "=" * 60)
    if article_count > 0 or comment_count > 0:
        print("✅ 数据库中有数据！爬虫保存成功。")
    else:
        print("⚠️  数据库中暂无数据，可能是爬取失败或数据库连接问题。")

    print(f"📊 总计: {article_count} 条文章，{comment_count} 条评论")
