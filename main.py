import http
import os
from base64 import b64encode
from typing import Dict
from urllib.parse import quote

import requests
from requests import Request, Session
from requests.adapters import HTTPAdapter
from requests.auth import CONTENT_TYPE_FORM_URLENCODED
from yarl import URL


class BasicAuth(requests.auth.AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r: Request):
        r.headers["Authorization"] = "Basic " + self.token
        return r


class Admitad:
    API_URL = URL("https://api.admitad.com/")
    TOKEN_PATH = "token/"
    AUTH_PATH = "authorize/"
    DEEPLINK_URL = "deeplink/{website_id}/advcampaign/{campaign_id}/"
    COUPONS_URL = "coupons/"
    COUPON_URL = "coupons/{id}/"

    def __init__(self, client_id, client_secret: str, scopes: str):
        self.session = Session()
        self.session.mount(str(self.API_URL), HTTPAdapter(max_retries=5))
        user_data = self.get_oauth_token(client_id, client_secret, scopes)
        self.session.headers.update(
            {
                "Authorization": "Bearer " + user_data.get("access_token"),
                "Connection": "Keep-Alive",
            }
        )

    @staticmethod
    def encode_credentials(client_id, client_secret: str):
        return b64encode(
            "{}:{}".format(client_id, client_secret).encode()
        ).decode("utf-8")

    def get_oauth_token(self, client_id, client_secret, scopes: str):
        params = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "scope": scopes,
        }
        credentials = self.encode_credentials(client_id, client_secret)
        headers = {
            "Content-Type": CONTENT_TYPE_FORM_URLENCODED,
        }
        response = self.session.post(
            str(self.API_URL / self.TOKEN_PATH),
            data=params,
            headers=headers,
            auth=BasicAuth(credentials),
        )
        if response.status_code != http.HTTPStatus.OK:
            raise BaseException("Bad status code ", response.status_code)
        return response.json()

    def get_coupons(self, params: Dict):
        response = self.session.get(
            str(self.API_URL / self.COUPONS_URL), params=params
        )
        if response.status_code != http.HTTPStatus.OK:
            raise BaseException("Bad status code ", response.status_code)
        data = response.json()
        return data

    def generate_deeplink(self, website_id, campaign_id: int, ulp, subid: str):
        response = self.session.get(
            str(
                self.API_URL / self.DEEPLINK_URL.format(
                    website_id=website_id, campaign_id=campaign_id
                )
            ),
            params={"ulp": quote(ulp), "sibod": subid},
        )
        if response.status_code != http.HTTPStatus.OK:
            raise BaseException("Bad status code ", response.status_code)
        data = response.json()
        return data


if __name__ == "__main__":
    admitad = Admitad(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET"),
        "advcampaigns banners websites coupons deeplink_generator",
    )
    # тут получаем купон в c типом промокод, но в ответе промокода нет
    # нужно ли как-то отдельно получать промокод?
    coupons = admitad.get_coupons({"type": 1, "limit": 1, "region": "RU"})
    print(coupons.get("results"))

    # пытаемся сгенерить диплинку по доке
    # https://developers.admitad.com/ru/doc/api_ru/methods/deeplink/deeplink/
    # получаем 404
    admitad.generate_deeplink(
        22, 10, "https://admitad.com/some/", "AS32djkd31"
    )

