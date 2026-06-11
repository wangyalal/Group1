
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);


CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_date DATE NOT NULL,                                       
    description TEXT NOT NULL,                                             
    category VARCHAR(50) NOT NULL,          
    amount DECIMAL(12, 2) NOT NULL,                                        
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('Income', 'Expense')),  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO categories (name) VALUES ('Expense'), ('Income'), ('Category'), ('TIFC');


INSERT INTO transactions (transaction_date, description, category, amount, transaction_type) VALUES 
('2023-02-08', 'Enter a short description...', 'Expense', 10.00, 'Expense'),
('2023-03-29', 'Recent an service', 'Expense', -20.00, 'Expense'),
('2023-04-28', 'Sarninn food', 'Income', 20.00, 'Income'),
('2022-04-27', 'Income banp', 'Income', 30.00, 'Income'),
('2022-04-20', 'Add Payment', 'TIFC', 70.00, 'Income'); 