import json

from brain_core.bids import validate_bids_file_name, validate_dataset_description


def test_validate_bids_file_name_accepts_eeg_events_tsv() -> None:
    result = validate_bids_file_name("sub-001_ses-01_task-rest_events.tsv")

    assert result.is_valid
    assert result.errors == ()


def test_validate_bids_file_name_rejects_wrong_entity_order() -> None:
    result = validate_bids_file_name("task-rest_sub-001_eeg.edf")

    assert not result.is_valid
    assert "Encje BIDS występują w niepoprawnej kolejności." in result.errors


def test_validate_dataset_description_accepts_minimal_raw_description(tmp_path) -> None:
    description_path = tmp_path / "dataset_description.json"
    description_path.write_text(
        json.dumps(
            {
                "Name": "Zbiór testowy EEG",
                "BIDSVersion": "1.11.1",
                "DatasetType": "raw",
            }
        ),
        encoding="utf-8",
    )

    result = validate_dataset_description(description_path)

    assert result.is_valid
    assert result.errors == ()


def test_validate_dataset_description_rejects_missing_dataset_type(tmp_path) -> None:
    description_path = tmp_path / "dataset_description.json"
    description_path.write_text(
        json.dumps({"Name": "Zbiór testowy EEG", "BIDSVersion": "1.11.1"}),
        encoding="utf-8",
    )

    result = validate_dataset_description(description_path)

    assert not result.is_valid
    assert (
        "Pole 'DatasetType' jest wymagane w dataset_description.json." in result.errors
    )
