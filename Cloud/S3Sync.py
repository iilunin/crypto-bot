import hashlib
import logging
import traceback
from threading import Thread
from typing import List

import boto3
import botocore
from botocore import client
from botocore.response import StreamingBody
import os
from os import path, listdir
from os.path import join, isfile


class BotThread(Thread):
    def __init__(self, fn, *args, **kvargs):
        Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kvargs = kvargs

    def run(self):
        self.fn(*self.args, **self.kvargs)

class S3Persistence:
    def __init__(self, bucket, mapping: {}):

        if not bucket:
            raise ValueError('bucket cannot be empty')

        self.logger = logging.getLogger(__class__.__name__)
        self.bucket = bucket
        self.mapping = mapping
        self.thread = None

    def sync(self, resolve_conflict_using_local=True, delete=False):
        self.await()

        self.thread = BotThread(self.__sync_thread, resolve_conflict_using_local, delete)
        self.thread.name = 'S3 Sync'

        self.thread.start()

    def await(self):
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def __sync_thread(self, resolve_conflict_using_local=True, delete=True):
        try:
            self.logger.info('S3 Sync started. Delete: {}, Direction: {}'.format(delete,
                                                                                 'UP' if resolve_conflict_using_local else 'DOWN'))

            session = boto3.session.Session()
            s3 = session.resource('s3')
            bucket: s3.Bucket = s3.Bucket(self.bucket)

            # sym, _ = os.path.splitext(os.path.basename(file))

            for local_folder, s3_prefix in self.mapping.items():

                local_files = {f: self.get_md5(join(local_folder, f)) for f in listdir(local_folder) if
                         isfile(join(local_folder, f)) and f.lower().endswith('json')}


                items = bucket.objects.filter(Delimiter='/', Prefix=s3_prefix)

                remote_files = {path.basename(item.key): item.e_tag.strip('"') for item in items if
                                item.key.lower().endswith('json')}

                l_keys = set(local_files.keys())
                r_keys = set(remote_files.keys())
                common_keys = l_keys & r_keys

                local_files_missing_from_remote = set(local_files.keys()) - set(remote_files.keys())
                remote_files_missing_from_local = set(remote_files.keys()) - set(local_files.keys())
                common_changed_files = set()

                for key in common_keys:
                    if local_files[key] != remote_files[key]:
                        common_changed_files.add(key)

                if delete:
                    if resolve_conflict_using_local and remote_files_missing_from_local: # delete remote files which are not available locally
                        del_obj = {
                            'Objects': [{'Key': s3_prefix + key} for key in remote_files_missing_from_local],
                            'Quiet': True
                        }
                        bucket.delete_objects(Delete=del_obj)
                        remote_files_missing_from_local.clear()
                    else: # delete local files which are not available remotely
                        for file in local_files_missing_from_remote:
                            os.remove(join(local_folder, file))
                        local_files_missing_from_remote.clear()

                # download
                if not resolve_conflict_using_local: # download changed files from remote and ignore local changes
                    remote_files_missing_from_local |= common_changed_files

                for file in remote_files_missing_from_local:
                    bucket.download_file(s3_prefix+file, join(local_folder, file))

                # upload
                if resolve_conflict_using_local: # upload changed files from local and ignore remote changes
                    local_files_missing_from_remote |= common_changed_files

                for file in local_files_missing_from_remote:
                    bucket.upload_file(join(local_folder, file), s3_prefix+file)

        except Exception as e:
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.info('S3 Sync completed')




    def get_md5(self, filename):
        m = hashlib.md5()
        with open(filename, 'rb') as f:
            while True:
                data = f.read(4096)
                if len(data) == 0:
                    break

                m.update(data)
        return m.hexdigest()




