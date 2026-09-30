import functools
from typing import Callable, Any

try:
    from langchain_core.tools import tool
except (ImportError, ModuleNotFoundError):
    class MockTool:
        """Fallback tool wrapper replicating LangChain tool decorator functionality."""
        def __init__(self, func: Callable, name: str = None, description: str = None):
            self.func = func
            self.name = name or getattr(func, "__name__", "tool")
            self.description = description or getattr(func, "__doc__", "")
            self.__name__ = getattr(func, "__name__", self.name)
            self.__doc__ = getattr(func, "__doc__", self.description)
            try:
                functools.update_wrapper(self, func)
            except Exception:
                pass

        def __call__(self, *args, **kwargs) -> Any:
            return self.func(*args, **kwargs)

        def invoke(self, args, *_, **__) -> Any:
            if isinstance(args, dict):
                return self.func(**args)
            return self.func(args)

    def tool(*args, **kwargs):
        """Fallback tool decorator that wraps functions to support .invoke() and direct calls."""
        if len(args) == 1 and callable(args[0]):
            return MockTool(args[0])
        def wrapper(f):
            name = kwargs.get("name")
            desc = kwargs.get("description")
            return MockTool(f, name=name, description=desc)
        return wrapper
