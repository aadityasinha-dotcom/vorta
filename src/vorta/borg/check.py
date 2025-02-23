from typing import Any, Dict
from vorta.config import LOG_DIR
from vorta.i18n import translate
from vorta.utils import borg_compat
from .borg_job import BorgJob


class BorgCheckJob(BorgJob):
    def started_event(self):
        self.app.backup_started_event.emit()
        self.app.backup_progress_event.emit(f"[{self.params['profile_name']}] {self.tr('Starting consistency check…')}")

    def finished_event(self, result: Dict[str, Any]):
        """
        Process that the job terminated with the given results.

        Parameters
        ----------
        result : Dict[str, Any]
            The (json-like) dictionary containing the job results.
        """
        self.app.backup_finished_event.emit(result)
        self.result.emit(result)
        if result['returncode'] != 0:
            self.app.backup_progress_event.emit(
                f"[{self.params['profile_name']}] "
                + translate('RepoCheckJob', 'Repo check failed. See the <a href="{0}">logs</a> for details.').format(
                    LOG_DIR.as_uri()
                )
            )
            self.app.check_failed_event.emit(result)
        else:
            self.app.backup_progress_event.emit(f"[{self.params['profile_name']}] {self.tr('Check completed.')}")

    @classmethod
    def prepare(cls, profile):
        ret = super().prepare(profile)
        if not ret['ok']:
            return ret
        else:
            ret['ok'] = False  # Set back to false, so we can do our own checks here.

        cmd = ['borg', 'check', '--info', '--log-json', '--progress']
        if borg_compat.check('V2'):
            cmd = cmd + ["-r", profile.repo.url]
        else:
            cmd.append(f'{profile.repo.url}')

        ret['ok'] = True
        ret['cmd'] = cmd

        return ret
