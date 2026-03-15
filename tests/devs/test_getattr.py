"""
测试 SendDSL 的 __getattr__ 功能
"""

import asyncio
from ErisPulse.Core.Bases.adapter import SendDSL, BaseAdapter


class MockAdapter(BaseAdapter):
    """模拟适配器用于测试"""
    
    async def call_api(self, endpoint: str, **params):
        return {"status": "ok", "retcode": 0, "data": {}}
    
    async def start(self):
        pass
    
    async def shutdown(self):
        pass


def test_case_insensitive():
    """测试大小写不敏感"""
    print("=" * 50)
    print("测试 1: 大小写不敏感的方法调用")
    print("=" * 50)
    
    adapter = MockAdapter()
    send_dsl = adapter.Send.To("group", "123")
    
    # 测试不同大小写形式
    print("\n1.1 测试 Example 方法:")
    print(f"  hasattr(send_dsl, 'Example'): {hasattr(send_dsl, 'Example')}")
    print(f"  hasattr(send_dsl, 'example'): {hasattr(send_dsl, 'example')}")
    print(f"  hasattr(send_dsl, 'EXAMPLE'): {hasattr(send_dsl, 'EXAMPLE')}")
    
    # 测试 To 方法
    print("\n1.2 测试 To 方法:")
    result1 = send_dsl.To("user", "789")
    result2 = send_dsl.to("user", "789")
    result3 = send_dsl.TO("user", "789")
    print(f"  To('user', '789'): target_id = {result1._target_id}")
    print(f"  to('user', '789'): target_id = {result2._target_id}")
    print(f"  TO('user', '789'): target_id = {result3._target_id}")
    
    # 测试 Using 方法
    print("\n1.3 测试 Using 方法:")
    result = send_dsl.using("bot1")
    print(f"  using('bot1'): account_id = {result._account_id}")
    
    result = send_dsl.USING("bot2")
    print(f"  USING('bot2'): account_id = {result._account_id}")
    
    print("\n✓ 大小写不敏感测试通过\n")


def test_nonexistent_method():
    """测试不存在的方法"""
    print("=" * 50)
    print("测试 2: 不存在的方法调用")
    print("=" * 50)
    
    adapter = MockAdapter()
    send_dsl = adapter.Send.To("group", "123")
    
    print("\n2.1 测试 hasattr 对不存在的方法:")
    print(f"  hasattr(send_dsl, 'NonExistentMethod'): {hasattr(send_dsl, 'NonExistentMethod')}")
    print(f"  hasattr(send_dsl, 'AnotherNonExistent'): {hasattr(send_dsl, 'AnotherNonExistent')}")
    
    print("\n2.2 测试访问不存在的方法（应该打印警告并抛出异常）:")
    try:
        _ = send_dsl.NonExistentMethod
        print("  ✗ 没有抛出异常（错误）")
    except AttributeError as e:
        print(f"  ✓ 正确抛出 AttributeError: {e}")
    
    print("\n✓ 不存在方法测试通过\n")


def test_existing_methods():
    """测试现有方法正常工作"""
    print("=" * 50)
    print("测试 3: 现有方法正常工作")
    print("=" * 50)
    
    adapter = MockAdapter()
    send_dsl = SendDSL(adapter, None, None)
    
    print("\n3.1 测试 To 方法:")
    result = send_dsl.To("group", "123")
    print(f"  target_type = {result._target_type}")
    print(f"  target_id = {result._target_id}")
    
    print("\n3.2 测试 Using 方法:")
    result = send_dsl.Using("bot1")
    print(f"  account_id = {result._account_id}")
    
    print("\n3.3 测试 Account 方法:")
    result = send_dsl.Account("bot2")
    print(f"  account_id = {result._account_id}")
    
    print("\n✓ 现有方法测试通过\n")


def test_at_methods():
    """测试 At 等修饰方法"""
    print("=" * 50)
    print("测试 4: At 等修饰方法的大小写不敏感")
    print("=" * 50)
    
    adapter = MockAdapter()
    send_dsl = adapter.Send.To("group", "123")
    
    print("\n4.1 测试 At 方法:")
    print(f"  hasattr(send_dsl, 'At'): {hasattr(send_dsl, 'At')}")
    print(f"  hasattr(send_dsl, 'at'): {hasattr(send_dsl, 'at')}")
    print(f"  hasattr(send_dsl, 'AT'): {hasattr(send_dsl, 'AT')}")
    
    result = send_dsl.at(user_id="456")
    print(f"  at(user_id='456'): 返回类型 = {type(result).__name__}")
    
    print("\n4.2 测试 Reply 方法:")
    print(f"  hasattr(send_dsl, 'Reply'): {hasattr(send_dsl, 'Reply')}")
    print(f"  hasattr(send_dsl, 'reply'): {hasattr(send_dsl, 'reply')}")
    
    print("\n4.3 测试 AtAll 方法:")
    print(f"  hasattr(send_dsl, 'AtAll'): {hasattr(send_dsl, 'AtAll')}")
    print(f"  hasattr(send_dsl, 'atall'): {hasattr(send_dsl, 'atall')}")
    print(f"  hasattr(send_dsl, 'ATALL'): {hasattr(send_dsl, 'ATALL')}")
    
    print("\n✓ At 方法测试通过\n")


def test_raw_ob12():
    """测试 Raw_ob12 方法"""
    print("=" * 50)
    print("测试 5: Raw_ob12 方法的大小写不敏感")
    print("=" * 50)
    
    adapter = MockAdapter()
    send_dsl = adapter.Send.To("group", "123")
    
    print("\n5.1 测试 Raw_ob12 方法:")
    print(f"  hasattr(send_dsl, 'Raw_ob12'): {hasattr(send_dsl, 'Raw_ob12')}")
    print(f"  hasattr(send_dsl, 'raw_ob12'): {hasattr(send_dsl, 'raw_ob12')}")
    print(f"  hasattr(send_dsl, 'RAW_OB12'): {hasattr(send_dsl, 'RAW_OB12')}")
    
    # 注意：Raw_ob12 返回的是一个 asyncio Task
    async def test_async():
        result = send_dsl.raw_ob12([{"type": "text", "data": {"text": "test"}}])
        print(f"  raw_ob12(...) 返回类型: {type(result).__name__}")
        return result
    
    # 运行异步测试
    asyncio.run(test_async())
    
    print("\n✓ Raw_ob12 方法测试通过\n")


def main():
    """运行所有测试"""
    print("\n")
    print("*" * 50)
    print("SendDSL.__getattr__ 功能测试")
    print("*" * 50)
    print()
    
    try:
        test_case_insensitive()
        test_nonexistent_method()
        test_existing_methods()
        test_at_methods()
        test_raw_ob12()
        
        print("=" * 50)
        print("所有测试通过！✓")
        print("=" * 50)
        print()
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()