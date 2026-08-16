import argparse
import csv
import sys
from tabulate import tabulate

# ============================================================================
# FUNCTIONS
# ============================================================================
def parse_args(argv=None):
    """
    Parse command-line arguments for choosing how debts are loaded.

    Defines two mutually exclusive ways of supplying debts: '--csv',
    which takes a path to a CSV file, and '--manual', a flag indicating
    the user will enter debts interactively. If neither is provided, the
    caller is expected to default to manual entry.

    :param argv: A list of argument strings to parse, primarily used for
        testing. If None, arguments are read from sys.argv as usual.
        Defaults to None.
    :type argv: list[str] or None
    :raise SystemExit: If both '--csv' and '--manual' are passed
        together, or if argparse encounters invalid/unrecognized
        arguments.
    :return: An object with two attributes: 'csv' (the path to a CSV
        file if provided, otherwise None) and 'manual' (True if the
        --manual flag was passed).
    :rtype: argparse.Namespace
    """

    args_parser = argparse.ArgumentParser(
        description = "Debt payoff simulator: Snowball vs Avalanche"
    )

    # debts from csv file
    args_parser.add_argument(
        "--csv",
        type=str,
        help="Path to a CSV file containing debts (columns: name, balance, rate, min_payment)"
    )

    # debts from user input
    args_parser.add_argument(
        "--manual",
        action="store_true",
        help="Enter debts manually via the terminal"
    )

    # read terminal arguments
    args = args_parser.parse_args(argv)

    if args.manual and args.csv:
        args_parser.error("Using --csv and --manual at the same time is not possible")

    return args


def load_debts_from_csv(csv_filepath):
    """
    Load a list of debts from a CSV file.

    The CSV must contain a header row with exactly the columns 'name',
    'balance', 'rate', and 'min_payment'. Each row below is parsed
    into a debt dictionary.

    :param csv_filepath: Path to the CSV file containing the debts.
    :type csv_filepath: str
    :raise FileNotFoundError: If no file exists at the given filepath.
    :raise ValueError: If the CSV is missing required columns, contains
        non-numeric values in a numeric column, contains an out-of-range
        value, or contains no valid debt rows at all.
    :return: A list of debts, where each debt is a dictionary with the
        keys 'name', 'balance', 'rate', and 'min_payment'.
    :rtype: list[dict]
    """

    debts = []
    try:
        with open(csv_filepath, "r", newline="") as file:
            reader = csv.DictReader(file)

            debts_info = {"name", "balance", "rate", "min_payment"}

            # check if the corresponding fieldnames are in the file
            if not debts_info.issubset(reader.fieldnames or []):
                raise ValueError("The CSV file must have the following columns: name, balance, rate, min_payment")

            for row in reader:
                try:
                    balance = float(row["balance"])
                    rate = float(row["rate"])
                    min_payment = float(row["min_payment"])

                    if balance <= 0 or rate < 0 or min_payment <= 0:
                        raise ValueError

                except ValueError:
                    raise ValueError(f"Invalid debt information in row: {row}")

                debts.append({"name": row["name"],
                            "balance": balance,
                            "rate": rate,
                            "min_payment": min_payment})

    except FileNotFoundError:
        raise FileNotFoundError(f"The CSV file was not found: {csv_filepath}")

    if not debts:
        raise ValueError("The CSV file is empty or does not contain valid debts")

    return debts


def get_debts():
    """
    Prompt the user to manually enter their debts one at a time.

    Repeatedly asks for a debt's name, balance, annual interest rate, and
    minimum monthly payment until the user types 'listo'. Invalid numeric
    input or out-of-range values (zero or negative where not allowed) are
    rejected and the user is asked to try again for that entry.

    :return: A list of debts, where each debt is a dictionary with the
        keys 'name', 'balance', 'rate', and 'min_payment'. Returns an
        empty list if the user exits without entering any debts.
    :rtype: list[dict]
    """

    debts = []
    while True:
        name = input("Debt name (or 'Done' to finish): ")
        if name.lower() == "done":
            break

        try:
            balance = float(input("Balance: "))
            rate = float(input("Rate: "))
            min_payment = float(input("Minimum payment: "))

            if balance <= 0 or rate < 0 or min_payment <= 0:
                raise ValueError

        except ValueError:
            print("Invalid debt information, please try again.")
            continue

        debts.append({"name": name,
                    "balance": balance,
                    "rate": rate,
                    "min_payment": min_payment})

    return debts


def print_debts_table(debts):
    """
    Print a table listing each debt's name, balance, rate, and minimum payment.

    :param debts: A list of debt dictionaries with keys 'name', 'balance',
        'rate', and 'min_payment'.
    :type debts: list[dict]
    """
    headers = ["Name", "Balance", "Rate (%)", "Minimum payment"]
    rows = [
        [d["name"], f"${d['balance']}", d["rate"], f"${d['min_payment']}"]
        for d in debts
    ]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def get_extra_payment():
    """
    Prompt the user for the extra amount they can pay toward debt each month.

    Keeps asking until the user enters a valid, non-negative number.

    :return: The extra monthly payment amount, in the same currency
        units as the debts (e.g. dollars).
    :rtype: float
    """
    while True:
        try:
            extra = float(input("Monthly extra payment for debts: "))
            if extra < 0:
                raise ValueError
            return extra
        except ValueError:
            print("Not a valid number")


