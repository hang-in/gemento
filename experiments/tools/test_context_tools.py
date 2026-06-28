"""Redis Context Tools unit tests.

실제 기동된 Redis 컨테이너를 활용해 read_context 및 grep_context의 동작을 테스트합니다.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import unittest
from context_tools import get_redis_client, read_context, grep_context



class TestContextTools(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Redis 연결 시도 및 테스트 키 초기화
        cls.r = get_redis_client()
        cls.test_handle = "ctx:test_run_01:stdout"
        
        # 16KB 용량 제한을 피하기 위해 각 라인을 짧게 구성 (600줄 전체 4.8KB 내외)
        cls.lines = [f"Line {i}" for i in range(1, 601)]
        cls.text = "\n".join(cls.lines)
        
        # Redis에 적재
        cls.r.set(cls.test_handle, cls.text)
        
    @classmethod
    def tearDownClass(cls):
        # 테스트 데이터 정리
        cls.r.delete(cls.test_handle)

    def test_read_context_basic(self):
        # 10라인부터 15라인까지 읽기
        res = read_context(self.test_handle, start_line=10, end_line=15)
        self.assertNotIn("error", res)
        self.assertEqual(res["start_line"], 10)
        self.assertEqual(res["end_line"], 15)
        self.assertFalse(res["truncated_by_lines"])
        
        # 실제 내용 확인
        expected_content = "\n".join(self.lines[9:15])
        self.assertEqual(res["content"], expected_content)

    def test_read_context_limits(self):
        # 500라인을 초과해 읽으려 할 때, 500라인으로 자동 슬라이싱 및 Truncated 플래그 확인
        res = read_context(self.test_handle, start_line=1, end_line=550)
        self.assertNotIn("error", res)
        self.assertTrue(res["truncated_by_lines"])
        self.assertEqual(res["end_line"], 500)  # 1 + 500 - 1 = 500
        
        content_lines = res["content"].splitlines()
        self.assertEqual(len(content_lines), 500)

    def test_grep_context_basic(self):
        # 특정 행 검색
        res = grep_context(self.test_handle, pattern="Line 100")
        self.assertNotIn("error", res)
        self.assertEqual(res["total_matches"], 1)
        self.assertIn("100: Line 100", res["matches"])

    def test_grep_context_regex(self):
        # 정규식을 이용해 590~599 범위의 10개 행 검색
        res = grep_context(self.test_handle, pattern="Line 59[0-9]")
        self.assertNotIn("error", res)
        self.assertEqual(res["total_matches"], 10)  # 590 ~ 599
        self.assertIn("590: Line 590", res["matches"])


if __name__ == "__main__":
    unittest.main()

