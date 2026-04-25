import unittest
from tools.chunker import chunk_document, Chunk


class TestChunker(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(chunk_document(""), [])

    def test_short_text_one_chunk(self):
        text = "hello world " * 100  # 200 words
        chunks = chunk_document(text, size=500, overlap=50)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].word_count, 200)

    def test_exact_size_boundary(self):
        text = " ".join(str(i) for i in range(500))
        chunks = chunk_document(text, size=500, overlap=50)
        self.assertEqual(len(chunks), 1)

    def test_size_plus_one(self):
        text = " ".join(str(i) for i in range(501))
        chunks = chunk_document(text, size=500, overlap=50)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[1].start_offset, 450)

    def test_overlap_content(self):
        text = " ".join(str(i) for i in range(1000))
        chunks = chunk_document(text, size=500, overlap=50)
        # chunk 0: 0~499, chunk 1: 450~949 → 450~499가 overlap
        overlap_chunk0 = chunks[0].content.split()[-50:]
        overlap_chunk1 = chunks[1].content.split()[:50]
        self.assertEqual(overlap_chunk0, overlap_chunk1)

    def test_invalid_params(self):
        with self.assertRaises(ValueError):
            chunk_document("test", size=100, overlap=100)
        with self.assertRaises(ValueError):
            chunk_document("test", size=0, overlap=0)
        with self.assertRaises(ValueError):
            chunk_document("test", size=100, overlap=-1)

    def test_chunk_to_dict(self):
        text = "a b c d e"
        chunks = chunk_document(text, size=3, overlap=1)
        d = chunks[0].to_dict()
        self.assertEqual(set(d.keys()), {"chunk_id", "content", "word_count", "start_offset", "end_offset"})


if __name__ == "__main__":
    unittest.main()
