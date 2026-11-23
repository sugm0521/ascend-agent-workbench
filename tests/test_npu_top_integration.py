"""Include component-owned artifact tests in the workbench's normal discovery."""
import importlib.util
from pathlib import Path


def load_tests(loader, tests, pattern):
    path = Path(__file__).resolve().parents[1] / 'integrations/npu-top/tests/test_manage.py'
    spec = importlib.util.spec_from_file_location('npu_top_component_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
