import logging
from enum import Enum
from os import listdir
from os.path import join

from typing import List

from benchmark.data.misuse import Misuse


class DataReaderSubprocess:
    class Answer(Enum):
        ok = 0
        skip = 1

    def setup(self) -> None:
        pass

    def run(self, misuse: Misuse) -> Answer:
        raise NotImplementedError

    def teardown(self) -> None:
        pass


class DataReader:
    def __init__(self, data_path: str, white_list: List[str], black_list: List[str]):
        self._logger = logging.getLogger()
        self.steps = []  # type: List[DataReaderSubprocess]
        self.data_path = data_path
        self.white_list = white_list
        self.black_list = black_list

    def add(self, step: DataReaderSubprocess):
        self.steps.append(step)

    def run(self) -> None:
        misuses = self._get_misuses()

        try:
            self._run_setup()

            for i, misuse in enumerate(misuses, start=1):
                self._logger.info("Misuse '%s' (%r/%r) >", misuse, i, len(misuses))

                for step in self.steps:
                    answer = step.run(misuse)
                    if answer is DataReaderSubprocess.Answer.skip:
                        break
        finally:
            self._run_teardown()

    def _run_setup(self):
        for step in self.steps:
            try:
                self._logger.debug("Setup '%s'", type(step).__name__)
                step.setup()
            except Exception:
                self._logger.error("Error in setup", exc_info=True)
                raise

    def _run_teardown(self):
        for step in self.steps:
            self._logger.debug("Teardown '%s'", type(step).__name__)
            step.teardown()

    def _get_misuses(self):
        candidates = [join(self.data_path, file) for file in sorted(listdir(self.data_path))]
        misuses = [Misuse(path) for path in candidates if Misuse.ismisuse(path)]
        misuses = [misuse for misuse in misuses if not self.__skip(misuse.name)]
        return misuses

    def __skip(self, file: str):
        whitelisted = any([white_listed in file for white_listed in self.white_list])
        blacklisted = any([black_listed in file for black_listed in self.black_list])
        return not whitelisted or blacklisted
