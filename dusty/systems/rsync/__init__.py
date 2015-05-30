import os
import logging
from subprocess import check_call

from ... import constants
from ...config import get_config_value, assert_config_key
from ...demote import check_call_demoted
from ...source import repo_is_overridden, get_expanded_repo_name
from ...repo_path import local_repo_path, vm_repo_path
from ...log import log_to_client
from dusty.compiler.spec_assembler import get_repo_of_app_or_library, get_assembled_specs

def _ensure_vm_dir_exists(remote_dir):
    check_call_demoted(['boot2docker', 'ssh', 'sudo mkdir -p {0}; sudo chown -R docker {0}'.format(remote_dir)])

def _rsync_command(local_path, remote_path, is_dir=True):
    ssh_opts = 'ssh -p 2022 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /Users/{}/.ssh/id_boot2docker'.format(get_config_value('mac_username'))
    command = ['rsync', '-e', ssh_opts, '-az', '--exclude', '*/.git', '--force',
               '{}{}'.format(local_path, '/' if is_dir else ''), 'docker@localhost:{}'.format(remote_path)]
    return command

def sync_local_dir_to_vm(local_dir, remote_dir, demote=False):
    _ensure_vm_dir_exists(remote_dir)
    command = _rsync_command(local_dir, remote_dir, is_dir=True)
    logging.debug('Executing rsync command: {}'.format(' '.join(command)))
    check_call(command) if not demote else check_call_demoted(command)

def sync_local_file_to_vm(local_path, remote_path, demote=False):
    _ensure_vm_dir_exists(os.path.split(remote_path)[0])
    command = _rsync_command(local_path, remote_path, is_dir=False)
    logging.debug('Executing rsync command: {}'.format(' '.join(command)))
    check_call(command) if not demote else check_call_demoted(command)

def sync_repos(repos):
    logging.info('Syncing repos over rsync')
    assert_config_key('mac_username')
    for repo_name in repos:
        repo_name = get_expanded_repo_name(repo_name)
        repo_type = 'overridden' if repo_is_overridden(repo_name) else 'Dusty-managed'
        remote_path = vm_repo_path(repo_name)
        log_to_client('Syncing {} repo {} to remote at {}'.format(repo_type, repo_name, remote_path))
        sync_local_dir_to_vm(local_repo_path(repo_name), remote_path)

def sync_repos_by_app_name(app_names):
    repos = set()
    assembled_specs = get_assembled_specs()
    for app_name in app_names:
        for lib_name in assembled_specs['apps'][app_name]['depends']['libs']:
            repos.add(get_repo_of_app_or_library(lib_name))
        repos.add(get_repo_of_app_or_library(app_name))
    sync_repos(repos)
