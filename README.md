# Debt Snowball & Avalanche Simulator
#### Video Demo: <URL HERE>
#### Description:

This project simulates two common strategies for paying off multiple debts: the **Snowball method** and the **Avalanche method**. Given a set of debts (balance, interest rate, and minimum payment), the program calculates how many months it would take to pay off all debts under each strategy, and the total interest paid, so the two can be compared directly.

The Snowball method pays off debts in order of smallest balance first, regardless of interest rate. The Avalanche method pays off debts in order of highest interest rate first. In both cases, any extra monthly payment beyond the minimums is applied entirely to whichever debt is first in the current order. Once a debt reaches zero, its minimum payment is folded into the extra payment for the next debt in line, which is what produces the compounding "snowball" effect the first method is named after.

### Project structure

All code lives in `project.py`, with a `main()` function and several additional functions, each independently testable and covered in `test_project.py`.

### Functions

**`main()`**
Entry point. Parses command-line arguments to determine how debts are supplied, collects the extra monthly payment, runs both simulations, and prints the results.

**`parse_args(argv=None)`**
Defines two mutually exclusive command-line flags: `--csv <path>`, for loading debts from a CSV file, and `--manual`, for entering them interactively. If neither is passed, the program defaults to manual entry. Passing both raises an error via `argparse`. The optional `argv` parameter allows the function to be tested without relying on `sys.argv`.

**`load_debts_from_csv(csv_filepath)`**
Reads debts from a CSV file using `csv.DictReader`. The file must contain the columns `name`, `balance`, `rate`, and `min_payment`. Numeric fields are validated (non-negative, non-zero where required); missing columns, invalid values, or an empty file raise a `ValueError`. A missing file raises `FileNotFoundError`. This function only reads and validates data — it does not print anything or exit the program, so any calling code decides how to handle failures.

**`get_debts()`**
Collects debts interactively via `input()`. Prompts for name, balance, rate, and minimum payment in a loop until the user types `done`. Invalid input is rejected with a message, and the same entry is requested again.

**`get_extra_payment()`**
Prompts for the extra amount available per month, rejecting negative or non-numeric values until a valid one is entered.

**`print_debts_table(debts)`**
Displays the list of debts in a formatted table using the `tabulate` library.

**`snowball_order(debts)`**
Returns a new list of debts sorted by ascending balance. Does not modify the input list.

**`avalanche_order(debts)`**
Returns a new list of debts sorted by descending interest rate. Does not modify the input list.

**`simulate_payoff(debts, extra_payment=0)`**
Runs the core simulation. Operates on a copy of the input list, so the original is left unchanged. Each iteration represents one month: interest accrues on every debt with a remaining balance, minimum payments are applied, and the extra payment is directed to the first debt in the list with a balance above zero. The loop continues until all balances reach zero, tracking total months and total interest paid. If the debts are not paid off within 1080 months — typically meaning the minimum payments don't cover the accruing interest — a `RuntimeError` is raised instead of looping indefinitely.

**`print_comparison(snowball_result, avalanche_result)`**
Prints a table comparing months and total interest for both strategies, using `tabulate`.

### Design notes

Debts are represented as dictionaries (`name`, `balance`, `rate`, `min_payment`) inside a plain list, rather than as a custom class. This keeps the sorting functions to a single line each (`sorted(debts, key=...)`) and avoids adding structure the project doesn't need at this scale.

`simulate_payoff()` operates on a copy of the debts it receives (`[d.copy() for d in debts]`). This matters because `main()` calls the function twice — once for each strategy — using the same original list. Without copying, the second call would silently operate on debts already drained to zero by the first.

CSV loading and manual entry are kept as separate functions rather than merged into one, since they fail differently: a CSV either has valid data or raises an exception immediately, while manual entry can recover from a single bad input by asking again. Mixing `raise` (used for CSV parsing) with `print` + retry (used for manual entry) in the same function would blur that distinction.

### Testing

`test_project.py` covers every function that doesn't depend on `input()`: `parse_args`, `load_debts_from_csv`, `snowball_order`, `avalanche_order`, and `simulate_payoff`. CSV-related tests use pytest's `tmp_path` fixture to create temporary files, so they run without any external file needing to exist beforehand. `simulate_payoff` is tested both for expected behavior (faster payoff with extra payments, an exact result with 0% interest) and for its failure case (`RuntimeError` when minimum payments never cover accruing interest).

`get_debts()` and `get_extra_payment()` are not covered by automated tests, since both depend on `input()`.

### Requirements

Dependencies are listed in `requirements.txt`:

```
tabulate
pytest
```

Install with:

```bash
pip install -r requirements.txt
```

### Usage

```bash
python project.py --manual
python project.py --csv debts.csv
```

CSV format:

```csv
name,balance,rate,min_payment
Visa,1500,24.5,50
Car Loan,8000,7.2,220
```

