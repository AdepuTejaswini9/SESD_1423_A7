from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# === Observer Pattern ===
class Observer:
    def update(self, account, message):
        pass

class Customer(Observer):
    def __init__(self, name):
        self.name = name
        self.notifications = []

    def update(self, account, message):
        note = f"Notification to {self.name}: Account {account.acc_id} - {message}"
        self.notifications.append(note)

# === Strategy Pattern ===
class InterestStrategy:
    def calculate_interest(self, balance):
        pass

class SavingsInterest(InterestStrategy):
    def calculate_interest(self, balance):
        return balance * 0.04

class FDInterest(InterestStrategy):
    def calculate_interest(self, balance):
        return balance * 0.07

class CurrentInterest(InterestStrategy):
    def calculate_interest(self, balance):
        return balance * 0.02

# === Account (Subject) ===
class Account:
    def __init__(self, acc_id, balance):
        self.acc_id = acc_id
        self.balance = balance
        self.observers = []
        self.strategy = None

    def attach(self, obs):
        self.observers.append(obs)

    def notify(self, msg):
        for o in self.observers:
            o.update(self, msg)

    def deposit(self, amt):
        self.balance += amt
        self.notify(f"Deposited {amt} | New balance: {self.balance}")

    def withdraw(self, amt):
        if amt > self.balance:
            self.notify(f"Withdrawal of {amt} failed (insufficient funds). Balance: {self.balance}")
        else:
            self.balance -= amt
            self.notify(f"Withdrew {amt} | New balance: {self.balance}")

    def set_interest_strategy(self, strategy):
        self.strategy = strategy

    def calculate_interest(self):
        if self.strategy:
            return self.strategy.calculate_interest(self.balance)
        return 0

# === Command Pattern ===
class Command:
    def execute(self): pass
    def undo(self): pass

class DepositCommand(Command):
    def __init__(self, account, amt):
        self.account = account
        self.amt = amt
        self.prev_balance = account.balance

    def execute(self):
        self.account.deposit(self.amt)

    def undo(self):
        self.account.balance = self.prev_balance
        self.account.notify("Undo deposit: balance restored")

class WithdrawCommand(Command):
    def __init__(self, account, amt):
        self.account = account
        self.amt = amt
        self.prev_balance = account.balance

    def execute(self):
        self.account.withdraw(self.amt)

    def undo(self):
        self.account.balance = self.prev_balance
        self.account.notify("Undo withdrawal: balance restored")

class Invoker:
    def __init__(self):
        self.history = []

    def execute_command(self, cmd):
        cmd.execute()
        self.history.append(cmd)

    def undo(self):
        if self.history:
            last = self.history.pop()
            last.undo()

# === Setup demo accounts & customers ===
a1 = Account("A1", 1000)
a2 = Account("A2", 500)

alice = Customer("Alice")
bob = Customer("Bob")

a1.attach(alice)
a1.attach(bob)
a2.attach(bob)

invoker = Invoker()

@app.route("/")
def index():
    return render_template("index.html", a1=a1, a2=a2, alice=alice, bob=bob)

@app.route("/deposit/<acc>/<int:amt>")
def deposit(acc, amt):
    acc_ref = a1 if acc == "A1" else a2
    invoker.execute_command(DepositCommand(acc_ref, amt))
    return redirect(url_for("index"))

@app.route("/withdraw/<acc>/<int:amt>")
def withdraw(acc, amt):
    acc_ref = a1 if acc == "A1" else a2
    invoker.execute_command(WithdrawCommand(acc_ref, amt))
    return redirect(url_for("index"))

@app.route("/undo")
def undo():
    invoker.undo()
    return redirect(url_for("index"))

@app.route("/interest/<acc>/<type>")
def interest(acc, type):
    acc_ref = a1 if acc == "A1" else a2
    if type == "savings":
        acc_ref.set_interest_strategy(SavingsInterest())
    elif type == "fd":
        acc_ref.set_interest_strategy(FDInterest())
    else:
        acc_ref.set_interest_strategy(CurrentInterest())
    interest_val = acc_ref.calculate_interest()
    acc_ref.notify(f"Interest calculated ({type}): {interest_val}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
