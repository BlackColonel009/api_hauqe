import json
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.fixture(scope='module')
def model():
    if not shutil.which('docker'):
        pytest.skip('Docker CLI required for Compose validation (daemon not needed)')
    result = subprocess.run([
        'docker', 'compose', '--env-file', '.env.compose.linux.example',
        '-f', 'compose.linux.yaml', '--profile', 'operations',
        'config', '--no-env-resolution', '--format', 'json',
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_linux_does_not_expose_postgresql(model):
    assert not model['services']['db'].get('ports')
    port = model['services']['web']['ports'][0]
    assert port['host_ip'] == '127.0.0.1'
    assert str(port['published']) == '8002'


def test_linux_worker_and_smtp_are_opt_in(model):
    web, worker = (model['services'][key] for key in ('web', 'worker'))
    assert worker['profiles'] == ['operations']
    for service in (web, worker):
        assert service['environment']['BACKGROUND_SERVICES_ENABLED'] == 'false'
        assert service['environment']['HAUQE_SMTP_ENABLED'] == 'false'
    assert worker['command'] == ['python', '-m', 'app.tasks.run_background_services']


def test_linux_storage_shared_only_with_its_worker(model):
    services = model['services']
    for key in ('web', 'worker'):
        targets = {item['target'] for item in services[key]['volumes']}
        assert '/srv/sngsc/uploads' in targets
        assert '/srv/sngsc/app/uploads/avatars' in targets
    assert services['web']['depends_on']['db']['condition'] == 'service_healthy'


def test_database_role_is_not_superuser():
    init = Path('deploy/init-db.sh').read_text()
    assert 'NOSUPERUSER NOCREATEDB NOCREATEROLE' in init
    assert "PASSWORD :'app_password'" in init


def test_export_does_not_mutate_or_collect_secrets():
    script = Path('deploy/export-contabo.sh').read_text()
    assert 'pg_dump -Fc' in script
    assert 'app/uploads/avatars' in script
    assert 'application.tar.gz' in script
    assert "--exclude='.env*'" in script
    assert 'sha256sum' in script
    assert '.env' not in script.split('printf')[0]
    assert 'DROP ' not in script and 'UPDATE ' not in script and 'systemctl' not in script


def test_image_contains_versioned_pg_client_and_legacy_linux_path():
    text = Path('Dockerfile').read_text()
    assert 'postgresql-client-${POSTGRES_MAJOR}' in text
    assert 'ln -s /srv/sngsc /var/www/api_hauqe' in text


def test_linux_matches_confirmed_source_major(model):
    assert model['services']['db']['image'] == 'postgres:16-bookworm'
    assert str(model['services']['web']['build']['args']['POSTGRES_MAJOR']) == '16'
