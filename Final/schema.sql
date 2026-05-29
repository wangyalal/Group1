
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);


CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_date DATE NOT NULL,                                       
    description TEXT NOT NULL,                                             
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,          
    amount DECIMAL(12, 2) NOT NULL,                                        
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('Income', 'Expense')), 
    entry_method VARCHAR(15) CHECK (entry_method IN ('Manual', 'Chat Box')), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO categories (name) VALUES ('Expense'), ('Income'), ('Category'), ('TIFC');


INSERT INTO transactions (transaction_date, description, category_id, amount, transaction_type, entry_method) VALUES 
('2023-02-08', 'Enter a short description...', 1, 10.00, 'Expense', 'Manual'),
('2023-03-29', 'Recent an service', 1, -20.00, 'Expense', 'Manual'),
('2023-04-28', 'Sarninn food', 3, 20.00, 'Income', 'Manual'),
('2022-04-27', 'Income banp', 3, 30.00, 'Income', 'Manual'),
('2022-04-20', 'Add Payment', 4, 70.00, 'Income', 'Chat Box'); 