# -*- coding: utf-8 -*-
"""后台任务运行器：回测/选股等长任务放到后台线程执行

- 主线程用 @st.fragment(run_every=...) 定时读取进度并渲染
- 支持中途停止（worker 周期性检查 job['stop']）
- 任务状态放在模块级注册表（线程安全），会话切换页面不影响任务继续运行
"""
import threading

_REGISTRY = {}
_LOCK = threading.Lock()


def get_job(key):
    with _LOCK:
        return _REGISTRY.get(key)


def start_job(key, worker, args=(), kwargs=None):
    """启动后台任务。worker(job, *args) 负责更新 job 字典。"""
    job = {
        "running": True,
        "stop": False,
        "progress": 0.0,
        "done": 0,
        "total": 0,
        "status": "准备中",
        "result": None,
        "stats": None,
        "error": "",
        "finalized": False,
    }
    with _LOCK:
        _REGISTRY[key] = job

    def _wrap():
        try:
            worker(job, *args, **(kwargs or {}))
        except Exception as exc:
            job["error"] = str(exc)
            job["status"] = "失败"
        finally:
            job["running"] = False

    threading.Thread(target=_wrap, daemon=True).start()
    return job


def request_stop(key):
    job = get_job(key)
    if job:
        job["stop"] = True
        job["status"] = "正在停止..."
        return True
    return False
