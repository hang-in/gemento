import unittest
from tools.chunker import chunk_document
from tools.bm25_tool import bm25_retrieve


class TestBM25Tool(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            {"chunk_id": 0, "content": "apple orange banana fruit basket", "word_count": 5, "start_offset": 0, "end_offset": 5},
            {"chunk_id": 1, "content": "car vehicle transportation highway", "word_count": 4, "start_offset": 5, "end_offset": 9},
            {"chunk_id": 2, "content": "apple pie recipe baking kitchen", "word_count": 5, "start_offset": 9, "end_offset": 14},
        ]

    def test_top_k_returns_relevant(self):
        results = bm25_retrieve("apple recipe", self.chunks, top_k=2)
        self.assertEqual(len(results), 2)
        # chunk_2 (apple pie recipe)가 가장 높은 점수여야 함
        self.assertEqual(results[0]["chunk_id"], 2)

    def test_empty_chunks_raises(self):
        with self.assertRaises(ValueError):
            bm25_retrieve("test", [], top_k=3)

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            bm25_retrieve("", self.chunks, top_k=3)

    def test_top_k_exceeds_chunks(self):
        results = bm25_retrieve("apple", self.chunks, top_k=10)
        self.assertLessEqual(len(results), 3)

    def test_score_descending(self):
        results = bm25_retrieve("apple fruit", self.chunks, top_k=3)
        scores = [r["bm25_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_end_to_end_with_chunker(self):
        long_text = "This is a document about planets. Jupiter is the largest. " * 50
        long_text += "The smallest dwarf planet is Ceres. " * 30
        long_text += "Mars has two moons. " * 40
        chunks = chunk_document(long_text, size=30, overlap=5)
        dicts = [c.to_dict() for c in chunks]
        results = bm25_retrieve("smallest planet", dicts, top_k=3)
        # Ceres가 언급된 chunk가 top에 등장해야 함
        self.assertTrue(any("ceres" in r["content"].lower() for r in results[:2]))


if __name__ == "__main__":
    unittest.main()
