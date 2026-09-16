import unittest

from normalize_review import CANONICAL_NO_FINDING, normalize_review


class NormalizeReviewTest(unittest.TestCase):
    def test_removes_trailing_explanation_from_single_no_finding_line(self) -> None:
        review = (
            "## 이 PR이 하는 일\n\n- 버전 범프\n\n"
            "## 리뷰\n\n"
            "- P4 규칙 기준으로 지적할 이슈 없음. 로직 변경이 없습니다.\n"
        )

        normalized = normalize_review(review)

        self.assertEqual(
            normalized,
            "## 이 PR이 하는 일\n\n- 버전 범프\n\n"
            f"## 리뷰\n\n{CANONICAL_NO_FINDING}\n",
        )

    def test_keeps_exact_verdict_stable(self) -> None:
        review = f"## 이 PR이 하는 일\n\n- 변경\n\n## 리뷰\n\n{CANONICAL_NO_FINDING}\n"
        self.assertEqual(normalize_review(review), review)

    def test_normalizes_severity_specific_no_finding_variants(self) -> None:
        for label in ("P0", "P1", "P2", "P3", "P4", "P0-P2", "P0–P2"):
            with self.subTest(label=label):
                review = (
                    "## 이 PR이 하는 일\n\n- 버전 범프\n\n"
                    "## 리뷰\n\n"
                    f"- {label} 규칙 기준으로 지적할 이슈 없음. 설명입니다.\n"
                )
                self.assertEqual(
                    normalize_review(review),
                    "## 이 PR이 하는 일\n\n- 버전 범프\n\n"
                    f"## 리뷰\n\n{CANONICAL_NO_FINDING}\n",
                )

    def test_does_not_modify_a_finding(self) -> None:
        review = (
            "## 이 PR이 하는 일\n\n- 변경\n\n## 리뷰\n\n"
            "- P2 `src/app.py:10` 실패 경로가 열려 있습니다.\n"
        )
        self.assertEqual(normalize_review(review), review)

    def test_does_not_hide_mixed_or_multiline_review(self) -> None:
        review = (
            "## 이 PR이 하는 일\n\n- 변경\n\n## 리뷰\n\n"
            "- P4 규칙 기준으로 지적할 이슈 없음.\n"
            "- P2 `src/app.py:10` 실패 경로가 열려 있습니다.\n"
        )
        self.assertEqual(normalize_review(review), review)

    def test_only_normalizes_review_section(self) -> None:
        review = (
            "## 이 PR이 하는 일\n\n"
            "- P4 규칙 기준으로 지적할 이슈 없음. 설명입니다.\n\n"
            "## 리뷰\n\n- P3 `src/app.py:10` 정리할 수 있습니다.\n"
        )
        self.assertEqual(normalize_review(review), review)


if __name__ == "__main__":
    unittest.main()
