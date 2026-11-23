"""HTTP connection shared by Social's terminal features."""
import json
import socket
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = os.environ.get("SOCIAL_API_URL", "https://social.xylin48.site").rstrip("/")


class SocialAPI:
    def __init__(self, base_url=API_URL):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def request(self, path, method="GET", payload=None):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            with urlopen(Request(self.base_url + path, data=data, headers=headers, method=method), timeout=15) as response:
                try:
                    return json.load(response)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise ValueError("Social server returned an invalid response") from exc
        except HTTPError as exc:
            try:
                message = json.load(exc).get("error", str(exc))
            except Exception:
                message = str(exc)
            raise ValueError(message) from exc
        except (URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
            detail = getattr(exc, "reason", exc)
            raise ValueError("Cannot connect to Social server: " + str(detail)) from exc
