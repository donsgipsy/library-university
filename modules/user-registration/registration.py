"""Регистрация по телефону; хранилище и SMS-шлюз передаются снаружи."""

import re
import secrets
import time
from dataclasses import dataclass


class RegistrationError(Exception):
    """Ошибка ввода или выполнения регистрации."""


class SmsError(Exception):
    """SMS-шлюз не смог отправить сообщение."""


class InvalidPhoneError(SmsError):
    """SMS-шлюз сообщил, что номер недействителен."""


@dataclass(frozen=True)
class User:
    id: int
    phone: str
    role: str = "Читатель"


@dataclass(frozen=True)
class Session:
    token: str
    user: User


@dataclass
class Challenge:
    code: str
    expires_at: float


class RegistrationService:
    def __init__(self, sms_gateway, clock=time.time):
        self.sms_gateway = sms_gateway
        self.clock = clock
        self.users = {}
        self.challenges = {}
        self.failures = {}
        self.locked_until = {}
        self.sessions = {}
        self.next_id = 1

    @staticmethod
    def validate_phone(phone):
        if not isinstance(phone, str) or not re.fullmatch(r"\+[1-9][0-9]{7,14}", phone):
            raise RegistrationError("Введите номер телефона в международном формате, например +79991234567")

    def _check_lock(self, phone):
        until = self.locked_until.get(phone, 0)
        if self.clock() < until:
            raise RegistrationError("Ввод кода заблокирован на 15 минут после пяти ошибок")
        if until:
            self.locked_until.pop(phone, None)
            self.failures.pop(phone, None)

    def request_code(self, phone):
        self.validate_phone(phone)
        if phone in self.users:
            raise RegistrationError("Номер уже зарегистрирован. Выполните вход")
        self._check_lock(phone)
        # Старый код становится недействительным даже при ошибке новой отправки.
        self.challenges.pop(phone, None)
        code = f"{secrets.randbelow(1_000_000):06d}"
        try:
            self.sms_gateway.send(phone, code)
        except InvalidPhoneError as exc:
            raise RegistrationError("Указанный номер телефона недействителен") from exc
        except SmsError as exc:
            raise RegistrationError("Не удалось отправить SMS. Попробуйте позже") from exc
        self.challenges[phone] = Challenge(code, self.clock() + 300)

    def confirm(self, phone, code):
        self.validate_phone(phone)
        if phone in self.users:
            raise RegistrationError("Номер уже зарегистрирован. Выполните вход")
        self._check_lock(phone)
        challenge = self.challenges.get(phone)
        if challenge is None:
            raise RegistrationError("Сначала запросите код подтверждения")
        if self.clock() >= challenge.expires_at:
            del self.challenges[phone]
            raise RegistrationError("Срок действия кода истёк. Запросите новый код")
        if not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code) or not secrets.compare_digest(code, challenge.code):
            self.failures[phone] = self.failures.get(phone, 0) + 1
            if self.failures[phone] >= 5:
                self.locked_until[phone] = self.clock() + 900
                raise RegistrationError("Ввод кода заблокирован на 15 минут после пяти ошибок")
            raise RegistrationError("Неверный код подтверждения. Попробуйте ещё раз")
        user = User(self.next_id, phone)
        self.next_id += 1
        self.users[phone] = user
        del self.challenges[phone]
        self.failures.pop(phone, None)
        session = Session(secrets.token_urlsafe(32), user)
        self.sessions[session.token] = session
        return session


class ConsoleSmsGateway:
    """Демонстрационный шлюз: реальная SMS не отправляется."""

    def send(self, phone, code):
        print(f"[Демонстрация SMS для {phone}] Код: {code}")


def main():
    service = RegistrationService(ConsoleSmsGateway())
    print("Регистрация читателя. Для выхода введите exit.")
    while True:
        phone = input("Номер телефона: ").strip()
        if phone.lower() == "exit":
            return
        try:
            service.request_code(phone)
            while True:
                code = input("Код из SMS (или новый для повторной отправки): ").strip()
                if code.lower() == "новый":
                    service.request_code(phone)
                    continue
                try:
                    session = service.confirm(phone, code)
                    print(f"Регистрация завершена: ID {session.user.id}, роль {session.user.role}. Сессия создана.")
                    return
                except RegistrationError as exc:
                    print(exc)
                    if phone not in service.challenges or phone in service.locked_until:
                        break
        except RegistrationError as exc:
            print(exc)


if __name__ == "__main__":
    main()
