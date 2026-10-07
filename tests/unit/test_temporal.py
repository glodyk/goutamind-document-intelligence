from app.document.dates import labelled_dates
from app.temporal import find_dates
from app.vocabulary import DateRole, TemporalPrecision


def only(text: str, **kwargs):
    matches = find_dates(text, **kwargs)
    assert len(matches) == 1, matches
    return matches[0].temporal


def test_iso_date_and_datetime():
    assert only("Tgl SEP : 2025-02-03").value == "2025-02-03"
    tv = only("Tgl Daftar : 2025-02-03 10:11:12")
    assert (tv.value, tv.precision) == ("2025-02-03T10:11:12", TemporalPrecision.EXACT_DATETIME)


def test_indonesian_and_english_month_names():
    assert only("3 Februari 2025").value == "2025-02-03"
    assert only("14 Mar 2024").value == "2024-03-14"
    assert only("21 May 2023").value == "2023-05-21"
    assert only("25 Desember 2024").value == "2024-12-25"


def test_month_precision_is_not_increased():
    tv = only("Kontrol : September 2025")
    assert tv.value == "2025-09"
    assert tv.precision is TemporalPrecision.MONTH


def test_time_and_timezone_are_kept_only_when_written():
    tv = only("Waktu Datang : 3 Februari 2025, 07:55 WIB")
    assert tv.value == "2025-02-03T07:55"
    assert tv.timezone == "WIB"
    assert only("3 Februari 2025").precision is TemporalPrecision.DATE


def test_ambiguous_numeric_date_is_not_guessed():
    tv = only("Tanggal Masuk : 03/02/2025")
    assert tv.value is None
    assert tv.precision is TemporalPrecision.UNKNOWN
    assert tv.ambiguity == "AMBIGUOUS_DAY_MONTH_ORDER"
    assert tv.raw_text == "03/02/2025"


def test_numeric_date_resolved_when_unambiguous_or_configured():
    assert only("14/03/2024").value == "2024-03-14"
    assert only("03/14/2024").value == "2024-03-14"
    assert only("03/02/2025", numeric_order="DMY").value == "2025-02-03"
    assert only("03/02/2025", numeric_order="MDY").value == "2025-03-02"


def test_invalid_dates_are_ignored():
    assert find_dates("Kode 99/99/2025 dan 2025-13-40") == []


def test_raw_text_is_preserved():
    assert only("Dicetak pada 19-08-2024 10:05").raw_text == "19-08-2024 10:05"


def test_date_roles_come_from_the_label_before_the_date():
    dates = labelled_dates("Tgl. Order : 19/08/2024 09:30 Tgl. Periksa : 19/08/2024 10:05")
    assert [d.date_role for d in dates] == [DateRole.ORDER, DateRole.UNKNOWN]
    assert labelled_dates("Tgl KRS : 5 Februari 2025")[0].date_role is DateRole.DISCHARGE
    assert labelled_dates("Kota Contoh, 9 April 2024")[0].date_role is DateRole.UNKNOWN


def test_birth_dates_are_not_collected():
    dates = labelled_dates("Tgl. Lahir : 15/06/1980 Tgl. Periksa : 19/08/2024")
    assert [d.raw_text for d in dates] == ["19/08/2024"]
