import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from antsk_filechunk.unified_document_parser import DocumentContent, UnifiedDocumentParser


class RemoteDocumentParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = UnifiedDocumentParser()

    def test_build_document_content_from_markdown(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_file.write(b"dummy")
            temp_path = Path(temp_file.name)

        try:
            markdown = "\n".join(
                [
                    "# Title",
                    "",
                    "First paragraph line",
                    "Second paragraph line",
                    "",
                    "| Name | Value | Notes |",
                    "| --- | --- | --- |",
                    "| A | 1 | ok |",
                    "",
                    "![diagram](https://example.com/img.png)",
                ]
            )

            result = self.parser._build_document_content_from_markdown(
                markdown=markdown,
                file_path=temp_path,
                file_extension=".docx",
                remote_images=[{"url": "https://example.com/img.png", "filename": "diagram"}],
            )

            self.assertIsInstance(result, DocumentContent)
            self.assertEqual(result.file_info["source"], "remote_api")
            self.assertEqual(len(result.paragraphs), 2)
            self.assertEqual(result.paragraphs[0]["type"], "heading")
            self.assertEqual(len(result.tables), 1)
            self.assertEqual(len(result.images), 1)
            self.assertIn("Title", result.markdown_content)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_parse_file_prefers_remote_parser_for_supported_documents(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_file.write(b"dummy")
            temp_path = Path(temp_file.name)

        remote_result = DocumentContent(
            paragraphs=[],
            tables=[],
            images=[],
            metadata={"parser_source": "remote_api"},
            structure={},
            markdown_content="# ok",
            file_info={"format": "docx"},
        )

        try:
            with patch.object(self.parser, "_parse_via_remote_api", return_value=remote_result) as remote_mock:
                result = self.parser.parse_file(temp_path)

            self.assertIs(result, remote_result)
            remote_mock.assert_called_once()
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
