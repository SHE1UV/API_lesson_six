import requests
import os
import random
from dotenv import load_dotenv
from urllib.parse import urlencode

MAX_COMIC_NUM = 2500

def check_vk_response(response):
    json_response = response.json()
    if 'error' in json_response:
        error_code = json_response['error']['error_code']
        error_msg = json_response['error']['error_msg']
        raise requests.HTTPError(f"VK API Error {error_code}: {error_msg}")

    return json_response


def download_comic_image(img_url, file_name):
    response = requests.get(img_url)
    response.raise_for_status()

    with open(file_name, "wb") as file:
        file.write(response.content)


def get_random_xkcd_comic():
    random_comic_number = random.randint(1, MAX_COMIC_NUM)
    xkcd_url = f"https://xkcd.com/{random_comic_number}/info.0.json"
    response = requests.get(xkcd_url)
    response.raise_for_status()
    return response.json()


def upload_to_vk(file_name, vk_group_id, vk_token):
    vk_upload_url = "https://api.vk.com/method/photos.getWallUploadServer"
    params = {
        'group_id': vk_group_id,
        'access_token': vk_token,
        'v': '5.131'
    }
    
    response = requests.get(vk_upload_url, params=params)
    response.raise_for_status()
    check_vk_response(response)
    upload_server = response.json()
    upload_url = upload_server["response"]["upload_url"]

    with open(file_name, "rb") as file:
        files = {'photo': file}
        upload_response = requests.post(upload_url, files=files)
        
    upload_response.raise_for_status()

    upload_details = check_vk_response(upload_response)
    server = upload_details['server']
    photo = upload_details['photo']
    hash_value = upload_details['hash']

    vk_photo_save_url = "https://api.vk.com/method/photos.saveWallPhoto"
    params = {
        "access_token": vk_token,
        "server": server,
        "photo": photo,
        "hash": hash_value,
        "group_id": vk_group_id,
        "v": "5.131"
    }

    response = requests.post(vk_photo_save_url, params=params)
    response.raise_for_status()
    photo_details = check_vk_response(response)

    owner_id = photo_details['response'][0]['owner_id']
    photo_id = photo_details['response'][0]['id']
    return owner_id, photo_id


def post_to_wall(owner_id, photo_id, alt_text, vk_token, vk_group_id):
    url = "https://api.vk.com/method/wall.post"
    params = {
        "access_token": vk_token,
        "owner_id": f"-{vk_group_id}",
        "from_group": 1,
        "attachments": f"photo{owner_id}_{photo_id}",
        "message": alt_text,
        "v": "5.131"
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    post_info = check_vk_response(response)


def main():
    load_dotenv()
    vk_group_id = os.environ['VK_GROUP_ID']
    vk_token = os.environ['VK_TOKEN']

    file_name = None  

    try:
        selected_comic = get_random_xkcd_comic()
        img_url = selected_comic["img"]
        file_name = f"{selected_comic['title']}.png"

        download_comic_image(img_url, file_name)

        owner_id, photo_id = upload_to_vk(file_name, vk_group_id, vk_token)

        alt_text = selected_comic['alt']

        post_to_wall(owner_id, photo_id, alt_text, vk_token, vk_group_id)

    except requests.exceptions.RequestException as request_exception:
        print(f"Request exception occurred: {request_exception}")
    except requests.exceptions.HTTPError as http_error:
        print(f"HTTP error occurred: {http_error}")
    except KeyError as key_error:
        print(f"Key error occurred: {key_error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if file_name is not None:
            os.remove(file_name)


if __name__ == "__main__":
    main()
