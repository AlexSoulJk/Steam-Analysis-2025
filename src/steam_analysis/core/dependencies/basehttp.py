import requests
import time
from typing import Dict, Any
import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class HTTPClient(Protocol):
    def get(self, url: str, params: dict = None) -> dict: ...

    def post(self, url: str, data: dict = None) -> dict: ...


class RequestsClient:
    """Простой синхронный клиент на requests (базовый)"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })

    def get(self, url: str, params: dict = None, headers: dict = None) -> Dict[str, Any]:
        response = self.session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def post(self, url: str, data: dict = None, headers: dict = None) -> Dict[str, Any]:
        response = self.session.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()


class RequestsWithDelayClient:
    """Синхронный клиент с rate limiting"""

    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })

    def _ensure_delay(self):
        """Защита от слишком частых запросов"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        self.last_request_time = time.time()

    def get(self, url: str, params: dict = None, headers: dict = None) -> Dict[str, Any]:
        self._ensure_delay()
        logger.debug(f"GET {url}")

        response = self.session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def post(self, url: str, data: dict = None, headers: dict = None) -> Dict[str, Any]:
        self._ensure_delay()
        logger.debug(f"POST {url}")

        response = self.session.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()