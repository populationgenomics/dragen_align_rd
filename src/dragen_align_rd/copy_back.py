import os
from argparse import ArgumentParser

from loguru import logger

from icasdk.apis.tags import project_data_api

from google.cloud import storage
from dragen_align_rd.ica_api_utils import get_ica_api_client, get_ica_secrets
from dragen_align_rd.ica_utils import list_and_filter_ica_files, stream_ica_file_to_gcs


"""
copy files back, using a CPG ID and an ICA workflow ID
"""

BATCH_TMP = os.environ.get('BATCH_TMPDIR', '/io')


parser = ArgumentParser()
parser.add_argument('--analysis_name')
parser.add_argument('--analysis_id')
parser.add_argument('--cpg_id')
parser.add_argument('--bucket')
args = parser.parse_args()


BUCKET = f'gs://cpg-{args.bucket}-test/'
OUTPUT_BUCKET_GCS = f'{BUCKET}ica/{args.cpg_id}/'

project_id = get_ica_secrets()['projectID']

secrets: dict[str, str] = get_ica_secrets()
path_parameters: dict[str, str] = {'projectId': secrets['projectID']}
base_ica_folder_path = f'/{args.bucket}/{args.cpg_id}/{args.analysis_name}-{args.analysis_id}'
storage_client = storage.Client()
gcs_bucket = storage_client.bucket(BUCKET)

with get_ica_api_client() as api_client:

    api_instance = project_data_api.ProjectDataApi(api_client)

    # --- List, filter, and download files ---
    files_to_download = list_and_filter_ica_files(
        api_instance=api_instance,
        path_parameters=path_parameters,
        base_ica_folder_path=base_ica_folder_path,
    )

    for file_name, file_id in files_to_download:
        logger.info(f'Preparing to download file: {file_name} (ID: {file_id})')
        stream_ica_file_to_gcs(
            api_instance=api_instance,
            path_parameters=path_parameters,
            file_id=file_id,
            file_name=file_name,
            gcs_bucket=gcs_bucket,
            gcs_prefix=f'ica/{args.cpg_id}/',
            expected_md5_hash=None,
        )
