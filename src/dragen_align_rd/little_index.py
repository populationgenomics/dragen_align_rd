import os
from argparse import ArgumentParser
from typing import Iterator

from loguru import logger
from icasdk.model.create_data import CreateData
from icasdk.apis.tags import project_data_api

from icasdk import ApiClient, Configuration
from icasdk.exceptions import ApiException

from dragen_align_rd.utils import run_subprocess_with_log
from dragen_align_rd.ica_cli_utils import authenticate_ica_cli
from dragen_align_rd.ica_api_utils import get_ica_api_client, get_ica_secrets


BATCH_TMP = os.environ.get('BATCH_TMPDIR', '/io')


parser = ArgumentParser()
parser.add_argument('--bucket')
parser.add_argument('--sample')
args = parser.parse_args()


CRAM = f'gs://cpg-{args.bucket}-test/cram/{args.sample}.cram.crai'
LOCAL_NAME = f'{BATCH_TMP}/{args.sample}.cram.crai'

project_id = get_ica_secrets()['projectID']

with get_ica_api_client() as api_client:

    pd_api = project_data_api.ProjectDataApi(api_client)

    folder = f'/{args.bucket}/{args.sample}/'
    body = CreateData(
        name=f'{args.sample}.cram.crai',
        folderPath=folder,
        dataType='FILE',
    )
    api_response = pd_api.create_data_in_project(  # type: ignore[ReportUnknownVariableType]
        path_params={'projectId': project_id},  # type: ignore[ReportUnknownVariableType]
        body=body,
    )

    new_object_id = api_response.body['data']['id']  # type: ignore[ReportUnknownVariableType]
    new_status = api_response.body['data']['details']['status']  # type: ignore[ReportUnknownVariableType]

    authenticate_ica_cli()

    run_subprocess_with_log(['gcloud', 'storage', 'cp', CRAM, LOCAL_NAME], f'Download {CRAM}')
    run_subprocess_with_log(
        [
            'icav2',
            'projectdata',
            'upload',
            LOCAL_NAME,
            folder,
        ],
        f'Upload {LOCAL_NAME} to ICA',
    )
