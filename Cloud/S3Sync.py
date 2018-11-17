import json
import hashlib
import traceback
from threading import Thread

import boto3
import os
from os import path, listdir
from os.path import join, isfile

from Utils.Logger import Logger


class BotThread(Thread):
    def __init__(self, fn, *args, **kvargs):
        Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kvargs = kvargs

    def run(self):
        self.fn(*self.args, **self.kvargs)


class S3Persistence(Logger):
    def __init__(self, bucket, mapping: {}):
        super().__init__()

        if not bucket:
            raise ValueError('bucket cannot be empty')

        self.bucket = bucket
        self.mapping = mapping
        self.rev_mapping = {v: k for k, v in mapping.items()}
        self.queue_url = None
        self.queue_not_available = False
        self.thread = None
        self.uploaded_requests = {}

    def sync(self, resolve_conflict_using_local=True, delete=False):
        self.finish()

        self.thread = BotThread(self.__sync_thread, resolve_conflict_using_local, delete)
        self.thread.name = 'S3 Sync'

        self.thread.start()

    def finish(self):
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def check_s3_events(self):
        del_set, upd_set = set(), set()
        ret_val = (del_set, upd_set)

        if self.queue_not_available:
            return ret_val

        try:
            session = boto3.session.Session()

            deleted_files, updated_files = self.get_s3_deleted_and_updated_event_messages(session)

            if not updated_files and not deleted_files:
                return ret_val

            for k, _ in deleted_files.items():
                local_folder, file_name = self.get_local_path(k)

                if not local_folder:
                    continue

                full_path = join(local_folder, file_name)
                del_set.add(full_path)

                if os.path.exists(full_path):
                    os.remove(full_path)
                    # file_watch_list.pop(full_path, None)

            if updated_files:
                bucket = session.resource('s3').Bucket(self.bucket)

                for k, etag in updated_files.items():
                    local_folder, file_name = self.get_local_path(k)
                    full_path = join(local_folder, file_name)

                    if not os.path.exists(full_path) or self.get_md5(full_path) != etag:
                        bucket.download_file(k, full_path)
                        upd_set.add(full_path)
                        # file_watch_list[full_path] = os.stat(full_path).st_mtime

        except Exception:
            self.logError(traceback.format_exc())

        return ret_val

    def get_s3_deleted_and_updated_event_messages(self, session):
        EVT_OBJ_CREATED = 'ObjectCreated'
        EVT_OBJ_DELETED = 'ObjectRemoved'
        self.set_queue_url(session)
        sqs = session.resource('sqs')
        queue = sqs.Queue(self.queue_url)

        deleted_files = {}
        updated_files = {}

        for message in queue.receive_messages(MaxNumberOfMessages=10):
            # Get the custom author message attribute if it was set
            if message.body:

                msg = json.loads(message.body)

                for record in msg.get('Records', []):

                    event_name = record['eventName'].split(':', 1)[0]

                    if event_name in (EVT_OBJ_CREATED, EVT_OBJ_DELETED):
                        d = deleted_files if event_name == EVT_OBJ_DELETED else updated_files
                        s3obj = record['s3']['object']
                        key = s3obj['key']
                        etag = s3obj.get('eTag', 'DEL')

                        if self.check_upload_req(key, etag):
                            self.remove_upload_req(key, etag)
                            continue

                        d[key] = etag
                        self.logInfo('SQS: {}: {}'.format(event_name, key))

            message.delete()

        return deleted_files, updated_files

    def add_upload_req(self, key, etag):
        etag_list = self.uploaded_requests.get(key, [])
        self.uploaded_requests[key] = etag_list
        etag_list.append(etag)

    def check_upload_req(self, key, etag):
        if etag is None:
            return key in self.uploaded_requests[key]

        return etag in self.uploaded_requests.get(key, [])

    def remove_upload_req(self, key, etag):
        if etag is None:
            self.uploaded_requests.pop(key, None)
        else:
            self.uploaded_requests.get(key, []).remove(etag)

    def get_local_path(self, key):
        path, file_name = os.path.split(key)

        if not path:
            return None, file_name

        if not path.endswith('/'):
            path += '/'

        return self.rev_mapping.get(path, None), file_name

    def __sync_thread(self, resolve_conflict_using_local=True, delete=True):
        try:
            self.logInfo('S3 Sync started. Delete: {}, Direction: {}'.format(delete,
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
                    if resolve_conflict_using_local:  # delete remote files which are not available locally
                        if remote_files_missing_from_local:
                            del_obj = {
                                'Objects': [{'Key': s3_prefix + key} for key in remote_files_missing_from_local],
                                'Quiet': True
                            }
                            bucket.delete_objects(Delete=del_obj)
                            [self.add_upload_req(s3_prefix + key, 'DEL') for key in remote_files_missing_from_local]

                            remote_files_missing_from_local.clear()
                    else:  # delete local files which are not available remotely
                        for file in local_files_missing_from_remote:
                            file_path = join(local_folder, file)

                            if os.path.exists(file_path):
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
                    self.add_upload_req(s3_prefix+file, self.get_md5(join(local_folder, file)))
                    bucket.upload_file(join(local_folder, file), s3_prefix+file)

        except Exception as e:
            self.logError(traceback.format_exc())
        finally:
            self.logInfo('S3 Sync completed')

    def set_queue_url(self, session):
        if self.queue_url:
            return

        bucket_notification = session.resource('s3').BucketNotification(self.bucket)
        for qc in bucket_notification.queue_configurations:
            for q in session.resource('sqs').queues.all():
                if qc['QueueArn'] == q.attributes['QueueArn']:
                    self.queue_url = q.url
            break

        if not self.queue_url:
            self.queue_not_available = True

    def get_md5(self, filename):
        m = hashlib.md5()
        with open(filename, 'rb') as f:
            while True:
                data = f.read(4096)
                if len(data) == 0:
                    break

                m.update(data)
        return m.hexdigest()




