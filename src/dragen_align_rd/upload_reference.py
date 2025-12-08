import os
from icasdk.model.create_data import CreateData
from icasdk.apis.tags import project_data_api

from dragen_align_rd.utils import run_subprocess_with_log
from dragen_align_rd.ica_cli_utils import authenticate_ica_cli
from dragen_align_rd.ica_api_utils import get_ica_api_client, get_ica_secrets


BATCH_TMP = os.environ.get('BATCH_TMPDIR', '/io')


FASTA = 'gs://cpg-common-main/references/hg38/v0/dragen_reference/Homo_sapiens_assembly38_masked.fasta'
LOCAL_NAME = f'{BATCH_TMP}/Homo_sapiens_assembly38_masked.cram'

project_id = get_ica_secrets()['projectID']

with get_ica_api_client() as api_client:

    pd_api = project_data_api.ProjectDataApi(api_client)

    folder = f'/ref_data/'
    body = CreateData(
        name='Homo_sapiens_assembly38_masked.fasta',
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

    run_subprocess_with_log(['gcloud', 'storage', 'cp', FASTA, LOCAL_NAME], f'Download {FASTA}')
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
