import requests
import time
from typing import Dict, Any
import logging
from typing import Protocol

from steam_analysis.core.services.fastlogger import setup_logger

logger = setup_logger("RequestsWithDelayClient")


class HTTPClient(Protocol):
    def get(self, url: str, params: dict = None) -> dict: ...

    def post(self, url: str, data: dict = None) -> dict: ...


class RequestsClient(HTTPClient):
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


class RequestsWithDelayClient(HTTPClient):
    """Синхронный клиент с rate limiting"""
    ## 5 мин = 200 запросов ??
    count_of_request = 0
    MAX_REQUEST = 500
    last_request_time = 0
    interval_time = 180
    def __init__(self, delay: float = 0.1):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })

    def _ensure_delay(self):
        """Защита от слишком частых запросов"""
        current_time = time.time()

        if RequestsWithDelayClient.count_of_request == 0:
            RequestsWithDelayClient.last_request_time = current_time

        elif RequestsWithDelayClient.count_of_request - 1 == RequestsWithDelayClient.MAX_REQUEST:
            delay = current_time - RequestsWithDelayClient.last_request_time
            logger.info(f"Now we will sleep {RequestsWithDelayClient.interval_time - delay}")
            delta = max(RequestsWithDelayClient.interval_time - delay, 0)
            time.sleep(delta)
            RequestsWithDelayClient.last_request_time = time.time()
            RequestsWithDelayClient.count_of_request = 0

        RequestsWithDelayClient.count_of_request += 1

        if RequestsWithDelayClient.count_of_request % 20 == 0:
            logger.info(f"Count of requests {RequestsWithDelayClient.count_of_request}")

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