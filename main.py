from OAuth_token import OAuth_token_vk
from ya_token import QAuth_TOKEN_ya
import vk_api
import yandex_api


if __name__ == '__main__':
    vk = vk_api.VKUser(OAuth_token_vk)
    ya_dick = yandex_api.YandexDisc(QAuth_TOKEN_ya)

    photo = vk.get_photoVK(id_vk='325379352')
    ya_dick.upload_photo_disk(photo)



