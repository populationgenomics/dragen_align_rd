import os
from icasdk.apis.tags import project_data_api

from dragen_align_rd.utils import run_subprocess_with_log
from dragen_align_rd.ica_cli_utils import authenticate_ica_cli
from dragen_align_rd.ica_api_utils import get_ica_api_client, get_ica_secrets


BATCH_TMP = os.environ.get('BATCH_TMPDIR', '/io')


FASTA = 'gs://cpg-common-main/references/hg38/v0/dragen_reference/Homo_sapiens_assembly38_masked.fasta'
LOCAL_NAME = f'{BATCH_TMP}/Homo_sapiens_assembly38_masked.fasta'
LOCAL_INDEX = f'{BATCH_TMP}/Homo_sapiens_assembly38_masked.fasta.fai'

project_id = get_ica_secrets()['projectID']

with get_ica_api_client() as api_client:

    pd_api = project_data_api.ProjectDataApi(api_client)

    authenticate_ica_cli()

    run_subprocess_with_log(['gcloud', 'storage', 'cp', FASTA, LOCAL_NAME], f'Download {FASTA}')
    run_subprocess_with_log(['gcloud', 'storage', 'cp', f'{FASTA}.fai', LOCAL_INDEX], f'Download {FASTA}')
    run_subprocess_with_log(['tar', '-cf', 'Homo_sapiens_assembly38_masked.tar', LOCAL_NAME, LOCAL_INDEX], 'TAR files')
    run_subprocess_with_log(
        [
            'icav2',
            'projectdata',
            'upload',
            'Homo_sapiens_assembly38_masked.tar',
            '/ref_data/',
        ],
        'Upload Reference to ICA',
    )
