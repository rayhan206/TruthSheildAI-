import unittest

from backend.engine.media_detector import _extract_ai_score, _uniform_indexes


class MediaDetectorTests(unittest.TestCase):
    def test_uniform_indexes_include_range_edges(self):
        indexes = _uniform_indexes(5, 95, 10)
        self.assertEqual(indexes[0], 5)
        self.assertEqual(indexes[-1], 95)
        self.assertEqual(len(indexes), 10)

    def test_extracts_artificial_label_probability(self):
        score = _extract_ai_score([
            {"label": "human", "score": 0.12},
            {"label": "artificial", "score": 0.88},
        ])
        self.assertAlmostEqual(score, 0.88)

    def test_inverts_real_probability(self):
        score = _extract_ai_score([{"label": "real", "score": 0.76}])
        self.assertAlmostEqual(score, 0.24)


if __name__ == "__main__":
    unittest.main()

