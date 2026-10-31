/**
 * SubscriptIQ Frontend API Client.
 *
 * Connects frontend dashboard, customer, subscription, invoice, payment,
 * and AI revenue intelligence views to actual FastAPI backend endpoints.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
		...(options.headers as Record<string, string>),
	};

	const token = localStorage.getItem("subscriptiq_token");
	if (token) {
		headers["Authorization"] = `Bearer ${token}`;
	}

	const response = await fetch(url, {
		...options,
		headers,
	});

	if (!response.ok) {
		let errorMsg = `HTTP Error ${response.status}`;
		try {
			const errData = await response.json();
			if (errData && errData.detail) {
				errorMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
			}
		} catch {
			// keep fallback errorMsg
		}
		throw new Error(errorMsg);
	}

	return response.json();
}

export const api = {
	// Dashboard & Financial Analytics
	getDashboardAnalytics: () => request<any>("/api/analytics/dashboard"),

	// Customers
	getCustomers: () => request<any[]>("/api/customers"),
	createCustomer: (data: any) => request<any>("/api/customers", { method: "POST", body: JSON.stringify(data) }),

	// Subscriptions
	getSubscriptions: () => request<any>("/api/subscriptions"),
	createSubscription: (data: any) => request<any>("/api/subscriptions", { method: "POST", body: JSON.stringify(data) }),

	// Invoices & PDF
	getInvoices: () => request<any[]>("/api/invoices"),
	getInvoicePdfUrl: (invoiceId: number | string) => `${API_BASE_URL}/api/invoices/${invoiceId}/pdf`,

	// Payments
	getPayments: () => request<any[]>("/api/payments"),

	// AI Revenue Intelligence Endpoints
	getForecast: (monthsAhead: number = 6) => request<any>(`/api/ai/forecast?months_ahead=${monthsAhead}`),
	getLeakageAlerts: (statusFilter?: string) =>
		request<any>(`/api/ai/leakage-alerts${statusFilter ? `?status_filter=${statusFilter}` : ""}`),
	getHealthScore: () => request<any>("/api/ai/health-score"),
	getChurnRisk: (customerId?: number) =>
		request<any>(`/api/ai/churn-risk${customerId ? `?customer_id=${customerId}` : ""}`),
	auditInvoice: (invoiceId?: number) =>
		request<any>("/api/ai/audit-invoice", {
			method: "POST",
			body: JSON.stringify(invoiceId ? { invoice_id: invoiceId, update_model: true } : { update_model: true }),
		}),

	// Demonstration Seeder
	seedDemoData: () => request<any>("/api/seed-demo-data", { method: "POST" }),

	// Authentication (Member 2)
	login: (credentials: { email: string; password: string }) =>
		request<any>("/auth/login", { method: "POST", body: JSON.stringify(credentials) }),
	register: (userData: { name: string; email: string; password: string }) =>
		request<any>("/auth/register", { method: "POST", body: JSON.stringify(userData) }),
	getProfile: () => request<any>("/auth/me"),
};
