# banking_app.py

from flask import Flask, render_template, request, redirect, url_for
import abc # For Abstract Base Classes

app = Flask(__name__)

# --- 1. OBSERVER PATTERN ---
# OO Concepts: Encapsulation (state is hidden), Polymorphism (update method)

class Subject:
    """The Subject (e.g., Account) that holds state and notifies observers."""
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self, message):
        for observer in self._observers:
            # Polymorphism: Different observers (Customers) react to the same notification
            observer.update(message)

class Customer:
    """The Observer that receives notifications."""
    def __init__(self, name):
        self.name = name
        self.notifications = []

    def update(self, message):
        self.notifications.append(message)
        print(f"  -> NOTIFICATION for {self.name}: {message}")

# --- 2. STRATEGY PATTERN ---
# OO Concepts: Inheritance (Concrete strategies extend interface), Polymorphism

class InterestStrategy(metaclass=abc.ABCMeta):
    """The Strategy Interface defining the interest calculation algorithm (Abstraction)."""
    @abc.abstractmethod
    def calculate_interest(self, balance):
        pass

class SavingsInterest(InterestStrategy):
    """Concrete Strategy 1: Low fixed rate."""
    def calculate_interest(self, balance):
        return round(balance * 0.02, 2) # 2% interest

class FDInterest(InterestStrategy):
    """Concrete Strategy 2: Higher rate on the entire balance."""
    def calculate_interest(self, balance):
        return round(balance * 0.05, 2) # 5% interest

class CurrentInterest(InterestStrategy):
    """Concrete Strategy 3: Zero interest."""
    def calculate_interest(self, balance):
        return 0.00 # 0% interest

# --- OO CORE CLASS & SUBJECT/CONTEXT ---

class Account(Subject):
    """The Subject (for Observer) and Context (for Strategy) and Receiver (for Command)."""
    def __init__(self, account_id, name, balance, interest_strategy: InterestStrategy):
        super().__init__()
        self.account_id = account_id
        # Encapsulation: balance is managed through methods
        self._name = name
        self._balance = balance
        # Composition: Account holds the InterestStrategy
        self.interest_strategy = interest_strategy 
        self.transaction_history = []
        
    @property
    def name(self):
        return self._name

    @property
    def balance(self):
        return self._balance

    # Strategy Pattern Method
    def calculate_yearly_interest(self):
        # Polymorphism: The same method call executes different logic based on the strategy object
        return self.interest_strategy.calculate_interest(self._balance)

    # Command Pattern Receiver Methods
    def deposit(self, amount):
        self._balance += amount
        self.notify(f"Deposit of ${amount:.2f} successful. New balance: ${self._balance:.2f}")
        return True

    def withdraw(self, amount):
        if self._balance >= amount:
            self._balance -= amount
            self.notify(f"Withdrawal of ${amount:.2f} successful. New balance: ${self._balance:.2f}")
            return True
        else:
            self.notify(f"Withdrawal of ${amount:.2f} FAILED. Insufficient funds: ${self._balance:.2f}")
            return False

# --- 3. COMMAND PATTERN ---
# OO Concepts: Encapsulation (request is an object), Decoupling, Undo

class Command(metaclass=abc.ABCMeta):
    """The Command interface."""
    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def undo(self):
        # Required for rollback/transfer
        raise NotImplementedError

class DepositCommand(Command):
    """Concrete Command for Deposit."""
    def __init__(self, account_receiver: Account, amount):
        self._receiver = account_receiver # Account is the Receiver
        self._amount = amount
        self._executed = False

    def execute(self):
        if self._receiver.deposit(self._amount):
            self._executed = True
            self._receiver.transaction_history.append(f"Deposit +${self._amount:.2f}")
            return f"Deposit of ${self._amount:.2f} executed."
        return "Deposit failed."

    def undo(self):
        if self._executed:
            self._receiver.withdraw(self._amount) # Undo a deposit by withdrawing
            self._receiver.transaction_history.append(f"Deposit UNDO -${self._amount:.2f}")
            self._executed = False
            return f"Deposit of ${self._amount:.2f} undone."
        return "Deposit command not executed or already undone."

class WithdrawCommand(Command):
    """Concrete Command for Withdrawal."""
    def __init__(self, account_receiver: Account, amount):
        self._receiver = account_receiver
        self._amount = amount
        self._executed = False

    def execute(self):
        if self._receiver.withdraw(self._amount):
            self._executed = True
            self._receiver.transaction_history.append(f"Withdrawal -${self._amount:.2f}")
            return f"Withdrawal of ${self._amount:.2f} executed."
        return "Withdrawal failed due to insufficient funds."

    def undo(self):
        if self._executed:
            self._receiver.deposit(self._amount) # Undo a withdrawal by depositing
            self._receiver.transaction_history.append(f"Withdrawal UNDO +${self._amount:.2f}")
            self._executed = False
            return f"Withdrawal of ${self._amount:.2f} undone."
        return "Withdrawal command not executed or already undone."