def snowball_order(debts):
    """
    Sort debts using the snowball strategy (smallest balance first).

    :param debts: A list of debt dictionaries, each containing at least
        a 'balance' key.
    :type debts: list[dict]
    :return: A new list containing the same debt dictionaries, sorted in
        ascending order by 'balance'. The original list is not modified.
    :rtype: list[dict]
    """
    return sorted(debts, key=lambda s: s["balance"])


def avalanche_order(debts):
    """
    Sort debts using the avalanche strategy (highest interest rate first).

    :param debts: A list of debt dictionaries, each containing at least
        a 'rate' key.
    :type debts: list[dict]
    :return: A new list containing the same debt dictionaries, sorted in
        descending order by 'rate'. The original list is not modified.
    :rtype: list[dict]
    """
    return sorted(debts, key=lambda s:s["rate"], reverse=True)

def simulate_payoff(debts, extra_payment=0):
    """
    Simulate paying off a list of debts month by month.

    Each month, interest is accrued on every debt with a remaining
    balance, minimum payments are applied, and the extra payment is
    directed entirely toward the first debt in the given order that still
    has a balance greater than zero. Once a debt is paid off, its minimum
    payment is effectively freed up for the next debt in line, since the
    extra payment always targets whichever debt is currently first — this
    is what produces the "snowball" effect.

    :param debts: A list of debt dictionaries, each with keys 'balance'
        (float), 'rate' (float, annual percentage), and 'min_payment'
        (float). The order of this list determines which debt is
        prioritized for the extra payment.
    :type debts: list[dict]
    :param extra_payment: The extra amount available each month to put
        toward the highest-priority debt, on top of all minimum
        payments. Defaults to 0.
    :type extra_payment: float
    :raise RuntimeError: If the debts are not fully paid off within 600
        months, which typically indicates the minimum payments are too
        low to ever cover the accruing interest.
    :return: A summary of the simulation with the keys 'months' (total
        number of months until every debt reached zero) and
        'total_interest' (total interest paid across all debts, rounded
        to 2 decimal places).
    :rtype: dict
    """
    debts = [d.copy() for d in debts]  # to not modify the original
    months = 0
    total_interest = 0
    available_extra = extra_payment

    while any(d["balance"] > 0 for d in debts): # if there is, at least, a non-paid debt
        months += 1
        for debt in debts:
            if debt["balance"] <= 0: # if the current debt is totally paid, continue
                continue

            monthly_debt_rate = debt["rate"] / 100 / 12

            interest = debt["balance"] * monthly_debt_rate

            total_interest += interest
            debt["balance"] += interest

            payment = debt["min_payment"]

            # if the current debt is the first debt that is not fully paid,
            # the extra monthly payment is applied to it
            if debt is next((d for d in debts if d["balance"] > 0), None):
                payment += available_extra

            payment = min(payment, debt["balance"])
            debt["balance"] -= payment

        # if the debt cannot be repaid throughout their lifetime
        if months > 1080:  # average number of months in a normal lifetime
            raise RuntimeError("The debts cannot be paid with the minimum payment")

    return {"months": months, "total_interest": round(total_interest, 2)}


def print_comparison(snowball_result, avalanche_result):
    """
    Print a human-readable comparison of the two payoff simulations as a table.

    :param snowball_result: The result of simulate_payoff() run with
        debts in snowball order, containing 'months' and
        'total_interest'.
    :type snowball_result: dict
    :param avalanche_result: The result of simulate_payoff() run with
        debts in avalanche order, containing 'months' and
        'total_interest'.
    :type avalanche_result: dict
    """
    headers = ["Method", "Months", "Total Interest"]
    rows = [
        ["Snowball", snowball_result["months"], f"${snowball_result['total_interest']}"],
        ["Avalanche", avalanche_result["months"], f"${avalanche_result['total_interest']}"],
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


# ============================================================================
# MAIN
# ============================================================================
def main():

    """Entry point of the program.

    Parses command-line arguments to decide how to load the user's debts
    (from a CSV file or via manual terminal input), asks for the extra
    monthly payment available, runs both the snowball and avalanche
    simulations, and prints a comparison of the two results.
    """

    args = parse_args()

    if args.csv:
        try:
            debts = load_debts_from_csv(args.csv)
        except (FileNotFoundError, ValueError) as e:
            sys.exit(f"Error: {e}")
    else:
        debts = get_debts()

    if not debts:
        sys.exit("No debts to process.")

    print_debts_table(debts)

    extra = get_extra_payment()

    snowball_result = simulate_payoff(snowball_order(debts), extra)
    avalanche_result = simulate_payoff(avalanche_order(debts), extra)

    print_comparison(snowball_result, avalanche_result)

if __name__ == "__main__":
    main()
