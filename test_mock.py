class MockTool:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def invoke(self, args):
        return self.func(**args)

def mock_tool_decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return MockTool(args[0])
    def wrapper(f):
        return MockTool(f)
    return wrapper

@mock_tool_decorator
def test_func():
    return "test"

@mock_tool_decorator(name="test")
def test_func_2():
    return "test 2"

print(type(test_func))
print(type(test_func_2))
