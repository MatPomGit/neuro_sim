from pathlib import Path


def test_windows_exe_workflow_is_manual_and_uploads_artifact() -> None:
    workflow_path = Path(__file__).parent.parent / '.github' / 'workflows' / 'build-windows-exe.yml'
    workflow_content = workflow_path.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow_content
    assert "runs-on: windows-latest" in workflow_content
    assert "python scripts/build_exe.py" in workflow_content
    assert "dist/NeuroSim/NeuroSim.exe" in workflow_content
    assert "actions/upload-artifact@v4" in workflow_content
    assert "artifact/NeuroSim-Windows.zip" in workflow_content
