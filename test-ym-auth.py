# import re
# import tls_client
#
# # Твоя строка (я сохранил ее в переменную)
# cookie_str = """<RequestsCookieJar[<Cookie lah=2:1835806583.11759323.QtMUGJXPP_GpneFb.1N7ObCvFO7i1RyCupmq4chuDOPeOQOxQg020.JAkJPcOZChbXlOhmKs2pnA for .passport.yandex.ru/>, <Cookie mda2_beacon=1772734583757 for .passport.yandex.ru/>, <Cookie sessguard=1.1772734583.1772734583748:GSak1A:2ea1..3.500:1759374.OQILhftq.ZdSRSv7kXolTaqUqu7aN-oysQtc for .passport.yandex.ru/>, <Cookie L=VVhBWmVebUpbcmlcWmBvA3tHDXQJRQ17IBgWR1hG.1772734583.1751745.339467.4b16ed157ae52a340bb4d8be8ec20bde for .yandex.ru/>, <Cookie Session_id=3:1772734583.5.0.1772734583748:GSak1A:2ea1.1.2:1|1553641783.-1.2.3:1772734583.6:2212690806.7:1772734583|3:11759293.785089.d9JdHKCDC_zQsxUHnc4gkKU-2SM for .yandex.ru/>, <Cookie sessar=1.1719226.CiB1y-Fbkm18-0-oRBPu2Vi-miv4C-CnrbA6bHiVc_Nz2Q.VHHfg1lKLubdXbCnxjHPVTD8QeE5ClxA5ga9P_3bWe4 for .yandex.ru/>, <Cookie sessionid2=3:1772734583.5.0.1772734583748:GSak1A:2ea1.1.2:1|1553641783.-1.2.3:1772734583.6:2212690806.7:1772734583|3:11759293.785089.fakesign0000000000000000000 for .yandex.ru/>, <Cookie yandex_login=Fugu95 for .yandex.ru/>, <Cookie yp=2088094583.udn.cDpGdWd1OTU%3D for .yandex.ru/>, <Cookie ys=udn.cDpGdWd1OTU%3D for .yandex.ru/>]>"""
#
# session = tls_client.Session(client_identifier="chrome_120")
#
# # Регулярка ищет паттерн Name=Value и Domain
# # Находит: (имя)=(значение) ... for (домен)
# matches = re.findall(r"Cookie ([^=]+)=([^\s]+) for ([^/]+)/", cookie_str)
#
# for name, value, domain in matches:
#     session.cookies.set(name, value, domain=domain)
#
# print(f"Загружено кук: {len(session.cookies)}")
#
#
# import requests
#
# headers = {
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#     'Accept-Language': 'ru',
#     'Cache-Control': 'no-cache',
#     'Connection': 'keep-alive',
#     'Pragma': 'no-cache',
#     'Sec-Fetch-Dest': 'document',
#     'Sec-Fetch-Mode': 'navigate',
#     'Sec-Fetch-Site': 'none',
#     'Sec-Fetch-User': '?1',
#     'Upgrade-Insecure-Requests': '1',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
#     'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
# }
#
# params = {
#     'response_type': 'token',
#     'client_id': '23cabbbdc6cd418abb4b39c32c41195d',
# }
#
# req = session.get('https://oauth.yandex.ru/authorize', params=params, headers=headers)
# print(req.cookies)
# print(req.text)
# print(req)
# exit()
import json
import time

import tls_client
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel


class SendCodePayload(BaseModel):
    phone_number: str
    csrf: str
    process_uuid: str
    track_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
ym_auth_router = APIRouter(prefix="/ym-auth")

