import requests
import easygui
from tqdm import tqdm
import time
import json
from sys import exit
from loguru import logger
from os import path
logger.add('logfile.log', format='{time} {level} {message}')


def write_json(file_name, new_json):
    file_name = f'{file_name}.json'
    if path.exists(file_name):
        with open(file_name, 'r') as file:
            data = json.load(file)
            data.extend(new_json)
            with open(file_name, 'w') as outfile:
                json.dump(data, outfile, indent=4)
                logger.info(f'Update file {file_name}')
    else:
        with open(file_name, 'w') as outfile:
            json.dump(new_json, outfile, indent=4)
            logger.info(f'Create file {file_name}')


class YandexDisc:
    def __init__(self, token):
        self.token = token

    def _get_headers(self):
        res = {'Content-type': 'application/json',
               'Authorization': f'OAuth {self.token}'}
        return res

    def get_files_list(self):
        files_url = 'https://cloud-api.yandex.net/v1/disk/resources/files'
        headers = self._get_headers()
        response = requests.get(files_url, headers=headers)
        files_info = response.json()
        files_download = []
        for files_name in files_info['items']:
            files_download.append([files_name['name'], files_name['file']])
        return files_download

    def get_meta_info_files(self, path):
        params = {'path': path}
        files_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self._get_headers()
        response = requests.get(files_url, headers=headers, params=params)
        if response:
            return True

    def create_folder(self, new_path_folder):
        create_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self._get_headers()
        params = {'path': new_path_folder}
        response = requests.put(create_url, headers=headers, params=params)
        if 100 < response.status_code < 300:
            res = response.json()
            return res
        else:
            print(f'Error: {response.status_code}')
            exit(1)

    def copy_file(self, from_path, in_path):
        copy_url = 'https://cloud-api.yandex.net/v1/disk/resources/copy'
        headers = self._get_headers()
        params = {'from': from_path, 'path': in_path, 'overwrite': 'true'}
        response = requests.post(copy_url, headers=headers, params=params)
        if response:
            print('Файл успешно скопирован')
            return
        else:
            print('error:', response.status_code)
            return

    def _get_upload_link(self, disk_file_path):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self._get_headers()
        params = {'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=headers, params=params)
        if response:
            res = response.json()
            return res['href']
        else:
            print(f'Error: {response.status_code}')
            exit(1)

    def upload_file_disk(self, disk_file_path, open_file_pc):
        href = self._get_upload_link(disk_file_path=disk_file_path)
        response = requests.put(href, data=open(open_file_pc, 'rb'))
        if response:
            print('Загрузка прошла успешно')
            return
        else:
            print('Error:', response.status_code)
            exit(1)

    def upload_url_disk(self, disk_file_path, url):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self._get_headers()
        upload_url_params = {'url': url,
                             'path': disk_file_path}
        response = requests.post(upload_url, headers=headers, params=upload_url_params)
        if response:
            return
        else:
            logger.info(f'Error: {response.status_code}')
            exit(1)

    def upload_photo_disk(self, photo):
        if photo:
            data_for_json = []
            folder_path = input('Введите название папки для загрузки фото... --> ')

            for data in tqdm(photo, desc='Загрузка фото ', unit=' photo', unit_scale=1, leave=False, colour='green'):
                time.sleep(0.2)
                data_for_json.append({'file_id': data[0],
                                      'file_likes': f'{data[2]}.jpg',
                                      'size': data[3]})
                if not self.get_meta_info_files(folder_path):
                    self.create_folder(folder_path)
                disk_file_path = f'{folder_path}/{data[0]}.jpg'
                self.upload_url_disk(disk_file_path, data[1])

            logger.info('Photo upload in ya_disc')
            write_json(f'{folder_path}', data_for_json)
        else:
            logger.info('Error: photo None')
            exit(1)

    def uploads_file_disk(self):
        open_file = easygui.fileopenbox()
        folder_path = input('Введите название папки Яндекс.Диск... ')
        if not self.get_meta_info_files(folder_path):
            self.create_folder(folder_path)
        file_name = [i for i in open_file.split('\\')]
        disk_file_path = f'{folder_path}/{file_name[-1]}'
        self.upload_file_disk(disk_file_path, open_file)
