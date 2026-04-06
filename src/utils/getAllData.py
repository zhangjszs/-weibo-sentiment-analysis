"""
旧版兼容模块。

历史上该模块在导入时就会触发全量文章/评论查询，副作用很重。
当前仅保留最小兼容壳，避免 import 时访问数据库。
"""

from .getPublicData import getAllCommentsData, getAllData

# 保留历史变量名以兼容旧代码，但不再在导入阶段执行查询。
allData = []
commentList = []

__all__ = ["getAllData", "getAllCommentsData", "allData", "commentList"]
