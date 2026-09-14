import importlib.util
import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest import mock
import xml.etree.ElementTree as ElementTree

from twilio.request_validator import RequestValidator


PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
RECEIVE_FILE = PROJECT_DIRECTORY / "receive.py"
TEST_AUTH_TOKEN = "test_auth_token_not_a_real_credential"
TEST_WEBHOOK_URL = "https://grocery-demo.example/webhook"
DATABASE_FUNCTION_NAMES = ("add_item", "remove_item", "get_list", "clear_list")


class WebhookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database_module = types.ModuleType("database")
        for function_name in DATABASE_FUNCTION_NAMES:
            setattr(cls.database_module, function_name, mock.Mock(name=function_name))

        module_spec = importlib.util.spec_from_file_location(
            "receive_under_test", RECEIVE_FILE
        )
        if module_spec is None or module_spec.loader is None:
            raise RuntimeError("Could not load receive.py for testing")

        cls.receive_module = importlib.util.module_from_spec(module_spec)
        with mock.patch.dict(sys.modules, {"database": cls.database_module}):
            with mock.patch.dict(
                os.environ,
                {
                    "TWILIO_AUTH_TOKEN": TEST_AUTH_TOKEN,
                    "TWILIO_WEBHOOK_URL": TEST_WEBHOOK_URL,
                    "FLASK_DEBUG": "0",
                },
            ):
                module_spec.loader.exec_module(cls.receive_module)

    def setUp(self):
        self.application = self.receive_module.app
        self.application.config.update(
            TESTING=True,
            TWILIO_AUTH_TOKEN=TEST_AUTH_TOKEN,
            TWILIO_WEBHOOK_URL=TEST_WEBHOOK_URL,
        )
        self.client = self.application.test_client()
        self.validator = RequestValidator(TEST_AUTH_TOKEN)
        for function_name in DATABASE_FUNCTION_NAMES:
            database_function = getattr(self.database_module, function_name)
            database_function.reset_mock()
        self.database_module.get_list.return_value = []

    def post_signed_request(self, form_data, request_path="/webhook"):
        signature = self.validator.compute_signature(
            self.application.config["TWILIO_WEBHOOK_URL"], form_data
        )
        return self.client.post(
            request_path,
            base_url="http://127.0.0.1:5000",
            data=form_data,
            headers={"X-Twilio-Signature": signature},
        )

    def assert_no_database_calls(self):
        for function_name in DATABASE_FUNCTION_NAMES:
            getattr(self.database_module, function_name).assert_not_called()

    def get_reply_text(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        response_document = ElementTree.fromstring(response.data)
        self.assertEqual(response_document.tag, "Response")
        reply_text = response_document.findtext("Message")
        self.assertIsNotNone(reply_text)
        self.assertTrue(reply_text.strip())
        return reply_text

    def test_missing_configuration_fails_closed(self):
        for setting_name in ("TWILIO_AUTH_TOKEN", "TWILIO_WEBHOOK_URL"):
            for setting_value in (None, ""):
                with self.subTest(setting=setting_name, value=setting_value):
                    self.application.config.update(
                        TWILIO_AUTH_TOKEN=TEST_AUTH_TOKEN,
                        TWILIO_WEBHOOK_URL=TEST_WEBHOOK_URL,
                    )
                    self.application.config[setting_name] = setting_value
                    response = self.client.post(
                        "/webhook", data={"Body": "add milk"}
                    )
                    self.assertEqual(response.status_code, 503)
                    self.assert_no_database_calls()

    def test_invalid_webhook_configuration_fails_closed(self):
        invalid_webhook_urls = (
            "http://grocery-demo.example/webhook",
            "https:///webhook",
            "https://grocery-demo.example/other",
            "https://user:password@grocery-demo.example/webhook",
            "https://grocery-demo.example/webhook#fragment",
            "https://grocery-demo.example:invalid/webhook",
            "https://[invalid/webhook",
        )
        for webhook_url in invalid_webhook_urls:
            with self.subTest(webhook_url=webhook_url):
                self.application.config["TWILIO_WEBHOOK_URL"] = webhook_url
                response = self.client.post(
                    "/webhook", data={"Body": "add milk"}
                )
                self.assertEqual(response.status_code, 503)
                self.assert_no_database_calls()

    def test_missing_signature_is_rejected_before_database_access(self):
        response = self.client.post("/webhook", data={"Body": "add milk"})
        self.assertEqual(response.status_code, 403)
        self.assert_no_database_calls()

    def test_invalid_signature_is_rejected_before_database_access(self):
        signature_for_different_body = self.validator.compute_signature(
            TEST_WEBHOOK_URL, {"Body": "3"}
        )
        for signature in ("invalid-signature", signature_for_different_body):
            with self.subTest(signature=signature):
                response = self.client.post(
                    "/webhook",
                    data={"Body": "4"},
                    headers={"X-Twilio-Signature": signature},
                )
                self.assertEqual(response.status_code, 403)
                self.assert_no_database_calls()

    def test_valid_signed_add_works_through_local_http_tunnel(self):
        response = self.post_signed_request({"Body": "  ADD Milk  "})
        reply_text = self.get_reply_text(response)
        self.assertIn("milk", reply_text)
        self.database_module.add_item.assert_called_once_with("milk")
        self.database_module.remove_item.assert_not_called()
        self.database_module.get_list.assert_not_called()
        self.database_module.clear_list.assert_not_called()

    def test_query_string_mismatch_is_rejected(self):
        query_string_cases = (
            (TEST_WEBHOOK_URL, "/webhook?unexpected=1"),
            (TEST_WEBHOOK_URL + "?demo=1", "/webhook"),
            (TEST_WEBHOOK_URL + "?demo=1", "/webhook?demo=2"),
            (TEST_WEBHOOK_URL + "?demo=a%20b", "/webhook?demo=a+b"),
        )
        for webhook_url, request_path in query_string_cases:
            with self.subTest(webhook_url=webhook_url, request_path=request_path):
                self.application.config["TWILIO_WEBHOOK_URL"] = webhook_url
                response = self.post_signed_request(
                    {"Body": "4"}, request_path=request_path
                )
                self.assertEqual(response.status_code, 403)
                self.assert_no_database_calls()

    def test_matching_configured_query_string_accepts_valid_signature(self):
        self.application.config["TWILIO_WEBHOOK_URL"] = (
            TEST_WEBHOOK_URL + "?demo=1"
        )
        response = self.post_signed_request(
            {"Body": "3"}, request_path="/webhook?demo=1"
        )
        self.get_reply_text(response)
        self.database_module.get_list.assert_called_once_with()

    def test_missing_or_blank_body_returns_guidance_without_database_access(self):
        for form_data in ({}, {"Body": ""}, {"Body": "   "}):
            with self.subTest(form_data=form_data):
                response = self.post_signed_request(form_data)
                reply_text = self.get_reply_text(response)
                self.assertIn("add", reply_text.lower())
                self.assert_no_database_calls()

    def test_empty_item_commands_do_not_change_database(self):
        for command in ("add ", "remove "):
            with self.subTest(command=command):
                response = self.post_signed_request({"Body": command})
                self.get_reply_text(response)
                self.assert_no_database_calls()

    def test_remove_command_removes_named_item(self):
        response = self.post_signed_request({"Body": "remove milk"})
        self.assertIn("milk", self.get_reply_text(response))
        self.database_module.remove_item.assert_called_once_with("milk")
        self.database_module.add_item.assert_not_called()
        self.database_module.clear_list.assert_not_called()

    def test_show_list_returns_stored_items_as_xml(self):
        self.database_module.get_list.return_value = ["milk", "bread & butter"]
        response = self.post_signed_request({"Body": "3"})
        reply_text = self.get_reply_text(response)
        self.assertIn("milk", reply_text)
        self.assertIn("bread & butter", reply_text)
        self.database_module.get_list.assert_called_once_with()
        self.database_module.add_item.assert_not_called()
        self.database_module.remove_item.assert_not_called()
        self.database_module.clear_list.assert_not_called()

    def test_show_empty_list_returns_empty_message(self):
        response = self.post_signed_request({"Body": "3"})
        self.assertIn("empty", self.get_reply_text(response).lower())
        self.database_module.get_list.assert_called_once_with()

    def test_clear_command_clears_list(self):
        response = self.post_signed_request({"Body": "4"})
        self.get_reply_text(response)
        self.database_module.clear_list.assert_called_once_with()
        self.database_module.add_item.assert_not_called()
        self.database_module.remove_item.assert_not_called()

    def test_unknown_command_returns_menu_without_database_access(self):
        response = self.post_signed_request({"Body": "help"})
        reply_text = self.get_reply_text(response)
        self.assertIn("add", reply_text.lower())
        self.assertIn("remove", reply_text.lower())
        self.assert_no_database_calls()

    def test_direct_startup_disables_debug_and_binds_to_localhost(self):
        self.assertFalse(self.application.debug)
        with mock.patch.dict(sys.modules, {"database": self.database_module}):
            with mock.patch.dict(
                os.environ,
                {
                    "TWILIO_AUTH_TOKEN": TEST_AUTH_TOKEN,
                    "TWILIO_WEBHOOK_URL": TEST_WEBHOOK_URL,
                    "FLASK_DEBUG": "0",
                },
            ):
                with mock.patch("flask.Flask.run") as run_application:
                    runpy.run_path(str(RECEIVE_FILE), run_name="__main__")
        run_application.assert_called_once()
        self.assertEqual(run_application.call_args.kwargs["host"], "127.0.0.1")
        self.assertIs(run_application.call_args.kwargs.get("debug"), False)
        self.assert_no_database_calls()


if __name__ == "__main__":
    unittest.main()