# --- IN-MEMORY DATA STORE ---
customer_alice = Customer("Alice")
customer_bob = Customer("Bob")

account_savings = Account("S101", "Alice's Savings", 1000.00, SavingsInterest())
account_current = Account("C202", "Bob's Current", 500.00, CurrentInterest())

# Attach observers (Customer) to subjects (Account)
account_savings.attach(customer_alice)
account_current.attach(customer_bob)

ACCOUNTS = {
    account_savings.account_id: account_savings,
    account_current.account_id: account_current
}
CUSTOMERS = {
    customer_alice.name: customer_alice,
    customer_bob.name: customer_bob
}

# --- FLASK ROUTES (Invoker Role) ---

@app.route('/')
def dashboard():
    """Renders the main dashboard."""
    
    # Calculate interest using the Strategy Pattern for display
    savings_interest = account_savings.calculate_yearly_interest()
    current_interest = account_current.calculate_yearly_interest()
    
    interest_data = {
        "S101": savings_interest,
        "C202": current_interest
    }

    return render_template('index.html', 
        accounts=ACCOUNTS.values(), 
        customers=CUSTOMERS.values(),
        interest_data=interest_data)

@app.route('/transact', methods=['POST'])
def transact():
    """Handles deposit and withdrawal using the Command Pattern."""
    account_id = request.form['account_id']
    transaction_type = request.form['transaction_type']
    amount = float(request.form['amount'])
    
    account = ACCOUNTS.get(account_id)
    
    if account and amount > 0:
        if transaction_type == 'deposit':
            command = DepositCommand(account, amount)
        elif transaction_type == 'withdraw':
            command = WithdrawCommand(account, amount)
        else:
            return redirect(url_for('dashboard'))

        # Invoker: Executes the command
        command.execute() 
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("--- Initial Account Setup ---")
    account_savings.notify("Welcome to your Savings Account!")
    account_current.notify("Welcome to your Current Account!")
    print("----------------------------")
# banking_app.py

from flask import Flask, render_template, request, redirect, url_for
import abc # For Abstract Base Classes

app = Flask(__name__)

# --- 1. OBSERVER PATTERN ---
# OO Concepts: Encapsulation (state is hidden), Polymorphism (update method)

class Subject:
    """The Subject (e.g., Account) that holds state and notifies observers."""
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self, message):
        for observer in self._observers:
            # Polymorphism: Different observers (Customers) react to the same notification
            observer.update(message)

class Customer:
    """The Observer that receives notifications."""
    def __init__(self, name):
        self.name = name
        self.notifications = []

    def update(self, message):
        self.notifications.append(message)
        print(f"  -> NOTIFICATION for {self.name}: {message}")

# --- 2. STRATEGY PATTERN ---
# OO Concepts: Inheritance (Concrete strategies extend interface), Polymorphism

class InterestStrategy(metaclass=abc.ABCMeta):
    """The Strategy Interface defining the interest calculation algorithm (Abstraction)."""
    @abc.abstractmethod
    def calculate_interest(self, balance):
        pass

class SavingsInterest(InterestStrategy):
    """Concrete Strategy 1: Low fixed rate."""
    def calculate_interest(self, balance):
        return round(balance * 0.02, 2) # 2% interest

class FDInterest(InterestStrategy):
    """Concrete Strategy 2: Higher rate on the entire balance."""
    def calculate_interest(self, balance):
        return round(balance * 0.05, 2) # 5% interest

class CurrentInterest(InterestStrategy):
    """Concrete Strategy 3: Zero interest."""
    def calculate_interest(self, balance):
        return 0.00 # 0% interest

# --- OO CORE CLASS & SUBJECT/CONTEXT ---

