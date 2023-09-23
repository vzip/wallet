import pytest

@pytest.fixture(scope="function")
def task_info(request):
    task_number = request.node.get_closest_marker("task_number")
    attempts = request.node.get_closest_marker("attempts")
    if task_number:
        request.node.task_number = task_number.args[0]
    else:
        request.node.task_number = "N/A"
    if attempts:
        request.node.attempts = attempts.args[0]
    else:
        request.node.attempts = "N/A"

def pytest_html_results_table_header(cells):
    cells.insert(1, 'Task Number')
    cells.insert(2, 'Attempts')
    cells.pop()

def pytest_html_results_table_row(report, cells):
    cells.insert(1, str(getattr(report, 'task_number', 'N/A')))
    cells.insert(2, str(getattr(report, 'attempts', 'N/A')))
    cells.pop()