@ym_auth_router.get('/create_auth_session')
def read_users():
    session = tls_client.Session(random_tls_extension_order=True)
    headers = {
        'Host': 'passport.yandex.ru',
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Priority': 'u=0, i',
        'Connection': 'keep-alive',
    }

    params = {
        'retpath': 'https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d',
        'noreturn': '1',
        'origin': 'oauth',
    }

    # GET CSRF AND PROCESS_UUID
    req = session.get('https://passport.yandex.ru/auth', params=params, headers=headers, allow_redirects=True)
    if 'process_uuid=' not in req.url:
        return {'status': False, 'error': 'Captcha, pass proxy or `parse_proxy=true` parameter'}
    print(req)
    print(req.url)
    csrf = req.text.split('__CSRF__ = "')[1].split('"')[0]
    process_uuid = req.text.split('process_uuid=')[1].split("'")[0]
    print('csrf', csrf)
    print('process_uuid', process_uuid)
    print(session.cookies)
    print(('='*30)+'\n')


    headers = {
        'Host': 'passport.yandex.ru',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'X-Csrf-Token': csrf,
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'C11n': 'yandex_phone_flow',
        'Tractor-Location': '0',
        'Sec-Ch-Ua-Mobile': '?0',
        'Tractor-Non-Proxy': '1',
        'Sec-Ch-Prefers-Color-Scheme': 'dark',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Process-Uuid': process_uuid,
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://passport.yandex.ru',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://passport.yandex.ru/',
        'Priority': 'u=1, i',
    }

    json_data = {
        'display_language': 'ru',
        'language': 'ru',
        'country': 'ru',
        'app_id': '',
        'app_version_name': '',
        'retpath': 'https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d',
        'device_id': '',
        'uid': '',
        'device_connection_type': '',
        'origin': 'oauth',
    }

    # GET TRACK_ID
    req = session.post(
        'https://passport.yandex.ru/pwl-yandex/api/passport/track/create',
        headers=headers,
        json=json_data,
    )
    print(req)
    track_id = req.json()['id']
    print('track_id', track_id)
    print(('='*30)+'\n')



    headers = {
        'Host': 'passport.yandex.ru',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'X-Csrf-Token': csrf,
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'C11n': 'yandex_phone_flow',
        'Tractor-Location': '0',
        'Sec-Ch-Ua-Mobile': '?0',
        'Tractor-Non-Proxy': '1',
        'Sec-Ch-Prefers-Color-Scheme': 'dark',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Process-Uuid': process_uuid,
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://passport.yandex.ru',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://passport.yandex.ru/',
        'Priority': 'u=1, i',
    }

    json_data = {
        'phone_number': '79950105861',
        'track_id': track_id,
        'can_use_anmon': True,
        'force_show_code_in_notification': '1',
        'country': 'ru',
    }

    # SEND CODE
    req = session.post(
        'https://passport.yandex.ru/pwl-yandex/api/passport/auth/suggest-send-push',
        headers=headers,
        json=json_data,
    )

    print(req)
    print(req.text)
    print(('='*30)+'\n')

    return {
        'csrf': csrf,
        'process_uuid': process_uuid,
        'track_id': track_id,
        'resp': req.json()
    }

@ym_auth_router.post('/send_code')
def send_code(payload: SendCodePayload):
    session = tls_client.Session(random_tls_extension_order=True)

    headers = {
        'Host': 'passport.yandex.ru',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'X-Csrf-Token': payload.csrf,
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'C11n': 'yandex_phone_flow',
        'Tractor-Location': '0',
        'Sec-Ch-Ua-Mobile': '?0',
        'Tractor-Non-Proxy': '1',
        'Sec-Ch-Prefers-Color-Scheme': 'dark',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Process-Uuid': payload.process_uuid,
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://passport.yandex.ru',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://passport.yandex.ru/',
        'Priority': 'u=1, i',
    }

    json_data = {
        'phone_number': payload.phone_number,
        'track_id': payload.track_id,
        'can_use_anmon': True,
        'force_show_code_in_notification': '1',
        'country': 'ru',
    }

    # SEND CODE
    req = session.post(
        'https://passport.yandex.ru/pwl-yandex/api/passport/auth/suggest-send-push',
        headers=headers,
        json=json_data,
    )

    print(req)
    print(req.text)
    print(('='*30)+'\n')
    return req.json()



app.include_router(ym_auth_router)

# if __name__ == '__main__':
#     uvicorn.run(app, port=9068)


phone_number = '+7 996 512 6914'
phone_number = '+7 9950105861'
ses = tls_client.Session(random_tls_extension_order=True)
headers = {
    'Host': 'passport.yandex.ru',
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Priority': 'u=0, i',
    'Connection': 'keep-alive',
}

params = {
    'retpath': 'https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d',
    'noreturn': '1',
    'origin': 'oauth',
}

# GET CSRF AND PROCESS_UUID
req = ses.get('https://passport.yandex.ru/auth', params=params, headers=headers, allow_redirects=True)
if 'process_uuid=' not in req.url:
    exit()
print(req)
print(req.url)
csrf = req.text.split('__CSRF__ = "')[1].split('"')[0]
process_uuid = req.text.split('process_uuid=')[1].split("'")[0]
print('csrf', csrf)
print('process_uuid', process_uuid)
print(ses.cookies)
print(('='*30)+'\n')


headers = {
    'Host': 'passport.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'X-Csrf-Token': csrf,
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'C11n': 'yandex_phone_flow',
    'Tractor-Location': '0',
    'Sec-Ch-Ua-Mobile': '?0',
    'Tractor-Non-Proxy': '1',
    'Sec-Ch-Prefers-Color-Scheme': 'dark',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Process-Uuid': process_uuid,
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://passport.yandex.ru',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=1, i',
}

