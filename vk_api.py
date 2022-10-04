import time
import requests
import yandex_api
import json
from tqdm import tqdm
from loguru import logger


logger.add('logfile.log', format='{time} {level} {message}')


def write_json(file_name, new_json):
    file_name = f'{file_name}.json'
    with open(file_name, 'a') as outfile:
        json.dump(new_json, outfile, indent=4)
        logger.info(f'Create file {file_name}')


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
        res = requests.get(url_get_albums, params={**self.params, **get_albums_params}).json()
        return [[i['id'], i['size']] for i in res['response']['items']]

    def _processing_photo(self, owner_id=None, extended=0, y=None):
        albums = self._get_all_albums(owner_id=owner_id)
        url_get_followers = self.url + 'photos.get'
        all_photos = []
        for album, count in tqdm(albums, desc='Получение данных о фото-альбомах', unit=' id_albums', unit_scale=1, leave=False, colour='green'):
            time.sleep(0.33)
            get_followers_params = {'owner_id': owner_id,
                                    'album_id': album,
                                    'extended': '1',
                                    'count': count}
            res = requests.get(url_get_followers, params={**self.params, **get_followers_params}).json()
            if 'error' not in res.keys():
                all_photos.append(res['response']['items'])
        return all_photos

    def get_all_photos(self, owner_id=None, extended=0, y=None):
        all_photos = []
        photos = self._processing_photo(owner_id=owner_id, extended=extended, y=y)
        for i in range(len(photos)):
            for photo in photos[i]:
                all_photos.append([{'file_id': photo['id'],
                                    'file_likes': photo['likes']['count'],
                                    'file_size_url': [max(photo['sizes'], key=lambda size: size['type'])]}])
        return all_photos

    def import_photoVK_in_yandex(self, ya_token, id_vk=None, count=5, extended=0, y=None):
        """
        :param ya_token: - OAuth - токен яндекс диска
        :param id_vk: - id - пользователя вк
        :param count: - количество фото, доступное для загрузки, по умолчанию 5
        :param extended: 1 - получение расширенной информации, по умолчанию 0
        """
        ya_disk = yandex_api.YandexDisc(ya_token)
        photos = self.get_all_photos(owner_id=id_vk, extended=extended, y=y)
        data_urls = []
        data_for_json = []

        for qty_photo in tqdm(range(count), desc='Загрузка данных о фото', unit=' id_albums', unit_scale=1, leave=False, colour='green'):
            time.sleep(0.33)
            for photo in photos[qty_photo]:
                data_urls.append([photo['file_id'],
                                  photo['file_size_url'][0]['url'],
                                  photo['file_likes'],
                                  photo['file_size_url'][0]['type']])

        folder_path = input('Введите название папки для загрузки фото... --> ')

        for data in tqdm(data_urls, desc='Загрузка фото', unit=' photo', unit_scale=1, leave=False, colour='green'):
            time.sleep(0.2)
            data_for_json.append({'file_id': data[0],
                                  'file_likes': f'{data[2]}.jpg',
                                  'size': data[3]})
            if not ya_disk.get_meta_info_files(folder_path):
                ya_disk.create_folder(folder_path)
            disk_file_path = f'{folder_path}/{data[0]}.jpg'
            ya_disk.upload_url_disk(disk_file_path, data[1])

        write_json(f'{folder_path}', data_for_json)
        print('Фото успешно загружены')

    # def newsfeed_search(self, q, extended=1):
    #     news_url = self.url + 'newsfeed.search'
    #     new_params = {'q': q,
    #                   'count': 200}
    #     newsfeed = pd.DataFrame()
    #     while True:
    #         result = requests.get(news_url, params={**self.params, **new_params})
    #         time.sleep(0.33)
    #         newsfeed = pd.concat([newsfeed, pd.DataFrame(result.json()['response']['items'])])
    #         if 'next_from' in result.json()['response']:
    #             new_params['start_from'] = result.json()['response']['next_from']
    #         else:
    #             break
    #     return newsfeed
