import {
	Activity,
	BadgePercent,
	BarChart3,
	BrainCircuit,
	CreditCard,
	FileText,
	LayoutDashboard,
	ReceiptText,
	Settings2,
	ShieldAlert,
	Sparkles,
	Users,
	WalletCards,
	Boxes,
} from "lucide-react";

const navigationSections = [
	{
		title: "MAIN",
		links: [
			{ label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
			{ label: "Customers", to: "/customers", icon: Users },
			{ label: "Products", to: "/products", icon: Boxes },
			{ label: "Subscription Plans", to: "/subscription-plans", icon: WalletCards },
			{ label: "Subscriptions", to: "/subscriptions", icon: Activity },
		],
	},
	{
		title: "BILLING",
		links: [
			{ label: "Quotations", to: "/quotations", icon: FileText },
			{ label: "Invoices", to: "/invoices", icon: ReceiptText },
			{ label: "Payments", to: "/payments", icon: CreditCard },
			{ label: "Discounts", to: "/discounts", icon: BadgePercent },
			{ label: "Taxes", to: "/taxes", icon: Settings2 },
		],
	},
	{
		title: "INTELLIGENCE",
		links: [
			{ label: "AI Intelligence", to: "/ai", icon: BrainCircuit },
			{ label: "Revenue Insights", to: "/ai/revenue-insights", icon: BarChart3 },
			{ label: "Revenue Leakage", to: "/ai/leakage", icon: ShieldAlert },
			{ label: "Churn Risk", to: "/ai/churn-risk", icon: Activity },
			{ label: "Revenue Forecast", to: "/ai/forecast", icon: Sparkles },
		],
	},
];

function Sidebar() {
	const currentPath = window.location.pathname;
	const isActivePath = (path: string) => currentPath === path || (path === "/dashboard" && currentPath === "/");

	return (
		<aside className="fixed inset-y-0 left-0 z-40 flex h-screen w-[250px] flex-col border-r border-[#007BA7]/20 bg-[#0A0A0C] text-[#F5F5F7] shadow-[8px_0_34px_rgba(0,0,0,0.3),1px_0_18px_rgba(0,123,167,0.07)]">
			<div className="flex h-[76px] shrink-0 items-center border-b border-[#17171C] bg-[#0D0D10] px-5">
				<a href="/dashboard" aria-label="SubscriptIQ dashboard" className="text-[21px] font-semibold tracking-tight">
					Subscript<span className="text-[#007BA7] drop-shadow-[0_0_10px_rgba(0,123,167,0.65)]">IQ</span>
				</a>
			</div>

			<nav aria-label="Main navigation" className="min-h-0 flex-1 overflow-y-auto px-3 py-5">
				<div className="space-y-6">
					{navigationSections.map((section) => (
						<section key={section.title} aria-label={section.title}>
							<h2 className="mb-2 px-3 text-[10px] font-semibold tracking-[0.12em] text-[#92929D]">
								{section.title}
							</h2>
							<ul className="space-y-1">
								{section.links.map(({ label, to, icon: Icon }) => (
									<li key={to}>
										<a
											href={to}
											aria-current={isActivePath(to) ? "page" : undefined}
											className={`group relative flex min-h-10 items-center gap-3 rounded-md px-3 text-[13px] transition-all duration-200 ${
												isActivePath(to)
													? to.startsWith("/ai")
														? "bg-[#007BA7]/[0.13] font-medium text-[#F5F5F7] shadow-[inset_0_0_22px_rgba(0,123,167,0.12),0_0_15px_rgba(0,123,167,0.16),0_0_16px_rgba(255,46,147,0.11)] before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:bg-[#FF2E93] before:shadow-[0_0_10px_rgba(255,46,147,0.9)]"
														: "bg-[#007BA7]/[0.14] font-medium text-[#F5F5F7] shadow-[inset_0_0_22px_rgba(0,123,167,0.12),0_0_17px_rgba(0,123,167,0.2)] before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:bg-[#007BA7] before:shadow-[0_0_11px_rgba(0,123,167,1)]"
													: "text-[#92929D] hover:bg-[#17171C] hover:text-[#F5F5F7] hover:shadow-[inset_0_0_12px_rgba(0,123,167,0.06)]"
											}`}
										>
											<Icon aria-hidden="true" size={17} strokeWidth={1.8} className={`shrink-0 transition-all duration-200 group-hover:brightness-150 group-hover:drop-shadow-[0_0_7px_rgba(0,123,167,0.8)] ${to.startsWith("/ai") ? "text-[#FF2E93]/75 group-hover:text-[#FF2E93] group-hover:drop-shadow-[0_0_8px_rgba(255,46,147,0.85)]" : "group-hover:text-[#007BA7]"}`} />
											<span className="truncate">{label}</span>
										</a>
									</li>
								))}
							</ul>
						</section>
					))}
				</div>
			</nav>

			<footer className="shrink-0 border-t border-[#17171C] px-5 py-4">
				<div className="flex items-center gap-3">
					<div className="flex size-9 shrink-0 items-center justify-center rounded-md border border-[#FF2E93]/20 bg-[#FF2E93]/[0.07] text-[#FF2E93] shadow-[0_0_16px_rgba(255,46,147,0.08)]">
						<Sparkles aria-hidden="true" size={16} strokeWidth={1.8} />
					</div>
					<div className="min-w-0">
						<p className="truncate text-xs font-medium text-[#F5F5F7]">SubscriptIQ</p>
						<p className="mt-0.5 truncate text-[11px] text-[#92929D]">AI-Powered Billing</p>
					</div>
				</div>
			</footer>
		</aside>
	);
}

export default Sidebar;