json_data = {
    'display_language': 'ru',
    'language': 'ru',
    'country': 'ru',
    'app_id': '',
    'app_version_name': '',
    'retpath': 'https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d',
    'device_id': '',
    'uid': '',
    'device_connection_type': '',
    'origin': 'oauth',
}

# GET TRACK_ID
req = ses.post(
    'https://passport.yandex.ru/pwl-yandex/api/passport/track/create',
    headers=headers,
    json=json_data,
)
print(req)
track_id = req.json()['id']
print('track_id', track_id)
print(('='*30)+'\n')

# headers = {
#     'Host': 'passport.yandex.ru',
#     'Pragma': 'no-cache',
#     'Cache-Control': 'no-cache',
#     'Sec-Ch-Ua-Platform': '"Windows"',
#     'X-Csrf-Token': csrf,
#     'Accept-Language': 'ru-RU,ru;q=0.9',
#     'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
#     'C11n': 'yandex_phone_flow',
#     'Tractor-Location': '0',
#     'Sec-Ch-Ua-Mobile': '?0',
#     'Tractor-Non-Proxy': '1',
#     'Sec-Ch-Prefers-Color-Scheme': 'dark',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
#     'Process-Uuid': process_uuid,
#     'Content-Type': 'application/json',
#     'Accept': '*/*',
#     'Origin': 'https://passport.yandex.ru',
#     'Sec-Fetch-Site': 'same-origin',
#     'Sec-Fetch-Mode': 'cors',
#     'Sec-Fetch-Dest': 'empty',
#     'Referer': 'https://passport.yandex.ru/',
#     'Priority': 'u=1, i',
# }
#
# json_data = {
#     'phone_number': phone_number,
#     'country': 'ru',
#     'track_id': track_id,
# }
#
#
# req = ses.post(
#     'https://passport.yandex.ru/pwl-yandex/api/passport/validate/phone_number',
#     headers=headers,
#     json=json_data,
# )
#
# print(req)
# print(req.text)
# print(('='*30)+'\n')



headers = {
    'Host': 'passport.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'X-Csrf-Token': csrf,
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'C11n': 'yandex_phone_flow',
    'Tractor-Location': '0',
    'Sec-Ch-Ua-Mobile': '?0',
    'Tractor-Non-Proxy': '1',
    'Sec-Ch-Prefers-Color-Scheme': 'dark',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Process-Uuid': process_uuid,
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://passport.yandex.ru',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=1, i',
}

json_data = {
    'phone_number': phone_number,
    'track_id': track_id,
    'can_use_anmon': True,
    'force_show_code_in_notification': '1',
    'country': 'ru',
}

# json_data = {
#     'number': phone_number,
#     'track_id': track_id,
#     'display_language': 'ru',
#     'gps_package_name': '',
#     'force_check_for_protocols': True,
#     'country': 'ru',
#     'code_format': 'by_3_dash',
#     'transport': 'by_telegram',
# }

# SEND CODE
req = ses.post(
    'https://passport.yandex.ru/pwl-yandex/api/passport/auth/suggest-send-push',
    # 'https://passport.yandex.ru/pwl-yandex/api/passport/confirm_phone/submit',
    headers=headers,
    json=json_data,
)

print(req)
print(req.text)
print(('='*30)+'\n')

time.sleep(10)

headers = {
    'Host': 'passport.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'X-Csrf-Token': csrf,
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'C11n': 'yandex_phone_flow',
    'Tractor-Location': '0',
    'Sec-Ch-Ua-Mobile': '?0',
    'Tractor-Non-Proxy': '1',
    'Sec-Ch-Prefers-Color-Scheme': 'dark',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Process-Uuid': process_uuid,
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://passport.yandex.ru',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=1, i',
}

json_data = {
    'number': phone_number,
    'track_id': track_id,
    'display_language': 'ru',
    'gps_package_name': '',
    'force_check_for_protocols': True,
    'country': 'ru',
    'code_format': 'by_3_dash',
    'transport': 'by_telegram',
}

req = ses.post(
    'https://passport.yandex.ru/pwl-yandex/api/passport/confirm_phone/submit',
    headers=headers,
    json=json_data,
)
sent_to_tg = True

print(req)
print(req.text)
print(('='*30)+'\n')


while True:
    code = input('Enter code: ')


    headers = {
        'Host': 'passport.yandex.ru',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'X-Csrf-Token': csrf,
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'C11n': 'yandex_phone_flow',
        'Tractor-Location': '0',
        'Sec-Ch-Ua-Mobile': '?0',
        'Tractor-Non-Proxy': '1',
        'Sec-Ch-Prefers-Color-Scheme': 'dark',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Process-Uuid': process_uuid,
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://passport.yandex.ru',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://passport.yandex.ru/',
        'Priority': 'u=1, i',
    }

    json_data = {
        'code': code,
        'track_id': track_id,
    }

    url = f"https://passport.yandex.ru/pwl-yandex/api/{'passport/confirm_phone/commit' if sent_to_tg else 'passport/auth/check-push-code'}"
    # VERIFY PUSH CODE
    req = ses.post(
        url,
        headers=headers,
        json=json_data,
    )
    print(req)
    print(req.headers)
    print(req.text)
    print(('='*30)+'\n')

    if 'code.invalid' in req.text:
        continue
    break


