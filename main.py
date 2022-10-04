from OAuth_token import OAuth_token_vk
from ya_token import QAuth_TOKEN_ya
import vk_api


if __name__ == '__main__':
    vk = vk_api.VKUser(OAuth_token_vk)
    vk.import_photoVK_in_yandex(QAuth_TOKEN_ya)

