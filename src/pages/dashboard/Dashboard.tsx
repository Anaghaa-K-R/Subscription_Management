import {
	Activity,
	AlertTriangle,
	ArrowDownRight,
	ArrowUpRight,
	BrainCircuit,
	CalendarDays,
	CheckCircle2,
	CreditCard,
	Sparkles,
	Users,
	Wallet,
} from "lucide-react";
import {
	Area,
	AreaChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import MainLayout from "../../component/layout/MainLayout";

const monthlyRevenue = [
	{ month: "Jan", revenue: 482 },
	{ month: "Feb", revenue: 510 },
	{ month: "Mar", revenue: 496 },
	{ month: "Apr", revenue: 568 },
	{ month: "May", revenue: 604 },
	{ month: "Jun", revenue: 592 },
	{ month: "Jul", revenue: 664 },
	{ month: "Aug", revenue: 701 },
	{ month: "Sep", revenue: 738 },
	{ month: "Oct", revenue: 776 },
	{ month: "Nov", revenue: 804 },
	{ month: "Dec", revenue: 842 },
];

const kpis = [
	{
		label: "Monthly Recurring Revenue",
		value: "₹8.42L",
		change: "+18.6%",
		icon: Wallet,
		accent: "blue",
		trend: "up",
	},
	{
		label: "Active Subscriptions",
		value: "1,248",
		change: "+12.4%",
		icon: Users,
		accent: "blue",
		trend: "up",
	},
	{
		label: "Revenue Growth",
		value: "+18.6%",
		change: "vs last month",
		icon: Activity,
		accent: "pink",
		trend: "up",
	},
	{
		label: "Pending Invoices",
		value: "37",
		change: "8 overdue",
		icon: CreditCard,
		accent: "amber",
		trend: "warning",
	},
] as const;

const subscriptionHealth = [
	{ label: "Active", value: "1,248", color: "bg-[#007BA7]", text: "text-[#F5F5F7]" },
	{ label: "Trial", value: "86", color: "bg-[#22C55E]", text: "text-[#22C55E]" },
	{ label: "At Risk", value: "42", color: "bg-[#FF2E93]", text: "text-[#FF2E93]" },
	{ label: "Cancelled", value: "19", color: "bg-[#92929D]/50", text: "text-[#92929D]" },
];

type KpiCardProps = (typeof kpis)[number];

function KpiCard({ label, value, change, icon: Icon, accent, trend }: KpiCardProps) {
	const accentStyles = {
		blue: {
			border: "border-[#007BA7]/25 hover:border-[#007BA7]/55",
			icon: "border-[#007BA7]/30 bg-[#007BA7]/[0.10] text-[#38BDF8] shadow-[0_0_18px_rgba(0,123,167,0.18)]",
			value: "drop-shadow-[0_0_13px_rgba(0,123,167,0.22)]",
			glow: "group-hover:shadow-[0_0_30px_rgba(0,123,167,0.15)]",
		},
		pink: {
			border: "border-[#FF2E93]/25 hover:border-[#FF2E93]/55",
			icon: "border-[#FF2E93]/30 bg-[#FF2E93]/[0.09] text-[#FF2E93] shadow-[0_0_18px_rgba(255,46,147,0.16)]",
			value: "drop-shadow-[0_0_13px_rgba(255,46,147,0.24)]",
			glow: "group-hover:shadow-[0_0_30px_rgba(255,46,147,0.14)]",
		},
		amber: {
			border: "border-[#F59E0B]/20 hover:border-[#F59E0B]/45",
			icon: "border-[#F59E0B]/25 bg-[#F59E0B]/[0.08] text-[#F59E0B] shadow-[0_0_16px_rgba(245,158,11,0.12)]",
			value: "drop-shadow-[0_0_12px_rgba(245,158,11,0.18)]",
			glow: "group-hover:shadow-[0_0_28px_rgba(245,158,11,0.11)]",
		},
	};
	const styles = accentStyles[accent];
	const isWarning = trend === "warning";

	return (
		<article className={`group relative min-w-0 overflow-hidden rounded-lg border bg-[#17171C]/95 p-5 shadow-[0_12px_30px_rgba(0,0,0,0.22)] transition duration-300 hover:-translate-y-1 ${styles.border} ${styles.glow} motion-reduce:transform-none motion-reduce:transition-none sm:p-5`}>
			<div className="absolute inset-x-5 top-0 h-px bg-gradient-to-r from-transparent via-white/[0.12] to-transparent" />
			<div className="flex items-start justify-between gap-3">
				<p className="text-[12px] font-medium leading-5 text-[#92929D]">{label}</p>
				<div className={`flex size-9 shrink-0 items-center justify-center rounded-md border ${styles.icon}`}>
					<Icon aria-hidden="true" size={17} strokeWidth={1.8} />
				</div>
			</div>
			<p className={`mt-5 text-[30px] font-semibold leading-none text-[#F5F5F7] sm:text-[32px] ${styles.value}`}>
				{value}
			</p>
			<div className="mt-4 flex min-h-5 items-center gap-1.5 text-[11px]">
				{isWarning ? (
					<AlertTriangle aria-hidden="true" size={13} className="text-[#F59E0B]" />
				) : change.startsWith("+") ? (
					<ArrowUpRight aria-hidden="true" size={14} className="text-[#22C55E]" />
				) : null}
				<span className={isWarning ? "text-[#F59E0B]" : change.startsWith("+") ? "text-[#22C55E]" : "text-[#92929D]"}>
					{change}
				</span>
			</div>
		</article>
	);
}

function StatusRow({ label, value, color, text }: (typeof subscriptionHealth)[number]) {
	return (
		<div className="flex items-center justify-between gap-3 py-2.5">
			<div className="flex min-w-0 items-center gap-2.5">
				<span className={`size-1.5 shrink-0 rounded-full ${color}`} />
				<span className="truncate text-[13px] text-[#92929D]">{label}</span>
			</div>
			<span className={`text-sm font-semibold tabular-nums ${text}`}>{value}</span>
		</div>
	);
}

function Dashboard() {
	const period = new Intl.DateTimeFormat("en", { month: "long", year: "numeric" }).format(new Date());

	return (
		<MainLayout>
			<div className="mx-auto min-h-screen w-full max-w-[1600px] px-5 py-7 text-[#F5F5F7] sm:px-8 sm:py-9 lg:px-11 lg:py-10">
				<header className="relative isolate mb-7 flex flex-wrap items-end justify-between gap-5 overflow-hidden border-b border-[#17171C] bg-[radial-gradient(ellipse_at_12%_30%,rgba(0,123,167,0.17),transparent_48%),radial-gradient(ellipse_at_88%_0%,rgba(255,46,147,0.10),transparent_38%)] pb-6 sm:mb-8 sm:pb-7">
					<div>
						<div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#92929D]">
							<span className="h-px w-7 bg-[#007BA7] shadow-[0_0_10px_2px_rgba(0,123,167,0.6)]" />
							Financial overview
						</div>
						<h1 className="text-[32px] font-bold leading-tight text-[#F5F5F7] drop-shadow-[0_0_22px_rgba(0,123,167,0.20)] sm:text-[38px]">
							Dashboard
						</h1>
						<p className="mt-2 text-sm text-[#92929D]">Welcome back to SubscriptIQ</p>
					</div>
					<div className="inline-flex items-center gap-2.5 rounded-md border border-[#17171C] bg-[#111115]/90 px-3.5 py-2.5 text-xs text-[#92929D] shadow-[0_0_18px_rgba(0,123,167,0.07)]">
						<CalendarDays aria-hidden="true" size={15} className="text-[#38BDF8]" />
						<span className="text-[#F5F5F7]">{period}</span>
					</div>
				</header>

				<section aria-label="Key performance indicators" className="mb-7 grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:mb-8 xl:grid-cols-4 xl:gap-4">
					{kpis.map((kpi) => <KpiCard key={kpi.label} {...kpi} />)}
				</section>

				<section className="mb-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.8fr)_minmax(300px,0.9fr)]">
					<article className="min-w-0 overflow-hidden rounded-lg border border-[#007BA7]/20 bg-[#17171C]/95 p-5 shadow-[0_12px_34px_rgba(0,0,0,0.24),0_0_26px_rgba(0,123,167,0.07)] sm:p-6">
						<div className="mb-6 flex flex-wrap items-start justify-between gap-4">
							<div>
								<h2 className="text-base font-semibold text-[#F5F5F7]">Revenue Overview</h2>
								<p className="mt-1 text-xs text-[#92929D]">Recurring revenue performance</p>
							</div>
							<div className="flex items-center gap-2 text-[11px] text-[#92929D]">
								<span className="size-1.5 rounded-full bg-[#007BA7] shadow-[0_0_8px_rgba(0,123,167,0.9)]" />
								Revenue
							</div>
						</div>
						<div className="h-[250px] w-full min-w-0 sm:h-[285px]">
							<ResponsiveContainer width="100%" height="100%">
								<AreaChart data={monthlyRevenue} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
									<defs>
										<linearGradient id="revenueArea" x1="0" y1="0" x2="0" y2="1">
											<stop offset="0%" stopColor="#007BA7" stopOpacity={0.34} />
											<stop offset="92%" stopColor="#007BA7" stopOpacity={0.01} />
										</linearGradient>
										<filter id="revenueLineGlow" x="-20%" y="-50%" width="140%" height="200%">
											<feGaussianBlur stdDeviation="3" result="blur" />
											<feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
										</filter>
									</defs>
									<CartesianGrid stroke="#92929D" strokeOpacity={0.12} vertical={false} />
									<XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#92929D", fontSize: 11 }} dy={10} />
									<YAxis axisLine={false} tickLine={false} tick={{ fill: "#92929D", fontSize: 11 }} tickFormatter={(value: number) => `₹${value}`} width={48} />
									<Tooltip
										formatter={(value) => [`₹${Number(value).toLocaleString("en-IN")}K`, "Revenue"]}
										contentStyle={{ background: "#111115", border: "1px solid rgba(0,123,167,0.35)", borderRadius: 6, color: "#F5F5F7", boxShadow: "0 0 18px rgba(0,123,167,0.12)" }}
										labelStyle={{ color: "#92929D", marginBottom: 4 }}
										cursor={{ stroke: "#92929D", strokeOpacity: 0.25 }}
									/>
									<Area
										type="monotone"
										dataKey="revenue"
										stroke="#159DCA"
										strokeWidth={2.5}
										fill="url(#revenueArea)"
										activeDot={{ r: 5, fill: "#F5F5F7", stroke: "#007BA7", strokeWidth: 3 }}
										style={{ filter: "url(#revenueLineGlow)" }}
										isAnimationActive
										animationDuration={900}
									/>
								</AreaChart>
							</ResponsiveContainer>
						</div>
					</article>

					<article className="group relative isolate flex min-w-0 flex-col overflow-hidden rounded-lg border border-[#FF2E93]/30 bg-[#17171C] p-5 shadow-[0_0_30px_rgba(255,46,147,0.08),0_14px_36px_rgba(0,0,0,0.28)] transition duration-300 hover:border-[#FF2E93]/50 hover:shadow-[0_0_36px_rgba(255,46,147,0.14),0_0_40px_rgba(0,123,167,0.09)] motion-reduce:transition-none sm:p-6">
						<div className="pointer-events-none absolute -right-10 -top-10 -z-10 size-40 rounded-full bg-[#FF2E93]/[0.08] blur-3xl transition duration-500 group-hover:bg-[#FF2E93]/[0.13] motion-reduce:transition-none" />
						<div className="mb-7 flex items-center justify-between gap-3">
							<div className="relative flex size-11 items-center justify-center rounded-md border border-[#FF2E93]/35 bg-[#FF2E93]/[0.09] text-[#FF2E93] shadow-[0_0_20px_rgba(255,46,147,0.2)]">
								<span className="absolute inset-0 rounded-md border border-[#FF2E93]/35 motion-safe:animate-pulse motion-reduce:animate-none" />
								<BrainCircuit aria-hidden="true" size={21} />
							</div>
							<span className="inline-flex items-center gap-1.5 rounded-sm border border-[#FF2E93]/30 bg-[#FF2E93]/[0.08] px-2 py-1 text-[9px] font-semibold tracking-[0.12em] text-[#FF80BC]">
								<Sparkles aria-hidden="true" size={11} /> AI INSIGHT
							</span>
						</div>
						<div className="mb-3 flex items-center gap-2">
							<span className="h-px w-5 bg-[#FF2E93] shadow-[0_0_8px_rgba(255,46,147,0.7)]" />
							<span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#FF80BC]">Intelligence layer</span>
						</div>
						<h2 className="text-lg font-semibold text-[#F5F5F7]">AI Revenue Intelligence</h2>
						<p className="mt-3 text-[13px] leading-6 text-[#B5B5BE]">
							Revenue is trending upward. AI detected an <span className="font-semibold text-[#FF80BC] drop-shadow-[0_0_9px_rgba(255,46,147,0.3)]">18.6% growth opportunity</span> based on subscription activity and payment patterns.
						</p>
						<div className="mt-auto flex items-center gap-2 border-t border-[#29232C] pt-5 text-[11px] text-[#92929D]">
							<span className="size-1.5 rounded-full bg-[#22C55E] shadow-[0_0_8px_rgba(34,197,94,0.7)]" />
							Insight updated today
						</div>
					</article>
				</section>

				<section aria-label="Subscription and revenue health" className="grid grid-cols-1 gap-4 lg:grid-cols-2">
					<article className="min-w-0 rounded-lg border border-[#202027] bg-[#17171C]/95 p-5 shadow-[0_12px_30px_rgba(0,0,0,0.2)] sm:p-6">
						<div className="mb-4 flex items-center justify-between gap-3 border-b border-[#24242B] pb-4">
							<div>
								<h2 className="text-sm font-semibold text-[#F5F5F7]">Subscription Health</h2>
								<p className="mt-1 text-[11px] text-[#92929D]">Current subscriber mix</p>
							</div>
							<Users aria-hidden="true" size={17} className="text-[#38BDF8]" />
						</div>
						<div className="divide-y divide-[#24242B]">
							{subscriptionHealth.map((status) => <StatusRow key={status.label} {...status} />)}
						</div>
					</article>

					<article className="min-w-0 rounded-lg border border-[#F59E0B]/20 bg-[#17171C]/95 p-5 shadow-[0_12px_30px_rgba(0,0,0,0.2)] sm:p-6">
						<div className="mb-4 flex items-center justify-between gap-3 border-b border-[#24242B] pb-4">
							<div>
								<h2 className="text-sm font-semibold text-[#F5F5F7]">Revenue Leakage Monitor</h2>
								<p className="mt-1 text-[11px] text-[#92929D]">Payment exceptions requiring attention</p>
							</div>
							<div className="flex size-8 items-center justify-center rounded-md border border-[#F59E0B]/25 bg-[#F59E0B]/[0.08] text-[#F59E0B] shadow-[0_0_14px_rgba(245,158,11,0.12)]">
								<AlertTriangle aria-hidden="true" size={16} />
							</div>
						</div>
						<div className="mb-3 flex items-baseline gap-2 border-b border-[#24242B] pb-4">
							<span className="text-[26px] font-semibold text-[#F5F5F7] drop-shadow-[0_0_12px_rgba(245,158,11,0.18)]">₹42,800</span>
							<span className="text-[11px] text-[#92929D]">potential leakage</span>
						</div>
						<div className="divide-y divide-[#24242B]">
							<div className="flex items-center justify-between gap-3 py-2.5">
								<span className="text-[13px] text-[#92929D]">Overdue invoices</span>
								<span className="flex items-center gap-1.5 text-sm font-semibold tabular-nums text-[#F59E0B]"><AlertTriangle aria-hidden="true" size={13} />8</span>
							</div>
							<div className="flex items-center justify-between gap-3 py-2.5">
								<span className="text-[13px] text-[#92929D]">Failed payments</span>
								<span className="flex items-center gap-1.5 text-sm font-semibold tabular-nums text-[#FF2E93]"><ArrowDownRight aria-hidden="true" size={14} />13</span>
							</div>
						</div>
						<div className="mt-3 flex items-center gap-2 text-[10px] text-[#92929D]">
							<CheckCircle2 aria-hidden="true" size={13} className="text-[#22C55E]" />
							Monitoring payment activity
						</div>
					</article>
				</section>
			</div>
		</MainLayout>
	);
}

export default Dashboard;