headers = {
    'Host': 'passport.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'X-Csrf-Token': csrf,
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'C11n': 'yandex_phone_flow',
    'Tractor-Location': '0',
    'Sec-Ch-Ua-Mobile': '?0',
    'Tractor-Non-Proxy': '1',
    'Sec-Ch-Prefers-Color-Scheme': 'dark',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Process-Uuid': process_uuid,
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://passport.yandex.ru',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=1, i',
}

json_data = {
    'track_id': track_id,
    'can_use_anmon': True,
}

# GET ACCOUNTS
req = ses.post(
    'https://passport.yandex.ru/pwl-yandex/api/passport/suggest/by_phone',
    headers=headers,
    json=json_data,
)
print(req)
print(json.dumps(req.json(), indent=4, ensure_ascii=False))
print(('='*30)+'\n')



headers = {
    'Host': 'passport.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'X-Csrf-Token': csrf,
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'C11n': 'yandex_phone_flow',
    'Tractor-Location': '0',
    'Sec-Ch-Ua-Mobile': '?0',
    'Tractor-Non-Proxy': '1',
    'Sec-Ch-Prefers-Color-Scheme': 'dark',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Process-Uuid': process_uuid,
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://passport.yandex.ru',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=1, i',
}


uid = int(input('Enter uid: '))

json_data = {
    'track_id': track_id,
    'uid': uid,
}

# AUTH IN ACCOUNT
req = ses.post(
    'https://passport.yandex.ru/pwl-yandex/api/passport/suggest/select-by-phone',
    headers=headers,
    json=json_data,
)
print(req)
print(req.text)
print(('='*30)+'\n')


headers = {
    'Host': 'passport.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'X-Csrf-Token': csrf,
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'C11n': 'yandex_phone_flow',
    'Tractor-Location': '0',
    'Sec-Ch-Ua-Mobile': '?0',
    'Tractor-Non-Proxy': '1',
    'Sec-Ch-Prefers-Color-Scheme': 'dark',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Process-Uuid': process_uuid,
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://passport.yandex.ru',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=1, i',
}

json_data = {
    'track_id': track_id,
}

# GET SESSION
req = ses.post(
    'https://passport.yandex.ru/pwl-yandex/api/passport/sessions/get_session',
    headers=headers,
    json=json_data,
)
print(req)
print(req.headers)
print(req.text)
print(('='*30)+'\n')



print(ses.cookies)
headers = {
    'Host': 'oauth.yandex.ru',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://passport.yandex.ru/',
    'Priority': 'u=0, i',
    'Connection': 'keep-alive',
}

params = {
    'response_type': 'token',
    'client_id': '23cabbbdc6cd418abb4b39c32c41195d',
}

req = ses.get('https://oauth.yandex.ru/authorize', params=params, headers=headers)
if 'AuthorizeApp-account' in req.text:
    oauth_csrf = req.text.split('name="csrf" value="')[1].split('"')[0]
    request_id = req.text.split('name="request_id" value="')[1].split('"')[0]
    headers = {
        'Host': 'oauth.yandex.ru',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Sec-Ch-Ua': '"Chromium";v="145", "Not:A-Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Origin': 'https://oauth.yandex.ru',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d',
        'Priority': 'u=0, i',
        'Connection': 'keep-alive',
    }

    data = {
        'retpath': 'https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d',
        'clientId': '23cabbbdc6cd418abb4b39c32c41195d',
        'client_id': '23cabbbdc6cd418abb4b39c32c41195d',
        'csrf': oauth_csrf,
        'origin': 'oauth',
        'request_id': request_id,
        'redirect_uri': 'https://music.yandex.ru/',
        'granted_scopes': [
            'login:avatar',
            'login:birthday',
            'login:email',
            'login:info',
            'cloud_api.data:app_data',
            'cloud_api.data:user_data',
            'iot:view',
            'messenger:music',
            'mobile:all',
            'music:content',
            'music:read',
            'music:write',
            'passport:bind_email',
            'passport:bind_phone',
            'payments:all',
            'quasar:glagol',
            'social:broker',
            'yadisk:disk',
            'yastore:publisher',
        ],
    }

    req = ses.post('https://oauth.yandex.ru/authorize/allow', headers=headers, data=data)

print(req)
# print(req.text)
access_token = req.text.split('access_token=')[1].split('&')[0].strip()
print(access_token)