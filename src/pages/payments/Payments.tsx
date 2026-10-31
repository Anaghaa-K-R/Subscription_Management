import { useState, useEffect } from "react";
import {
	ArrowDownUp,
	ArrowUpRight,
	Activity,
	CalendarClock,
	Check,
	ChevronDown,
	CircleAlert,
	Clock3,
	CreditCard,
	Ellipsis,
	Landmark,
	Plus,
	Search,
	Smartphone,
} from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import MainLayout from "../../component/layout/MainLayout";
import { api } from "../../services/api";

type PaymentStatus = "Successful" | "Pending" | "Failed";
type StatusFilter = "All payments" | PaymentStatus;
type PaymentMethod = "Card" | "UPI" | "Bank transfer" | "Net banking";

interface Payment {
	id: string;
	customer: string;
	invoice: string;
	date: string;
	amount: number;
	method: PaymentMethod;
	status: PaymentStatus;
	initials: string;
}

const statusFilters: StatusFilter[] = ["All payments", "Successful", "Pending", "Failed"];

const statusStyles: Record<PaymentStatus, string> = {
	Successful: "border-[#22C55E]/20 bg-[#22C55E]/[0.08] text-[#4ADE80]",
	Pending: "border-[#F59E0B]/25 bg-[#F59E0B]/[0.08] text-[#FBBF24]",
	Failed: "border-[#FF2E93]/25 bg-[#FF2E93]/[0.08] text-[#FF80BC]",
};

const avatarStyles = [
	"bg-[#007BA7]/15 text-[#38BDF8]",
	"bg-[#FF2E93]/10 text-[#FF80BC]",
	"bg-[#22C55E]/10 text-[#4ADE80]",
	"bg-[#F59E0B]/10 text-[#FBBF24]",
];

const methodIcons: Record<PaymentMethod, typeof CreditCard> = {
	Card: CreditCard,
	UPI: Smartphone,
	"Bank transfer": Landmark,
	"Net banking": Landmark,
};

const paymentMethodOptions: PaymentMethod[] = ["Card", "UPI", "Bank transfer", "Net banking"];

const paymentStatusStyles: Record<PaymentStatus, { color: string; icon: typeof Check }> = {
	Successful: { color: "#22C55E", icon: Check },
	Pending: { color: "#F59E0B", icon: Clock3 },
	Failed: { color: "#FF2E93", icon: CircleAlert },
};

