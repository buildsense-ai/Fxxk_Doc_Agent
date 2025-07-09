# 文件名: main.py
# -*- coding: utf-8 -*-

"""
main.py

项目的执行入口。
负责启动生成任务并演示如何轮询任务状态。
"""

import json
import os
from typing import Dict, Any, Optional

# --- 从其他模块导入依赖 ---
from generator import LongDocumentGenerator, TaskState
from config import Config


def get_task_status(task_id_to_check: str) -> Optional[Dict[str, Any]]:
    """
    模拟轮询API `GET /api/tasks/{taskId}/status` 的后端实现。
    它从任务状态文件中读取并返回一个简化的状态摘要。
    """
    task_state = TaskState(task_id_to_check)
    if task_state.load():
        # [已更新] 增加docxPublicUrl字段
        return {
            "taskId": task_state.data['taskId'],
            "overallStatus": task_state.data['status'],
            "progressPercentage": task_state.data['progressPercentage'],
            "message": task_state.data['currentStatusMessage'],
            "lastUpdated": task_state.data.get('lastUpdatedTimestamp', 'N/A'),
            "markdownPublicUrl": task_state.data.get('markdownPublicUrl', ''),
            "docxPublicUrl": task_state.data.get('docxPublicUrl', '')
        }
    return None


if __name__ == "__main__":

    # --- 示例1: 启动一个长篇报告生成任务 ---
    print(">>> 启动一个新的长篇报告生成任务...")
    generator_long = LongDocumentGenerator()
    chathistory_long = "我们之前讨论了关于1号住宅楼_1_01_结构设计总说明。"
    request_long = "请帮我解读和分析这份“1号住宅楼_1_01_结构设计总说明”文档，并生成一份详细的《文物影响评估报告》。"

    # 明确指定 report_type='long'
    task_id_long = generator_long.start_new_job(chathistory_long, request_long, report_type='long')
    print(f"\n>>> 长篇报告任务执行完毕。任务ID: {task_id_long}")

    print("\n\n>>> 模拟客户端轮询长篇报告的最终状态...")
    final_status_long = get_task_status(task_id_long)
    if final_status_long:
        print("轮询API返回的最终状态:")
        print(json.dumps(final_status_long, indent=2, ensure_ascii=False))

    # --- [新增] 示例2: 启动一个短篇报告生成任务 (默认注释掉) ---
    # print("\n" + "="*50 + "\n")
    # print(">>> 启动一个新的通用短文生成任务...")
    # generator_short = LongDocumentGenerator()
    # chathistory_short = "我们聊了最近的市场趋势。"
    # request_short = "请帮我写一篇关于“人工智能对市场营销行业未来影响”的分析短文，大概1500字。"

    # # 指定 report_type='short'
    # task_id_short = generator_short.start_new_job(chathistory_short, request_short, report_type='short')
    # print(f"\n>>> 短篇报告任务执行完毕。任务ID: {task_id_short}")

    # print("\n\n>>> 模拟客户端轮询短篇报告的最终状态...")
    # final_status_short = get_task_status(task_id_short)
    # if final_status_short:
    #     print("轮询API返回的最终状态:")
    #     print(json.dumps(final_status_short, indent=2, ensure_ascii=False))

