import unittest

from registration import InvalidPhoneError, RegistrationError, RegistrationService, SmsError


class Gateway:
    def __init__(self):
        self.code = None
        self.error = None

    def send(self, phone, code):
        if self.error:
            raise self.error
        self.code = code


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.gateway = Gateway()
        self.service = RegistrationService(self.gateway, lambda: self.now)
        self.phone = "+79991234567"

    def test_success_and_single_use(self):
        self.service.request_code(self.phone)
        self.assertEqual(len(self.gateway.code), 6)
        self.assertFalse(self.service.users)
        session = self.service.confirm(self.phone, self.gateway.code)
        self.assertEqual((session.user.id, session.user.role), (1, "Читатель"))
        self.assertIn(session.token, self.service.sessions)
        self.assertNotIn(self.phone, self.service.challenges)
        with self.assertRaises(RegistrationError):
            self.service.confirm(self.phone, self.gateway.code)

    def test_invalid_number_and_gateway_failure(self):
        with self.assertRaises(RegistrationError):
            self.service.request_code("123")
        for error in (SmsError(), InvalidPhoneError()):
            self.gateway.error = error
            with self.assertRaises(RegistrationError):
                self.service.request_code(self.phone)
            self.assertFalse(self.service.challenges)

    def test_expiry_boundary(self):
        self.service.request_code(self.phone)
        self.now += 300
        with self.assertRaisesRegex(RegistrationError, "истёк"):
            self.service.confirm(self.phone, self.gateway.code)
        self.assertFalse(self.service.users)
        self.assertFalse(self.service.challenges)

    def test_five_failures_lock_even_after_resend(self):
        self.service.request_code(self.phone)
        wrong = "000000" if self.gateway.code != "000000" else "111111"
        for _ in range(5):
            with self.assertRaises(RegistrationError):
                self.service.confirm(self.phone, wrong)
        with self.assertRaisesRegex(RegistrationError, "заблокирован"):
            self.service.request_code(self.phone)
        self.now += 900
        self.service.request_code(self.phone)
        self.assertEqual(self.service.confirm(self.phone, self.gateway.code).user.role, "Читатель")


if __name__ == "__main__":
    unittest.main()