class Account(Subject):
    """The Subject (for Observer) and Context (for Strategy) and Receiver (for Command)."""
    def __init__(self, account_id, name, balance, interest_strategy: InterestStrategy):
        super().__init__()
        self.account_id = account_id
        # Encapsulation: balance is managed through methods
        self._name = name
        self._balance = balance
        # Composition: Account holds the InterestStrategy
        self.interest_strategy = interest_strategy 
        self.transaction_history = []
        
    @property
    def name(self):
        return self._name

    @property
    def balance(self):
        return self._balance

    # Strategy Pattern Method
    def calculate_yearly_interest(self):
        # Polymorphism: The same method call executes different logic based on the strategy object
        return self.interest_strategy.calculate_interest(self._balance)

    # Command Pattern Receiver Methods
    def deposit(self, amount):
        self._balance += amount
        self.notify(f"Deposit of ${amount:.2f} successful. New balance: ${self._balance:.2f}")
        return True

    def withdraw(self, amount):
        if self._balance >= amount:
            self._balance -= amount
            self.notify(f"Withdrawal of ${amount:.2f} successful. New balance: ${self._balance:.2f}")
            return True
        else:
            self.notify(f"Withdrawal of ${amount:.2f} FAILED. Insufficient funds: ${self._balance:.2f}")
            return False

# --- 3. COMMAND PATTERN ---
# OO Concepts: Encapsulation (request is an object), Decoupling, Undo

class Command(metaclass=abc.ABCMeta):
    """The Command interface."""
    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def undo(self):
        # Required for rollback/transfer
        raise NotImplementedError

class DepositCommand(Command):
    """Concrete Command for Deposit."""
    def __init__(self, account_receiver: Account, amount):
        self._receiver = account_receiver # Account is the Receiver
        self._amount = amount
        self._executed = False

    def execute(self):
        if self._receiver.deposit(self._amount):
            self._executed = True
            self._receiver.transaction_history.append(f"Deposit +${self._amount:.2f}")
            return f"Deposit of ${self._amount:.2f} executed."
        return "Deposit failed."

    def undo(self):
        if self._executed:
            self._receiver.withdraw(self._amount) # Undo a deposit by withdrawing
            self._receiver.transaction_history.append(f"Deposit UNDO -${self._amount:.2f}")
            self._executed = False
            return f"Deposit of ${self._amount:.2f} undone."
        return "Deposit command not executed or already undone."

class WithdrawCommand(Command):
    """Concrete Command for Withdrawal."""
    def __init__(self, account_receiver: Account, amount):
        self._receiver = account_receiver
        self._amount = amount
        self._executed = False

    def execute(self):
        if self._receiver.withdraw(self._amount):
            self._executed = True
            self._receiver.transaction_history.append(f"Withdrawal -${self._amount:.2f}")
            return f"Withdrawal of ${self._amount:.2f} executed."
        return "Withdrawal failed due to insufficient funds."

    def undo(self):
        if self._executed:
            self._receiver.deposit(self._amount) # Undo a withdrawal by depositing
            self._receiver.transaction_history.append(f"Withdrawal UNDO +${self._amount:.2f}")
            self._executed = False
            return f"Withdrawal of ${self._amount:.2f} undone."
        return "Withdrawal command not executed or already undone."

# --- IN-MEMORY DATA STORE ---
customer_alice = Customer("Alice")
customer_bob = Customer("Bob")

account_savings = Account("S101", "Alice's Savings", 1000.00, SavingsInterest())
account_current = Account("C202", "Bob's Current", 500.00, CurrentInterest())

# Attach observers (Customer) to subjects (Account)
account_savings.attach(customer_alice)
account_current.attach(customer_bob)

ACCOUNTS = {
    account_savings.account_id: account_savings,
    account_current.account_id: account_current
}
CUSTOMERS = {
    customer_alice.name: customer_alice,
    customer_bob.name: customer_bob
}

# --- FLASK ROUTES (Invoker Role) ---

@app.route('/')
def dashboard():
    """Renders the main dashboard."""
    
    # Calculate interest using the Strategy Pattern for display
    savings_interest = account_savings.calculate_yearly_interest()
    current_interest = account_current.calculate_yearly_interest()
    
    interest_data = {
        "S101": savings_interest,
        "C202": current_interest
    }

    return render_template('index.html', 
        accounts=ACCOUNTS.values(), 
        customers=CUSTOMERS.values(),
        interest_data=interest_data)

@app.route('/transact', methods=['POST'])
def transact():
    """Handles deposit and withdrawal using the Command Pattern."""
    account_id = request.form['account_id']
    transaction_type = request.form['transaction_type']
    amount = float(request.form['amount'])
    
    account = ACCOUNTS.get(account_id)
    
    if account and amount > 0:
        if transaction_type == 'deposit':
            command = DepositCommand(account, amount)
        elif transaction_type == 'withdraw':
            command = WithdrawCommand(account, amount)
        else:
            return redirect(url_for('dashboard'))

        # Invoker: Executes the command
        command.execute() 
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("--- Initial Account Setup ---")
    account_savings.notify("Welcome to your Savings Account!")
    account_current.notify("Welcome to your Current Account!")
    print("----------------------------")
    app.run(debug=True)