#!/usr/bin/env python3
"""No GitHub writes or paid model calls; exercise the PR attempt contract."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import claim_pr_review as claim


class ClaimReviewTests(unittest.TestCase):
    def test_first_attempt_is_persisted_and_all_later_attempts_skip(self):
        comments = []

        def api(url, token, body=None):
            if body is not None:
                comments.append(body)
                return {"id": 1, **body}
            return comments.copy()

        with patch.object(claim, "request_json", side_effect=api):
            self.assertTrue(claim.claim_review("https://api.github.com", "org/repo", 7, "token"))
            # No SHA, mode or run ID in the key: none can grant another attempt.
            for _ in range(4):
                self.assertFalse(claim.claim_review("https://api.github.com", "org/repo", 7, "token"))
        self.assertEqual(len(comments), 1)
        self.assertTrue(comments[0]["body"].startswith(claim.MARKER))

    def test_claim_on_later_comment_page_skips_without_post(self):
        with patch.object(claim, "request_json", side_effect=[
            [{"body": "unrelated"}] * 100, [{"body": claim.MARKER}]
        ]) as api:
            self.assertFalse(claim.claim_review("https://github.example/api/v3/", "org/repo", 7, "token"))
        self.assertEqual(api.call_count, 2)
        self.assertIn("?per_page=100&page=2", api.call_args.args[0])
        self.assertEqual(len(api.call_args.args), 2)

    def test_unrelated_or_empty_comments_do_not_block(self):
        with patch.object(claim, "request_json", side_effect=[
            [{"body": None}, {"body": "review text"}], {"id": 2}
        ]) as api:
            self.assertTrue(claim.claim_review("https://api.github.com", "org/repo", 8, "token"))
        self.assertIn("/issues/8/comments", api.call_args.args[0])

    def test_read_failure_never_posts(self):
        with patch.object(claim, "request_json", side_effect=urllib.error.URLError("unavailable")) as api:
            with self.assertRaises(urllib.error.URLError):
                claim.claim_review("https://api.github.com", "org/repo", 7, "token")
        self.assertEqual(api.call_count, 1)

    def test_ambiguous_post_failure_is_not_retried(self):
        with patch.object(claim, "request_json", side_effect=[[], TimeoutError()]) as api:
            with self.assertRaises(TimeoutError):
                claim.claim_review("https://api.github.com", "org/repo", 7, "token")
        self.assertEqual(api.call_count, 2)

    def test_main_output_fails_closed_and_propagates_error(self):
        for result in (True, False, TimeoutError()):
            with self.subTest(result=result), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "output"
                env = dict(GITHUB_OUTPUT=str(output), GITHUB_REPOSITORY="org/repo",
                           PR_NUMBER="7", GITHUB_TOKEN="token")
                with patch.dict(os.environ, env), patch.object(claim, "claim_review") as reserve:
                    if isinstance(result, Exception):
                        reserve.side_effect = result
                        with self.assertRaises(TimeoutError):
                            claim.main()
                    else:
                        reserve.return_value = result
                        claim.main()
                self.assertEqual(output.read_text(), "allowed=false\n" +
                                 ("allowed=true\n" if result is True else ""))


if __name__ == "__main__":
    unittest.main()
