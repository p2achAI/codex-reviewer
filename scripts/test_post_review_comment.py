#!/usr/bin/env python3

import io
import json
import os
import tempfile
import unittest
from unittest import mock

import post_review_comment


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class PostReviewCommentTest(unittest.TestCase):
    def test_post_comment_uses_pull_request_issue_comments_api(self):
        response = FakeResponse({"html_url": "https://example.test/comment/1"})

        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            result = post_review_comment.post_comment(
                "https://api.github.test",
                "p2achAI/example",
                "42",
                "review body",
                "secret-token",
            )

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.github.test/repos/p2achAI/example/issues/42/comments",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data), {"body": "review body"})
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(result["html_url"], "https://example.test/comment/1")

    def test_main_posts_review_file(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as review:
            review.write("## Review\n\nNo findings.")
            review.flush()
            env = {
                "GITHUB_TOKEN": "secret-token",
                "GITHUB_REPOSITORY": "p2achAI/example",
                "PR_NUMBER": "42",
                "REVIEW_FILE": review.name,
            }
            result = {"html_url": "https://example.test/comment/1"}
            with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(
                post_review_comment, "post_comment", return_value=result
            ) as post:
                self.assertEqual(post_review_comment.main(), 0)

        post.assert_called_once_with(
            "https://api.github.com",
            "p2achAI/example",
            "42",
            "## Review\n\nNo findings.",
            "secret-token",
        )

    def test_main_rejects_empty_review(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as review:
            review.write("  \n")
            review.flush()
            env = {
                "GITHUB_TOKEN": "secret-token",
                "GITHUB_REPOSITORY": "p2achAI/example",
                "PR_NUMBER": "42",
                "REVIEW_FILE": review.name,
            }
            with mock.patch.dict(os.environ, env, clear=True), mock.patch(
                "sys.stderr", new_callable=io.StringIO
            ) as stderr:
                self.assertEqual(post_review_comment.main(), 1)

        self.assertIn("is empty", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
