import ast
import concurrent.futures
import math
import time
from datetime import datetime

import numpy as np
import pandas as pd


class StrategySandboxError(Exception):
    pass


FORBIDDEN_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.ClassDef,
    ast.Global,
    ast.Nonlocal,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Raise,
    ast.Delete,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Lambda,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
)

FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "getattr",
    "globals",
    "hasattr",
    "help",
    "input",
    "locals",
    "memoryview",
    "open",
    "print",
    "setattr",
    "super",
    "type",
    "vars",
}

FORBIDDEN_NAMES = FORBIDDEN_CALLS | {
    "breakpoint",
    "exit",
    "quit",
}

SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


def validate_strategy_source(source):
    try:
        tree = ast.parse(str(source))
    except SyntaxError as exc:
        raise StrategySandboxError(f"strategy syntax error: {exc}") from exc

    body = [node for node in tree.body if not _is_docstring_expr(node)]
    if not body or not all(isinstance(node, ast.FunctionDef) for node in body):
        raise StrategySandboxError("strategy may only contain function definitions")

    functions = {node.name: node for node in body}
    func = functions.get("generate_signals")
    if func is None:
        raise StrategySandboxError("strategy entrypoint must be generate_signals(df)")
    if any(node.decorator_list for node in body):
        raise StrategySandboxError("strategy decorators are not allowed")
    if any(node.name.startswith("__") for node in body):
        raise StrategySandboxError("double-underscore function names are not allowed")
    if len(func.args.args) != 1 or func.args.args[0].arg != "df":
        raise StrategySandboxError("generate_signals must accept one argument named df")
    if func.args.vararg or func.args.kwarg or func.args.defaults or func.args.kw_defaults:
        raise StrategySandboxError("generate_signals must not use extra args or defaults")

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            raise StrategySandboxError(f"{type(node).__name__} is not allowed in strategy code")
        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in FORBIDDEN_NAMES:
                raise StrategySandboxError(f"name {node.id!r} is not allowed")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in FORBIDDEN_CALLS:
                raise StrategySandboxError(f"attribute {node.attr!r} is not allowed")
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALLS or call_name.startswith("__"):
                raise StrategySandboxError(f"call {call_name!r} is not allowed")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "__" in node.value:
            raise StrategySandboxError("double-underscore strings are not allowed")

    return tree


def execute_strategy(source, df, timeout_seconds=2.0):
    tree = validate_strategy_source(source)
    namespace = {
        "__builtins__": SAFE_BUILTINS,
        "datetime": datetime,
        "math": math,
        "np": np,
        "pd": pd,
        "time": time,
    }
    exec(compile(tree, "<strategy>", "exec"), namespace, namespace)
    func = namespace.get("generate_signals")
    if not callable(func):
        raise StrategySandboxError("generate_signals(df) was not created")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, df.copy())
    try:
        result = future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise StrategySandboxError("strategy execution timed out") from exc
    finally:
        if future.done():
            executor.shutdown(wait=False, cancel_futures=True)

    if result is None or not isinstance(result, pd.DataFrame):
        raise StrategySandboxError("generate_signals(df) must return a pandas DataFrame")
    if len(result) != len(df):
        raise StrategySandboxError("returned DataFrame must keep the same row count")

    return normalize_strategy_result(result)


def normalize_strategy_result(df):
    result = df.copy()
    sig_col = next((col for col in result.columns if str(col).lower() == "signal"), None)
    if sig_col is None:
        raise StrategySandboxError("strategy must create a Signal column")

    signal = result[sig_col].fillna(0)
    if not np.issubdtype(signal.dtype, np.number):
        text_signal = signal.astype(str).str.lower().str.strip()
        signal = np.select(
            [
                text_signal.str.contains(r"buy|long|true|yes|1", regex=True),
                text_signal.str.contains(r"sell|short|-1", regex=True),
            ],
            [1, -1],
            default=0,
        )
    result["Signal"] = pd.Series(signal, index=result.index).apply(
        lambda value: 1 if float(value) > 0.1 else (-1 if float(value) < -0.1 else 0)
    ).astype(int)
    return result


def _is_docstring_expr(node):
    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(
        node.value.value, str
    )


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
