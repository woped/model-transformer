"""Directory handling and id generator for testgeneration."""
import shutil
from pathlib import Path

OUT_PATH = "out"


def set_out_path(path: str):
    """Set OUT_PATH to path parameter."""
    global OUT_PATH
    OUT_PATH = path


def clear():
    """Remove content from OUT_PATH directory."""
    try:
        shutil.rmtree(OUT_PATH)
    except Exception:
        pass


def create_file_path(file_name: str, test_case_name: str):
    """Create and return directory for test case and file name."""
    Path(f"{OUT_PATH}/{test_case_name}").mkdir(parents=True, exist_ok=True)
    return f"{OUT_PATH}/{test_case_name}/{file_name}"


def read_bpmn_file(case_name: str):
    """Return text of bpmn case."""
    return Path(f"{OUT_PATH}/{case_name}/bpmn.bpmn").read_text()


class UniqueIDGenerator:
    """Generates unique IDs."""
    running_id = 0

    @staticmethod
    def generate() -> str:
        """Returns an unique id starting with "element_"."""
        UniqueIDGenerator.running_id += 1
        return f"element_{UniqueIDGenerator.running_id}"
