import os
import sys

from spiderComments import start as commentsStart
from spiderContent import start as contentStart

# 添加项目根目录到 Python 路径，以便导入 config 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
import time

import pandas as pd
from sqlalchemy import create_engine

# 导入统一配置模块
from config.settings import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 优化的数据库引擎配置（使用统一配置）
engine = create_engine(
    Config.get_database_url(),
    pool_size=5,
    max_overflow=10,
    pool_recycle=Config.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=Config.IS_DEVELOPMENT,
)


def save_to_sql():
    """优化的数据保存函数"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    article_file = os.path.join(base_dir, "data", "articleData.csv")
    comments_file = os.path.join(base_dir, "data", "commentsData.csv")

    try:
        # 检查文件是否存在
        if not os.path.exists(article_file):
            logger.warning(f"文章数据文件不存在: {article_file}")
            return

        if not os.path.exists(comments_file):
            logger.warning(f"评论数据文件不存在: {comments_file}")
            return

        logger.info("开始读取爬取的数据文件...")

        # 读取新数据
        articleNewDf = pd.read_csv(article_file)
        commentNewDf = pd.read_csv(comments_file)

        logger.info(
            f"读取到 {len(articleNewDf)} 条文章数据，{len(commentNewDf)} 条评论数据"
        )

        # 处理文章数据
        try:
            logger.info("正在处理文章数据...")
            articleOldDf = pd.read_sql("SELECT * FROM article", engine)

            if not articleOldDf.empty:
                # 合并数据并去重
                concatDf = pd.concat([articleNewDf, articleOldDf], ignore_index=True)
                concatDf = concatDf.drop_duplicates(subset="id", keep="first")
                logger.info(f"合并后文章数据: {len(concatDf)} 条")
            else:
                concatDf = articleNewDf
                logger.info("数据库为空，直接插入新数据")

            # 批量插入，提升性能
            concatDf.to_sql(
                "article", con=engine, if_exists="replace", index=False, chunksize=1000
            )
            logger.info("文章数据保存成功")

        except Exception as e:
            logger.warning(f"文章数据合并失败，直接插入新数据: {e}")
            articleNewDf.to_sql(
                "article", con=engine, if_exists="replace", index=False, chunksize=1000
            )

        # 处理评论数据
        try:
            logger.info("正在处理评论数据...")
            commentOldDf = pd.read_sql("SELECT * FROM comments", engine)

            if not commentOldDf.empty:
                # 合并数据并去重（基于内容去重）
                concatCommentDf = pd.concat(
                    [commentNewDf, commentOldDf], ignore_index=True
                )
                concatCommentDf = concatCommentDf.drop_duplicates(
                    subset="content", keep="first"
                )
                logger.info(f"合并后评论数据: {len(concatCommentDf)} 条")
            else:
                concatCommentDf = commentNewDf
                logger.info("评论表为空，直接插入新数据")

            # 批量插入，提升性能
            concatCommentDf.to_sql(
                "comments", con=engine, if_exists="replace", index=False, chunksize=1000
            )
            logger.info("评论数据保存成功")

        except Exception as e:
            logger.warning(f"评论数据合并失败，直接插入新数据: {e}")
            commentNewDf.to_sql(
                "comments", con=engine, if_exists="replace", index=False, chunksize=1000
            )

        logger.info("数据保存完成")

    except Exception as e:
        logger.error(f"数据保存过程发生错误: {e}")
        raise e

    finally:
        # 清理临时文件
        try:
            if os.path.exists(article_file):
                os.remove(article_file)
                logger.info(f"已删除临时文件: {article_file}")

            if os.path.exists(comments_file):
                os.remove(comments_file)
                logger.info(f"已删除临时文件: {comments_file}")
        except Exception as e:
            logger.warning(f"删除临时文件失败: {e}")


def main():
    """主函数 - 添加错误处理和日志"""
    start_time = time.time()
    logger.info("开始执行微博数据爬取任务")

    try:
        # 爬取文章内容
        logger.info("开始爬取文章内容...")
        contentStart(2, 1)  # 爬取2个类型，每个类型1页
        logger.info("文章内容爬取完成")

        # 爬取评论内容
        logger.info("开始爬取评论内容...")
        commentsStart()
        logger.info("评论内容爬取完成")

        # 保存到数据库
        logger.info("开始保存数据到数据库...")
        save_to_sql()
        logger.info("数据保存完成")

        end_time = time.time()
        logger.info(f"爬取任务完成，总耗时: {end_time - start_time:.2f} 秒")

    except Exception as e:
        logger.error(f"爬取任务执行失败: {e}")
        raise e


if __name__ == "__main__":
    main()
