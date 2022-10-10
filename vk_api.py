import time
import requests
from tqdm import tqdm
from loguru import logger


class VKUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version='5.194'):
        self.params = {'access_token': token,
                       'v': version}

    def get_users(self, user_ids):
        # self.params['user_ids'] = user_ids
        # self.params['fields'] = 'education,sex'
        get_users_url = self.url + 'users.get'
        get_users_params = {'user_ids': user_ids,
                            'fields': 'education,sex'}
        res = requests.get(get_users_url, params={**self.params, **get_users_params})
        return res.json()

    def group_search(self, q, sorting=0):
        """
        Параметры sort
        0 - сортировать по умолчанию
        6 - сортировать по количеству пользователей
        """
        group_search_params = {
            'q': q,
            'sort': sorting,
            'count': 1
        }
        url_search_group = self.url + 'groups.search'
        res = requests.get(url_search_group, params={**self.params, **group_search_params}).json()
        return res['response']['items']

    def get_groups_info(self, q, sorting=0):
        groups = self.group_search(q=q, sorting=sorting)
        groups_id = ','.join([str(group['id']) for group in groups])
        url_groups_info = self.url + 'groups.getById'
        groups_info_params = {
            'group_ids': groups_id,
            'fields': 'members_count,activity,description'
        }
        res = requests.get(url_groups_info, params={**self.params, **groups_info_params}).json()
        return res['response']['groups']

    def get_groups_members(self, group_id, sort='id_asc'):
        url_get_groups_members = self.url + 'groups.getMembers'
        groups_members_params = {'group_id': group_id, 'fields': 'country,city,online,sex', 'sort': sort}
        res = requests.get(url_get_groups_members, params={**self.params, **groups_members_params}).json()
        return res

    def get_followers_users(self, user_id, count=20):
        url_get_followers = self.url + 'users.getFollowers'
        get_followers_params = {'user_id': user_id,
                                'count': count,
                                'fields': 'has_photo'}
        res = requests.get(url_get_followers, params={**self.params, **get_followers_params}).json()
        return res

    def get_groups(self, user_id=None):
        url_get_followers = self.url + 'groups.get'
        get_followers_params = {'user_id': user_id,
                                'extended': 1}
        res = requests.get(url_get_followers, params={**self.params, **get_followers_params}).json()
        return res

    def _get_all_albums(self, owner_id=None):
        """
        параметр owner_id: - id-пользователя ВК, по умолчанию используется id владельца токена
        """

        url_get_albums = self.url + 'photos.getAlbums'
        get_albums_params = {'owner_id': owner_id,
                             'need_system': 1}
        res = requests.get(url_get_albums, params={**self.params, **get_albums_params})
        if res:
            res = res.json()
            if 'error' not in res.keys():
                logger.info(f'Get info all albums user {owner_id}')
                return [[i['id'], i['size']] for i in res['response']['items']]
            else:
                logger.info(f'Error: {res["error"]["error_code"]}')
                return
        else:
            logger.info(f'Error: {res.status_code}')

    def _processing_photo(self, owner_id=None, extended=1):
        albums = self._get_all_albums(owner_id=owner_id)
        if albums:
            url_get_followers = self.url + 'photos.get'
            all_photos = []
            for album, count in tqdm(albums, desc='Получение данных о фото-альбомах', unit=' id_albums', unit_scale=1, leave=False, colour='green'):
                time.sleep(0.33)
                get_followers_params = {'owner_id': owner_id,
                                        'album_id': album,
                                        'extended': extended,
                                        'count': count}
                res = requests.get(url_get_followers, params={**self.params, **get_followers_params})
                if res:
                    res = res.json()
                    if 'error' not in res.keys():
                        all_photos.append(res['response']['items'])
                    else:
                        logger.info(f'Error: {res["error"]["error_code"]}')
                        return
                else:
                    logger.info(f'Error: {res.status_code}')
                    return
            return all_photos
        else:
            logger.info('Error: not data in albums')

    def get_all_photos(self, owner_id=None, extended=1):
        all_photos = []
        photos = self._processing_photo(owner_id=owner_id, extended=extended)
        if photos:
            for i in range(len(photos)):
                for photo in photos[i]:
                    all_photos.append([{'file_id': photo['id'],
                                        'file_likes': photo['likes']['count'],
                                        'file_size_url': [max(photo['sizes'], key=lambda size: size['type'])]}])
            return all_photos
        else:
            logger.info('Error: no data in photos')

    def get_photoVK(self, id_vk=None, count=5, extended=1):
        """
        :param id_vk: - id - пользователя вк
        :param count: - количество фото, доступное для загрузки, по умолчанию 5
        :param extended: 1 - получение расширенной информации, по умолчанию 0
        """
        photos = self.get_all_photos(owner_id=id_vk, extended=extended)
        if photos:
            data_urls = []

            for qty_photo in tqdm(range(count),
                                  desc='Загрузка данных о фото',
                                  unit=' id_albums',
                                  unit_scale=1,
                                  leave=False,
                                  colour='green'):
                time.sleep(0.33)
                for photo in photos[qty_photo]:
                    data_urls.append([photo['file_id'],
                                      photo['file_size_url'][0]['url'],
                                      photo['file_likes'],
                                      photo['file_size_url'][0]['type']])
            return data_urls
        else:
            logger.info('Error: no photo')



