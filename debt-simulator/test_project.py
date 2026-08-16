import pytest
from project import (
    parse_args,
    load_debts_from_csv,
    snowball_order,
    avalanche_order,
    simulate_payoff,
)

# ---------- Tests for parse_args ----------

def test_parse_args_csv():
    args = parse_args(["--csv", "debts.csv"])
    assert args.csv == "debts.csv"
    assert args.manual is False


def test_parse_args_manual():
    args = parse_args(["--manual"])
    assert args.manual is True
    assert args.csv is None


def test_parse_args_no_flags():
    args = parse_args([])
    assert args.csv is None
    assert args.manual is False


def test_parse_args_conflict():
    with pytest.raises(SystemExit):
        parse_args(["--csv", "debts.csv", "--manual"])

# ---------- Tests for load_debts_from_csv ----------

def test_load_debts_from_csv(tmp_path):
    csv_content = "name,balance,rate,min_payment\nCard,1000,20,50\n"
    file = tmp_path / "debts.csv"
    file.write_text(csv_content)

    debts = load_debts_from_csv(str(file))

    assert len(debts) == 1
    assert debts[0]["name"] == "Card"
    assert debts[0]["balance"] == 1000
    assert debts[0]["rate"] == 20
    assert debts[0]["min_payment"] == 50


def test_load_debts_from_csv_multiple_rows(tmp_path):
    csv_content = (
        "name,balance,rate,min_payment\n"
        "Visa,1500,24.5,50\n"
        "Car,8000,7.2,220\n"
    )
    file = tmp_path / "debts.csv"
    file.write_text(csv_content)

    debts = load_debts_from_csv(str(file))

    assert len(debts) == 2
    assert debts[1]["name"] == "Car"


def test_load_debts_from_csv_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_debts_from_csv("non_existant_file.csv")


def test_load_debts_from_csv_missing_columns(tmp_path):
    csv_content = "name,balance\nCard,1000\n"
    file = tmp_path / "bad_debts.csv"
    file.write_text(csv_content)

    with pytest.raises(ValueError):
        load_debts_from_csv(str(file))


def test_load_debts_from_csv_invalid_numeric_value(tmp_path):
    csv_content = "name,balance,rate,min_payment\nCard,abc,20,50\n"
    file = tmp_path / "bad_debts.csv"
    file.write_text(csv_content)

    with pytest.raises(ValueError):
        load_debts_from_csv(str(file))


def test_load_debts_from_csv_out_of_range_value(tmp_path):
    csv_content = "name,balance,rate,min_payment\nCard,-1000,20,50\n"
    file = tmp_path / "bad_debts.csv"
    file.write_text(csv_content)

    with pytest.raises(ValueError):
        load_debts_from_csv(str(file))


def test_load_debts_from_csv_empty_file(tmp_path):
    file = tmp_path / "empty.csv"
    file.write_text("")

    with pytest.raises(ValueError):
        load_debts_from_csv(str(file))



# ---------- Tests for snowball_order ----------

def test_snowball_order():
    debts = [
        {"name": "A", "balance": 500, "rate": 10, "min_payment": 20},
        {"name": "B", "balance": 100, "rate": 20, "min_payment": 10},
        {"name": "C", "balance": 300, "rate": 5, "min_payment": 15},
    ]
    result = snowball_order(debts)
    assert [d["name"] for d in result] == ["B", "C", "A"]


def test_snowball_order_does_not_mutate_original():
    debts = [
        {"name": "A", "balance": 500, "rate": 10, "min_payment": 20},
        {"name": "B", "balance": 100, "rate": 20, "min_payment": 10},
    ]
    original_order = [d["name"] for d in debts]
    snowball_order(debts)
    assert [d["name"] for d in debts] == original_order


# ---------- Tests for avalanche_order ----------

def test_avalanche_order():
    debts = [
        {"name": "A", "balance": 500, "rate": 10, "min_payment": 20},
        {"name": "B", "balance": 100, "rate": 20, "min_payment": 10},
        {"name": "C", "balance": 300, "rate": 5, "min_payment": 15},
    ]
    result = avalanche_order(debts)
    assert [d["name"] for d in result] == ["B", "A", "C"]


def test_avalanche_order_does_not_mutate_original():
    debts = [
        {"name": "A", "balance": 500, "rate": 10, "min_payment": 20},
        {"name": "B", "balance": 100, "rate": 20, "min_payment": 10},
    ]
    original_order = [d["name"] for d in debts]
    avalanche_order(debts)
    assert [d["name"] for d in debts] == original_order


# ---------- Tests for simulate_payoff ----------

def test_simulate_payoff_single_debt_no_extra():
    debts = [{"name": "A", "balance": 100, "rate": 12, "min_payment": 20}]
    result = simulate_payoff(debts)
    assert result["months"] > 0
    assert result["total_interest"] >= 0


def test_simulate_payoff_with_extra_payment_is_faster():
    debts = [{"name": "A", "balance": 1000, "rate": 12, "min_payment": 20}]
    result_no_extra = simulate_payoff(debts, extra_payment=0)
    result_with_extra = simulate_payoff(debts, extra_payment=100)
    assert result_with_extra["months"] < result_no_extra["months"]
    assert result_with_extra["total_interest"] < result_no_extra["total_interest"]


def test_simulate_payoff_does_not_mutate_original():
    debts = [{"name": "A", "balance": 1000, "rate": 12, "min_payment": 20}]
    simulate_payoff(debts, extra_payment=50)
    assert debts[0]["balance"] == 1000


def test_simulate_payoff_zero_interest_debt():
    debts = [{"name": "A", "balance": 100, "rate": 0, "min_payment": 25}]
    result = simulate_payoff(debts)
    assert result["months"] == 4
    assert result["total_interest"] == 0


def test_simulate_payoff_raises_when_never_paid_off():
    # Interest accrued each month exceeds the minimum payment,
    # so the balance never actually shrinks.
    debts = [{"name": "A", "balance": 1000, "rate": 99, "min_payment": 1}]
    with pytest.raises(RuntimeError):
        simulate_payoff(debts)


