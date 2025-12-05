import os
from argparse import ArgumentParser
from typing import Iterator

from loguru import logger
from icasdk.model.create_data import CreateData

from icasdk import ApiClient, Configuration
from icasdk.exceptions import ApiException

from dragen_align_rd.utils import run_subprocess_with_log


BATCH_TMP = os.environ.get('BATCH_TMPDIR', '/io')


ICA_CLI_SETUP = """
mkdir -p $HOME/.icav2
set +x
echo "server-url: ica.illumina.com" > /root/.icav2/config.yaml
echo "x-api-key: {API_KEY}" >> $HOME/.icav2/config.yaml
icav2 projects enter {PROJECT}
set -x
"""  # noqa: E501


def authenticate_ica_cli(project: str, key: str) -> None:
    """Authenticates the icav2 CLI."""
    logger.info('Authenticating ICA CLI...')
    # This command uses shell=True, but ICA_CLI_SETUP is a trusted constant
    run_subprocess_with_log(ICA_CLI_SETUP.format(API_KEY=key, PROJECT=project), 'Authenticate ICA CLI', shell=True)  # noqa: S604


def get_ica_api_client(key: str) -> Iterator[ApiClient]:
    """
    Provides a context-managed icasdk.ApiClient.
    Handles fetching secrets, configuring, and closing the client.
    """

    configuration = Configuration(host='https://ica.illumina.com/ica/rest', api_key=key)

    with ApiClient(configuration=configuration) as api_client:
        try:
            yield api_client
        except ApiException as e:
            logger.error(f'ICA API Exception caught by context manager: {e}')
            raise
        except Exception as e:
            logger.error(f'Non-API Exception caught by context manager: {e}')
            raise

parser = ArgumentParser()
parser.add_argument('--key')
parser.add_argument('--project')
parser.add_argument('--bucket')
parser.add_argument('--sample')
args = parser.parse_args()


CRAM = f'gs://cpg-{args.project}-test/cram/{args.sample}.cram'
LOCAL_NAME = f'{BATCH_TMP}/{args.sample}.cram'

with get_ica_api_client(key=args.key) as api_client:

    folder = f'/{args.bucket}/{args.sample}/'
    body = CreateData(
        name=f'{args.sample}.cram',
        folderPath=folder,
        dataType='FILE',
    )
    api_response = api_client.create_data_in_project(  # type: ignore[ReportUnknownVariableType]
        path_params=path_params,  # type: ignore[ReportUnknownVariableType]
        body=body,
    )
    print(api_response)

    new_object_id = api_response.body['data']['id']  # type: ignore[ReportUnknownVariableType]
    new_status = api_response.body['data']['details']['status']  # type: ignore[ReportUnknownVariableType]

    authenticate_ica_cli(project=args.project, key=args.key)
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