function Payments() {
	const [payments, setPayments] = useState<Payment[]>([]);
	const [searchTerm, setSearchTerm] = useState("");
	const [activeFilter, setActiveFilter] = useState<StatusFilter>("All payments");

	useEffect(() => {
		let isMounted = true;
		api.getPayments()
			.then((data) => {
				if (isMounted) {
					setPayments(data);
				}
			})
			.catch((err) => {
				console.error("Failed to load payments:", err);
			});
		return () => {
			isMounted = false;
		};
	}, []);

	const filteredPayments = payments.filter((payment) => {
		const matchesStatus = activeFilter === "All payments" || payment.status === activeFilter;
		const query = searchTerm.trim().toLowerCase();
		const matchesSearch = !query || [payment.id, payment.customer, payment.invoice, payment.method].some((value) => value.toLowerCase().includes(query));
		return matchesStatus && matchesSearch;
	});
	const successfulCount = payments.filter((payment) => payment.status === "Successful").length;
	const pendingCount = payments.filter((payment) => payment.status === "Pending").length;
	const failedCount = payments.filter((payment) => payment.status === "Failed").length;
	const successRate = payments.length > 0 ? Math.round((successfulCount / payments.length) * 100) : null;
	const collectedTotal = payments
		.filter((payment) => payment.status === "Successful")
		.reduce((total, payment) => total + payment.amount, 0);
	const hasPaymentData = payments.length > 0;
	const statusDistribution = [
		{ name: "Successful", value: successfulCount, color: "#22C55E" },
		{ name: "Pending", value: pendingCount, color: "#F59E0B" },
		{ name: "Failed", value: failedCount, color: "#FF2E93" },
	];
	const methodDistribution = paymentMethodOptions.map((method) => ({
		method,
		count: payments.filter((payment) => payment.method === method).length,
	}));

	return (
		<MainLayout>
			<div className="mx-auto min-h-screen w-full max-w-[1600px] overflow-x-hidden px-5 py-7 text-[#F5F5F7] sm:px-8 sm:py-9 lg:px-11 lg:py-10">
				<style>{"@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }"}</style>
				<header className="mb-7 flex flex-wrap items-end justify-between gap-5 border-b border-[#17171C] bg-[radial-gradient(ellipse_at_8%_30%,rgba(0,123,167,0.14),transparent_48%)] pb-6 sm:mb-8 sm:pb-7">
					<div>
						<div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#92929D]">
							<span className="h-px w-7 bg-[#007BA7] shadow-[0_0_10px_2px_rgba(0,123,167,0.65)]" />
							Transaction monitoring
						</div>
						<h1 className="text-[32px] font-bold leading-tight text-[#F5F5F7] drop-shadow-[0_0_20px_rgba(0,123,167,0.2)] sm:text-[38px]">Payments</h1>
						<p className="mt-2 text-sm text-[#92929D]">Track incoming payments and payment activity</p>
					</div>
					<button type="button" className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[#159DCA]/60 bg-[#007BA7] px-4 text-[13px] font-semibold text-white shadow-[0_0_20px_rgba(0,123,167,0.24),inset_0_1px_0_rgba(255,255,255,0.15)] transition hover:border-[#38BDF8] hover:bg-[#078AB8] hover:shadow-[0_0_26px_rgba(0,123,167,0.4)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#38BDF8] motion-reduce:transition-none">
						<Plus aria-hidden="true" size={16} />Record Payment
					</button>
				</header>

				<section aria-label="Payment activity monitoring" className="mb-5 overflow-hidden rounded-lg border border-[#007BA7]/25 bg-[#17171C]/95 shadow-[0_16px_40px_rgba(0,0,0,0.27),0_0_28px_rgba(0,123,167,0.08)]">
					<div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#25252C] px-5 py-5 sm:px-6">
						<div className="flex items-start gap-3">
							<div className="flex size-10 shrink-0 items-center justify-center rounded-md border border-[#007BA7]/30 bg-[#007BA7]/[0.09] text-[#38BDF8] shadow-[0_0_18px_rgba(0,123,167,0.15)]"><Activity aria-hidden="true" size={19} /></div>
							<div><h2 className="text-base font-semibold text-[#F5F5F7]">Payment Activity</h2><p className="mt-1 text-[11px] text-[#92929D]">Transaction health and settlement performance</p></div>
						</div>
						<div className="inline-flex items-center gap-2 rounded-md border border-[#25252C] bg-[#101014] px-3 py-2 text-[10px] text-[#92929D]"><CalendarClock aria-hidden="true" size={13} className="text-[#38BDF8]" />All activity</div>
					</div>
					<div className="grid grid-cols-1 divide-y divide-[#25252C] md:grid-cols-[minmax(230px,0.8fr)_minmax(0,1.5fr)] md:divide-x md:divide-y-0">
						<div className="flex flex-col items-center justify-center px-5 py-6 sm:flex-row sm:gap-6 md:flex-col md:gap-1 lg:flex-row lg:gap-6">
							<div className="relative size-[172px] shrink-0 motion-safe:animate-[fadeIn_700ms_ease-out_both] motion-reduce:animate-none">
								<ResponsiveContainer width="100%" height="100%">
									<PieChart>
										<Pie data={statusDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={58} outerRadius={76} paddingAngle={4} stroke="none" isAnimationActive animationDuration={900}>
											{statusDistribution.map((status) => <Cell key={status.name} fill={status.color} />)}
										</Pie>
										<Tooltip contentStyle={{ background: "#111115", border: "1px solid rgba(0,123,167,0.35)", borderRadius: 6, color: "#F5F5F7" }} />
									</PieChart>
								</ResponsiveContainer>
								<div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
									<span className="text-[28px] font-semibold leading-none text-[#F5F5F7]">{successRate === null ? "—" : `${successRate}%`}</span>
									<span className="mt-1.5 text-[9px] uppercase tracking-[0.12em] text-[#92929D]">success rate</span>
								</div>
								{!hasPaymentData && <span className="absolute inset-x-0 -bottom-1 text-center text-[9px] text-[#777783]">No transaction data</span>}
							</div>
							<div className="mt-5 grid w-full grid-cols-3 gap-3 sm:mt-0 md:mt-4 md:w-full lg:mt-0">
								{statusDistribution.map(({ name, value, color }) => {
									const StatusIcon = paymentStatusStyles[name as PaymentStatus].icon;
									return <div key={name} className="min-w-0 text-center"><div className="mx-auto mb-2 flex size-8 items-center justify-center rounded-md border" style={{ color, borderColor: `${color}40`, backgroundColor: `${color}12` }}><StatusIcon aria-hidden="true" size={14} /></div><p className="text-lg font-semibold tabular-nums text-[#F5F5F7]">{hasPaymentData ? value : "—"}</p><p className="mt-0.5 truncate text-[9px] text-[#92929D]">{name}</p></div>;
								})}
							</div>
						</div>
						<div className="flex flex-col justify-center px-5 py-5 sm:px-6">
							<div className="mb-5 flex flex-wrap items-end justify-between gap-3">
								<div><p className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#92929D]">Collected via successful transactions</p><p className="mt-2 text-[32px] font-semibold leading-none text-[#F5F5F7]">{hasPaymentData ? `₹${collectedTotal.toLocaleString("en-IN")}` : "—"}</p></div>
								<span className="inline-flex items-center gap-1.5 rounded-sm border border-[#007BA7]/20 bg-[#007BA7]/[0.07] px-2 py-1 text-[9px] font-medium text-[#69C9EB]"><Activity aria-hidden="true" size={11} />Transaction health</span>
							</div>
							<div className="grid grid-cols-3 gap-2">
								{statusDistribution.map(({ name, value, color }) => <div key={name} className="min-w-0 rounded-md border border-[#25252C] bg-[#101014]/80 px-3 py-3"><div className="mb-2 flex items-center gap-1.5"><span className="size-1.5 shrink-0 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 7px ${color}88` }} /><span className="truncate text-[9px] text-[#92929D]">{name}</span></div><p className="text-sm font-semibold tabular-nums text-[#F5F5F7]">{hasPaymentData ? value : "—"}</p></div>)}
							</div>
							<p className="mt-4 text-[10px] text-[#777783]">{hasPaymentData ? "Transaction success rate across recorded payments" : "No transaction data available to calculate payment performance."}</p>
						</div>
					</div>
				</section>

				<section aria-label="Payment monitoring details" className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
					<article className="group min-w-0 rounded-lg border border-[#25252C] bg-[#17171C]/95 p-5 shadow-[0_12px_30px_rgba(0,0,0,0.2)] transition duration-200 hover:-translate-y-0.5 hover:border-[#007BA7]/35 hover:shadow-[0_0_22px_rgba(0,123,167,0.08)] motion-reduce:transform-none motion-reduce:transition-none sm:p-5">
						<div className="mb-4 flex items-start justify-between gap-3 border-b border-[#25252C] pb-4"><div><h2 className="text-sm font-semibold text-[#F5F5F7]">Payment method breakdown</h2><p className="mt-1 text-[10px] text-[#92929D]">Transaction volume by payment rail</p></div><CreditCard aria-hidden="true" size={17} className="text-[#38BDF8]" /></div>
						<div className="space-y-4">
							{methodDistribution.map(({ method, count }) => {
								const MethodIcon = methodIcons[method];
								const width = payments.length > 0 ? `${(count / payments.length) * 100}%` : "0%";
								return <div key={method}><div className="mb-2 flex items-center justify-between gap-3"><span className="flex items-center gap-2 text-[11px] text-[#B5B5BE]"><MethodIcon aria-hidden="true" size={14} className="text-[#007BA7]" />{method}</span><span className="text-[10px] tabular-nums text-[#92929D]">{hasPaymentData ? count : "—"}</span></div><div className="h-1 overflow-hidden rounded-full bg-[#25252C]"><div className="h-full rounded-full bg-[#007BA7] shadow-[0_0_8px_rgba(0,123,167,0.7)] transition-all duration-700" style={{ width }} /></div></div>;
							})}
						</div>
						{!hasPaymentData && <p className="mt-4 border-t border-[#25252C] pt-3 text-[10px] text-[#777783]">No payment method data available.</p>}
					</article>

					<article className="min-w-0 rounded-lg border border-[#25252C] bg-[#17171C]/95 p-5 shadow-[0_12px_30px_rgba(0,0,0,0.2)] sm:p-5">
						<div className="mb-4 flex items-start justify-between gap-3 border-b border-[#25252C] pb-4"><div><h2 className="text-sm font-semibold text-[#F5F5F7]">Recent transaction activity</h2><p className="mt-1 text-[10px] text-[#92929D]">Latest payment events</p></div><Clock3 aria-hidden="true" size={17} className="text-[#38BDF8]" /></div>
						{payments.length > 0 ? <ol className="space-y-0 motion-safe:animate-[fadeIn_650ms_ease-out_both] motion-reduce:animate-none">{payments.slice(0, 4).map((payment, index) => { const Icon = paymentStatusStyles[payment.status].icon; const tone = paymentStatusStyles[payment.status].color; return <li key={payment.id} className="flex gap-3"><div className="flex w-8 shrink-0 flex-col items-center"><span className="z-10 flex size-7 items-center justify-center rounded-full border" style={{ color: tone, borderColor: `${tone}55`, backgroundColor: `${tone}12` }}><Icon aria-hidden="true" size={13} /></span>{index < Math.min(payments.length, 4) - 1 && <span className="my-1 min-h-5 w-px flex-1 bg-[#2D2D35]" />}</div><div className="min-w-0 flex-1 pb-3"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-[11px] font-medium text-[#E6E6EB]">{payment.status} payment <span className="font-mono text-[#69C9EB]">{payment.id}</span></p><span className="text-[9px] text-[#777783]">{payment.date}</span></div><p className="mt-1 text-[10px] text-[#92929D]">{payment.customer} · ₹{payment.amount.toLocaleString("en-IN")} · {payment.method}</p></div></li>; })}</ol> : <div className="flex min-h-[150px] items-center justify-center text-center text-[11px] text-[#92929D] motion-safe:animate-[fadeIn_650ms_ease-out_both] motion-reduce:animate-none"><div><div className="mx-auto mb-2 flex size-9 items-center justify-center rounded-md border border-[#007BA7]/20 bg-[#007BA7]/[0.06] text-[#38BDF8]"><Activity aria-hidden="true" size={16} /></div>No recent transactions available.</div></div>}
					</article>
				</section>

				<section aria-label="Transaction register" className="overflow-hidden rounded-lg border border-[#202027] bg-[#17171C]/95 shadow-[0_14px_38px_rgba(0,0,0,0.25),0_0_24px_rgba(0,123,167,0.045)]">
					<div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#25252C] px-4 py-4 sm:px-5">
						<div><h2 className="text-sm font-semibold text-[#F5F5F7]">Transaction register</h2><p className="mt-1 text-[11px] text-[#92929D]">Search and review payment records</p></div>
						<div className="flex w-full flex-col gap-2.5 sm:w-auto sm:flex-row sm:items-center">
							<label className="relative block w-full sm:w-[260px]"><Search aria-hidden="true" size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#92929D]" /><input type="search" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search transactions..." aria-label="Search payments" className="h-9 w-full rounded-md border border-[#2A2A32] bg-[#0F0F12] pl-9 pr-3 text-xs text-[#F5F5F7] outline-none placeholder:text-[#777783] transition focus:border-[#007BA7]/70 focus:shadow-[0_0_14px_rgba(0,123,167,0.12)]" /></label>
							<label className="relative block"><span className="sr-only">Filter by payment status</span><select value={activeFilter} onChange={(event) => setActiveFilter(event.target.value as StatusFilter)} className="h-9 w-full appearance-none rounded-md border border-[#2A2A32] bg-[#111115] py-0 pl-3 pr-9 text-xs text-[#D8D8DE] outline-none transition hover:border-[#007BA7]/40 focus:border-[#007BA7]/70 sm:w-[165px]">{statusFilters.map((filter) => <option key={filter} value={filter}>{filter}</option>)}</select><ChevronDown aria-hidden="true" size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#92929D]" /></label>
						</div>
					</div>
					<div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#25252C] px-4 py-3 sm:px-5"><div className="flex items-center gap-2 text-[11px] text-[#92929D]"><ArrowUpRight aria-hidden="true" size={14} className="text-[#38BDF8]" />Transaction ledger <span className="text-[#55555F]">/</span> {filteredPayments.length} records</div><button type="button" className="inline-flex items-center gap-1.5 text-[11px] text-[#92929D] transition hover:text-[#F5F5F7]"><ArrowDownUp aria-hidden="true" size={13} />Sort</button></div>
					<div className="overflow-x-auto">
						<table className="w-full min-w-[920px] border-collapse text-left">
							<thead className="bg-[#111115]/80"><tr className="border-b border-[#25252C] text-[10px] font-semibold uppercase tracking-[0.09em] text-[#777783]"><th scope="col" className="px-5 py-3.5">Payment ID</th><th scope="col" className="px-4 py-3.5">Customer</th><th scope="col" className="px-4 py-3.5">Invoice</th><th scope="col" className="px-4 py-3.5">Date</th><th scope="col" className="px-4 py-3.5 text-right">Amount</th><th scope="col" className="px-4 py-3.5">Payment Method</th><th scope="col" className="px-4 py-3.5">Status</th><th scope="col" aria-label="Actions" className="px-4 py-3.5" /></tr></thead>
							<tbody className="divide-y divide-[#24242B]">
								{filteredPayments.map((payment, index) => { const MethodIcon = methodIcons[payment.method]; return <tr key={payment.id} className={`group transition-colors duration-200 hover:bg-[#007BA7]/[0.055] ${payment.status === "Failed" ? "bg-[#FF2E93]/[0.025] hover:bg-[#FF2E93]/[0.07]" : ""}`}><td className="whitespace-nowrap px-5 py-3.5"><span className="inline-flex items-center gap-2 font-mono text-xs font-semibold text-[#69C9EB]"><span className="flex size-7 items-center justify-center rounded border border-[#007BA7]/20 bg-[#007BA7]/[0.06] text-[#38BDF8]"><CreditCard aria-hidden="true" size={13} /></span>{payment.id}</span></td><td className="whitespace-nowrap px-4 py-3.5"><div className="flex items-center gap-3"><div className={`flex size-9 shrink-0 items-center justify-center rounded-md text-[10px] font-semibold ${avatarStyles[index % avatarStyles.length]}`}>{payment.initials}</div><span className="text-[13px] font-medium text-[#F5F5F7]">{payment.customer}</span></div></td><td className="whitespace-nowrap px-4 py-3.5 font-mono text-xs text-[#92929D]">{payment.invoice}</td><td className="whitespace-nowrap px-4 py-3.5 text-xs text-[#92929D]">{payment.date}</td><td className="whitespace-nowrap px-4 py-3.5 text-right text-xs font-semibold tabular-nums text-[#F5F5F7]">₹{payment.amount.toLocaleString("en-IN")}</td><td className="whitespace-nowrap px-4 py-3.5"><div className="flex items-center gap-2 text-xs font-medium text-[#D8D8DE]"><MethodIcon aria-hidden="true" size={14} className="text-[#38BDF8]" />{payment.method}</div></td><td className="whitespace-nowrap px-4 py-3.5"><span className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 text-[10px] font-medium ${statusStyles[payment.status]}`}><span className={`size-1 rounded-full ${payment.status === "Successful" ? "bg-[#22C55E]" : payment.status === "Pending" ? "bg-[#F59E0B]" : "bg-[#FF2E93]"}`} />{payment.status}</span></td><td className="px-4 py-3.5 text-right"><button type="button" aria-label={`More actions for ${payment.id}`} className="inline-flex size-8 items-center justify-center rounded-md text-[#777783] transition hover:bg-[#25252C] hover:text-[#F5F5F7] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#007BA7]"><Ellipsis aria-hidden="true" size={17} /></button></td></tr>; })}
								{filteredPayments.length === 0 && <tr><td colSpan={8} className="px-5 py-14 text-center text-sm text-[#92929D]">{searchTerm || activeFilter !== "All payments" ? "No payments match your filters." : "No payment records available."}</td></tr>}
							</tbody>
						</table>
					</div>
					<div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#25252C] px-4 py-3.5 text-[11px] text-[#777783] sm:px-5"><span>Showing <span className="font-medium text-[#C4C4CC]">{filteredPayments.length}</span> of <span className="font-medium text-[#C4C4CC]">{payments.length}</span> transactions</span><span className="inline-flex items-center gap-2"><CreditCard aria-hidden="true" size={13} className="text-[#007BA7]" />Transaction ledger · INR</span></div>
				</section>
			</div>
		</MainLayout>
	);
}

export default Payments;
