
CREATE TABLE business_health_snapshots (
	id INTEGER NOT NULL, 
	snapshot_date DATE NOT NULL, 
	mrr NUMERIC(12, 2) NOT NULL, 
	arr NUMERIC(12, 2) NOT NULL, 
	active_subscriptions_count INTEGER NOT NULL, 
	total_outstanding_amount NUMERIC(12, 2) NOT NULL, 
	overdue_invoices_count INTEGER NOT NULL, 
	health_score NUMERIC(5, 2) NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE discounts (
	id INTEGER NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	discount_type VARCHAR(20) NOT NULL, 
	value NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3), 
	min_purchase_amount NUMERIC(12, 2) NOT NULL, 
	min_quantity INTEGER NOT NULL, 
	max_discount_amount NUMERIC(12, 2), 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	max_uses INTEGER, 
	current_uses INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	applicable_plan_id INTEGER, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE products (
	id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	price NUMERIC(12, 2) NOT NULL, 
	billing_interval VARCHAR(20) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE tax_rules (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	rate_percentage NUMERIC(5, 2) NOT NULL, 
	tax_type VARCHAR(20) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	state_province VARCHAR(100), 
	is_active BOOLEAN NOT NULL, 
	is_compound BOOLEAN NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	hashed_password VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255), 
	role VARCHAR(50) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE customers (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	company_name VARCHAR(255), 
	billing_address TEXT, 
	tax_id VARCHAR(64), 
	currency VARCHAR(3) NOT NULL, 
	is_tax_exempt BOOLEAN NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)

;


CREATE TABLE password_reset_tokens (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;


CREATE TABLE subscriptions (
	id INTEGER NOT NULL, 
	subscription_number VARCHAR(64) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	billing_interval VARCHAR(20) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	quantity INTEGER NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	start_date DATE NOT NULL, 
	current_period_start DATE NOT NULL, 
	current_period_end DATE NOT NULL, 
	next_billing_date DATE NOT NULL, 
	auto_renew BOOLEAN NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(plan_id) REFERENCES products (id) ON DELETE RESTRICT
)

;


CREATE TABLE invoices (
	id INTEGER NOT NULL, 
	invoice_number VARCHAR(64) NOT NULL, 
	subscription_id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	billing_period_start DATE NOT NULL, 
	billing_period_end DATE NOT NULL, 
	issue_date DATE NOT NULL, 
	due_date DATE NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	discount_id INTEGER, 
	tax_amount NUMERIC(12, 2) NOT NULL, 
	tax_rule_id INTEGER, 
	tax_rate_applied NUMERIC(5, 2), 
	total_amount NUMERIC(12, 2) NOT NULL, 
	amount_paid NUMERIC(12, 2) NOT NULL, 
	amount_due NUMERIC(12, 2) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	pdf_path VARCHAR(500), 
	is_audited BOOLEAN NOT NULL, 
	audit_discrepancy_notes TEXT, 
	notes TEXT, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_invoice_subscription_period UNIQUE (subscription_id, billing_period_start, billing_period_end), 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE RESTRICT, 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(discount_id) REFERENCES discounts (id) ON DELETE SET NULL, 
	FOREIGN KEY(tax_rule_id) REFERENCES tax_rules (id) ON DELETE SET NULL
)

;


CREATE TABLE invoice_items (
	id INTEGER NOT NULL, 
	invoice_id INTEGER NOT NULL, 
	product_id INTEGER, 
	description VARCHAR(255) NOT NULL, 
	quantity NUMERIC(10, 2) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	tax_amount NUMERIC(12, 2) NOT NULL, 
	total_price NUMERIC(12, 2) NOT NULL, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL
)

;


CREATE TABLE payments (
	id INTEGER NOT NULL, 
	payment_reference VARCHAR(64) NOT NULL, 
	invoice_id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	payment_method VARCHAR(30) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	transaction_reference VARCHAR(128), 
	payment_date DATETIME DEFAULT now() NOT NULL, 
	receipt_number VARCHAR(64), 
	failure_reason TEXT, 
	notes TEXT, 
	created_at DATETIME DEFAULT now() NOT NULL, 
	updated_at DATETIME DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id) ON DELETE RESTRICT, 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT
)

;


CREATE TABLE revenue_leakage_alerts (
	id INTEGER NOT NULL, 
	leakage_type VARCHAR(50) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	estimated_loss NUMERIC(12, 2) NOT NULL, 
	subscription_id INTEGER, 
	customer_id INTEGER, 
	invoice_id INTEGER, 
	description TEXT NOT NULL, 
	recommended_action TEXT, 
	status VARCHAR(20) NOT NULL, 
	detected_at DATETIME DEFAULT now() NOT NULL, 
	resolved_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id) ON DELETE SET NULL
)

;

