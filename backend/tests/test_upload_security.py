import asyncio
from io import BytesIO
from pathlib import Path

from starlette.datastructures import UploadFile

from routers.data import upload_csv
from services.analysis import load_csv_from_text

SAMPLE_CSV = "Run,Event,E1,E2,M\n1,1,1.0,2.0,3.0\n"


def test_load_csv_from_text_parses_valid_csv():
    records = load_csv_from_text(SAMPLE_CSV)
    assert len(records) == 1
    assert records[0]["M"] == 3.0


def test_upload_does_not_write_outside_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside_target = tmp_path.parent / "traversal_victim.csv"

    upload = UploadFile(
        filename="../traversal_victim.csv",
        file=BytesIO(SAMPLE_CSV.encode()),
    )
    response = asyncio.run(upload_csv(upload))

    assert response.rows == 1
    assert not outside_target.exists()
    assert not any(Path(tmp_path.parent).glob("traversal_victim.csv"))
