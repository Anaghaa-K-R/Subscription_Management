import { useState } from "react";
import {
	CalendarDays,
	ChevronDown,
	Clock3,
	Download,
	Ellipsis,
	FileText,
	Plus,
	Search,
	FileCheck2,
	ReceiptText,
} from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import MainLayout from "../../../component/layout/MainLayout";

type InvoiceStatus = "Paid" | "Pending" | "Overdue" | "Draft";
type StatusFilter = "All invoices" | InvoiceStatus;

interface Invoice {
	id: string;
	customer: string;
	company: string;
	issueDate: string;
	dueDate: string;
	amount: number;
	status: InvoiceStatus;
	initials: string;
}

const invoices: Invoice[] = [];

const statusFilters: StatusFilter[] = ["All invoices", "Paid", "Pending", "Overdue", "Draft"];

const statusStyles: Record<InvoiceStatus, string> = {
	Paid: "border-[#22C55E]/20 bg-[#22C55E]/[0.08] text-[#4ADE80]",
	Pending: "border-[#F59E0B]/25 bg-[#F59E0B]/[0.08] text-[#FBBF24]",
	Overdue: "border-[#FF2E93]/25 bg-[#FF2E93]/[0.08] text-[#FF80BC]",
	Draft: "border-[#92929D]/20 bg-[#92929D]/[0.07] text-[#B5B5BE]",
};

const avatarStyles = [
	"bg-[#007BA7]/15 text-[#38BDF8]",
	"bg-[#FF2E93]/10 text-[#FF80BC]",
	"bg-[#22C55E]/10 text-[#4ADE80]",
	"bg-[#F59E0B]/10 text-[#FBBF24]",
];

const distributionColors: Record<InvoiceStatus, string> = {
	Paid: "#22C55E",
	Pending: "#007BA7",
	Overdue: "#FF2E93",
	Draft: "#55555F",
};

function Invoices() {
	const [searchTerm, setSearchTerm] = useState("");
	const [activeFilter, setActiveFilter] = useState<StatusFilter>("All invoices");

	const filteredInvoices = invoices.filter((invoice) => {
		const matchesStatus = activeFilter === "All invoices" || invoice.status === activeFilter;
		const query = searchTerm.trim().toLowerCase();
		const matchesSearch = !query || [invoice.id, invoice.customer, invoice.company].some((value) => value.toLowerCase().includes(query));
		return matchesStatus && matchesSearch;
	});
	const statusDistribution = statusFilters.slice(1).map((status) => ({
  name: status,
  value: invoices.filter((invoice) => invoice.status === status).length,
  color: distributionColors[status as InvoiceStatus],
}));
	const hasInvoiceData = invoices.length > 0;
	const outstandingBalance = invoices
		.filter((invoice) => invoice.status === "Pending" || invoice.status === "Overdue")
		.reduce((total, invoice) => total + invoice.amount, 0);
	const overdueCount = invoices.filter((invoice) => invoice.status === "Overdue").length;

	return (
		<MainLayout>
			<div className="mx-auto min-h-screen w-full max-w-[1600px] px-5 py-7 text-[#F5F5F7] sm:px-8 sm:py-9 lg:px-11 lg:py-10">
				<header className="mb-7 flex flex-wrap items-end justify-between gap-5 border-b border-[#17171C] bg-[radial-gradient(ellipse_at_8%_30%,rgba(0,123,167,0.15),transparent_48%)] pb-6 sm:mb-8 sm:pb-7">
					<div>
						<div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#92929D]">
							<span className="h-px w-7 bg-[#007BA7] shadow-[0_0_10px_2px_rgba(0,123,167,0.6)]" />
							Billing documents
						</div>
						<h1 className="text-[32px] font-bold leading-tight text-[#F5F5F7] drop-shadow-[0_0_20px_rgba(0,123,167,0.18)] sm:text-[38px]">Invoices</h1>
						<p className="mt-2 text-sm text-[#92929D]">Manage invoices, payments and outstanding balances</p>
					</div>
					<button
						type="button"
						className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[#159DCA]/60 bg-[#007BA7] px-4 text-[13px] font-semibold text-white shadow-[0_0_20px_rgba(0,123,167,0.24),inset_0_1px_0_rgba(255,255,255,0.15)] transition hover:border-[#38BDF8] hover:bg-[#078AB8] hover:shadow-[0_0_26px_rgba(0,123,167,0.4)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#38BDF8] motion-reduce:transition-none"
					>
						<Plus aria-hidden="true" size={16} />
						Create Invoice
					</button>
				</header>

				<section aria-label="Invoice overview" className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.8fr)]">
					<article className="group relative isolate flex min-h-[220px] flex-col justify-between overflow-hidden rounded-lg border border-[#007BA7]/35 bg-[#17171C] p-5 shadow-[0_16px_40px_rgba(0,0,0,0.28),0_0_28px_rgba(0,123,167,0.11)] transition duration-300 hover:-translate-y-0.5 hover:border-[#007BA7]/55 hover:shadow-[0_18px_44px_rgba(0,0,0,0.3),0_0_34px_rgba(0,123,167,0.17)] motion-reduce:transform-none motion-reduce:transition-none sm:p-6">
						<div className="pointer-events-none absolute -right-10 -top-20 -z-10 size-64 rounded-full bg-[#007BA7]/[0.10] blur-3xl" />
						<div className="flex items-start justify-between gap-4">
							<div>
								<div className="mb-3 inline-flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#69C9EB]"><span className="h-px w-5 bg-[#007BA7] shadow-[0_0_8px_rgba(0,123,167,0.8)]" />Accounts receivable</div>
								<h2 className="text-sm font-medium text-[#B5B5BE]">Outstanding balance</h2>
								<p className="mt-3 text-[38px] font-semibold leading-none tracking-tight text-[#F5F5F7] drop-shadow-[0_0_18px_rgba(0,123,167,0.22)] sm:text-[44px]">{hasInvoiceData ? `₹${outstandingBalance.toLocaleString("en-IN")}` : "—"}</p>
								<p className="mt-3 text-xs text-[#92929D]">{hasInvoiceData ? "Pending and overdue invoice value" : "No data available for outstanding invoices"}</p>
							</div>
							<div className="flex size-11 shrink-0 items-center justify-center rounded-md border border-[#007BA7]/35 bg-[#007BA7]/[0.10] text-[#38BDF8] shadow-[0_0_20px_rgba(0,123,167,0.16)]"><ReceiptText aria-hidden="true" size={20} /></div>
						</div>
						<div className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-[#292930] pt-4">
							<div className="flex items-center gap-2 text-[11px] text-[#92929D]"><span className="size-1.5 rounded-full bg-[#007BA7] shadow-[0_0_7px_rgba(0,123,167,0.8)]" />Open invoices <span className="font-semibold tabular-nums text-[#F5F5F7]">{hasInvoiceData ? invoices.filter((invoice) => invoice.status === "Pending").length : "—"}</span></div>
							<div className="flex items-center gap-2 text-[11px] text-[#92929D]"><span className="size-1.5 rounded-full bg-[#FF2E93] shadow-[0_0_7px_rgba(255,46,147,0.65)]" />Overdue <span className="font-semibold tabular-nums text-[#FF80BC]">{hasInvoiceData ? overdueCount : "—"}</span></div>
						</div>
					</article>

					<article className="group relative overflow-hidden rounded-lg border border-[#25252C] bg-[#17171C]/95 p-5 shadow-[0_12px_34px_rgba(0,0,0,0.22)] transition duration-300 hover:-translate-y-0.5 hover:border-[#007BA7]/35 hover:shadow-[0_0_24px_rgba(0,123,167,0.09)] motion-reduce:transform-none motion-reduce:transition-none sm:p-5">
						<div className="mb-1 flex items-start justify-between gap-3">
							<div><h2 className="text-sm font-semibold text-[#F5F5F7]">Invoice status</h2><p className="mt-1 text-[11px] text-[#92929D]">Distribution by document state</p></div>
							<FileCheck2 aria-hidden="true" size={17} className="text-[#38BDF8]" />
						</div>
						<div className="relative mx-auto h-[142px] w-full max-w-[330px]">
							<ResponsiveContainer width="100%" height="100%">
								<PieChart>
									<Pie data={statusDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={43} outerRadius={59} paddingAngle={3} stroke="none" isAnimationActive animationDuration={850}>
										{statusDistribution.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
									</Pie>
									<Tooltip contentStyle={{ background: "#111115", border: "1px solid rgba(0,123,167,0.35)", borderRadius: 6, color: "#F5F5F7" }} />
								</PieChart>
							</ResponsiveContainer>
							<div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
								<span className="text-lg font-semibold text-[#F5F5F7]">{hasInvoiceData ? invoices.length : "—"}</span>
								<span className="text-[9px] uppercase tracking-[0.1em] text-[#777783]">invoices</span>
							</div>
							{!hasInvoiceData && <span className="absolute inset-x-0 bottom-0 text-center text-[10px] text-[#92929D]">No status data available</span>}
						</div>
						<div className="flex flex-wrap justify-center gap-x-4 gap-y-2 border-t border-[#25252C] pt-3">
							{statusDistribution.map(({ name, color, value }) => <span key={name} className="inline-flex items-center gap-1.5 text-[9px] text-[#92929D]"><span className="size-1.5 rounded-full" style={{ backgroundColor: color }} />{name}<span className="tabular-nums text-[#B5B5BE]">{hasInvoiceData ? value : "—"}</span></span>)}
						</div>
					</article>
				</section>

				<section aria-label="Invoice directory" className="overflow-hidden rounded-lg border border-[#202027] bg-[#17171C]/95 shadow-[0_14px_38px_rgba(0,0,0,0.25),0_0_24px_rgba(0,123,167,0.045)]">
					<div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#25252C] px-4 py-4 sm:px-5">
						<div>
							<h2 className="text-sm font-semibold text-[#F5F5F7]">Invoice register</h2>
							<p className="mt-1 text-[11px] text-[#92929D]">Monitor billing activity and payment status</p>
						</div>
						<div className="flex w-full flex-col gap-2.5 sm:w-auto sm:flex-row sm:items-center">
							<label className="relative block w-full sm:w-[250px]">
								<Search aria-hidden="true" size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#92929D]" />
								<input
									type="search"
									value={searchTerm}
									onChange={(event) => setSearchTerm(event.target.value)}
									placeholder="Search invoices..."
									aria-label="Search invoices"
									className="h-9 w-full rounded-md border border-[#2A2A32] bg-[#0F0F12] pl-9 pr-3 text-xs text-[#F5F5F7] outline-none placeholder:text-[#777783] transition focus:border-[#007BA7]/70 focus:shadow-[0_0_14px_rgba(0,123,167,0.12)]"
								/>
							</label>
							<label className="relative block">
								<span className="sr-only">Filter by invoice status</span>
								<select
									value={activeFilter}
									onChange={(event) => setActiveFilter(event.target.value as StatusFilter)}
									className="h-9 w-full appearance-none rounded-md border border-[#2A2A32] bg-[#111115] py-0 pl-3 pr-9 text-xs text-[#D8D8DE] outline-none transition hover:border-[#007BA7]/40 focus:border-[#007BA7]/70 sm:w-[155px]"
								>
									{statusFilters.map((filter) => <option key={filter} value={filter}>{filter}</option>)}
								</select>
								<ChevronDown aria-hidden="true" size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#92929D]" />
							</label>
						</div>
					</div>

					<div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#25252C] px-4 py-3 sm:px-5">
						<div className="flex items-center gap-2 text-[11px] text-[#92929D]"><CalendarDays aria-hidden="true" size={14} className="text-[#38BDF8]" /> Document register <span className="text-[#55555F]">/</span> {filteredInvoices.length} records</div>
						<span className="inline-flex items-center gap-1.5 text-[10px] text-[#777783]"><FileText aria-hidden="true" size={13} className="text-[#007BA7]" /> Invoice documents</span>
					</div>

					<div className="overflow-x-auto">
						<table className="w-full min-w-[850px] border-collapse text-left">
							<thead className="bg-[#111115]/80">
								<tr className="border-b border-[#25252C] text-[10px] font-semibold uppercase tracking-[0.09em] text-[#777783]">
									<th scope="col" className="px-5 py-3.5">Invoice ID</th>
									<th scope="col" className="px-4 py-3.5">Customer</th>
									<th scope="col" className="px-4 py-3.5">Issue Date</th>
									<th scope="col" className="px-4 py-3.5">Due Date</th>
									<th scope="col" className="px-4 py-3.5 text-right">Amount</th>
									<th scope="col" className="px-4 py-3.5">Status</th>
									<th scope="col" className="px-4 py-3.5"><span className="sr-only">Actions</span></th>
								</tr>
							</thead>
							<tbody className="divide-y divide-[#24242B]">
								{filteredInvoices.map((invoice, index) => (
									<tr key={invoice.id} className={`group transition-colors duration-200 hover:bg-[#007BA7]/[0.055] ${invoice.status === "Overdue" ? "bg-[#FF2E93]/[0.025] hover:bg-[#FF2E93]/[0.07]" : ""}`}>
										<td className="whitespace-nowrap px-5 py-3.5">
											<span className="inline-flex items-center gap-2 font-mono text-xs font-semibold text-[#69C9EB]"><span className="flex size-7 items-center justify-center rounded border border-[#007BA7]/20 bg-[#007BA7]/[0.06] text-[#38BDF8]"><FileText aria-hidden="true" size={13} /></span>{invoice.id}</span>
										</td>
										<td className="whitespace-nowrap px-4 py-3.5">
											<div className="flex items-center gap-3">
												<div className={`flex size-9 shrink-0 items-center justify-center rounded-md text-[10px] font-semibold ${avatarStyles[index % avatarStyles.length]}`}>{invoice.initials}</div>
												<div><p className="text-[13px] font-medium text-[#F5F5F7]">{invoice.customer}</p><p className="mt-0.5 text-[10px] text-[#777783]">{invoice.company}</p></div>
											</div>
										</td>
										<td className="whitespace-nowrap px-4 py-3.5 text-xs text-[#92929D]">{invoice.issueDate}</td>
										<td className="whitespace-nowrap px-4 py-3.5"><span className={`inline-flex items-center gap-1.5 text-xs ${invoice.status === "Overdue" ? "font-medium text-[#FF80BC]" : "text-[#B5B5BE]"}`}><Clock3 aria-hidden="true" size={12} className={invoice.status === "Overdue" ? "text-[#FF2E93]" : "text-[#007BA7]"} />{invoice.dueDate}</span></td>
										<td className="whitespace-nowrap px-4 py-3.5 text-right text-xs font-semibold tabular-nums text-[#F5F5F7]">₹{invoice.amount.toLocaleString("en-IN")}</td>
										<td className="whitespace-nowrap px-4 py-3.5">
											<span className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 text-[10px] font-medium ${statusStyles[invoice.status]}`}>
												<span className={`size-1 rounded-full ${invoice.status === "Paid" ? "bg-[#22C55E]" : invoice.status === "Pending" ? "bg-[#F59E0B]" : invoice.status === "Overdue" ? "bg-[#FF2E93]" : "bg-[#92929D]"}`} />
												{invoice.status}
											</span>
										</td>
										<td className="px-4 py-3.5 text-right">
											<button type="button" aria-label={`Download ${invoice.id}`} className="mr-1 inline-flex size-8 items-center justify-center rounded-md text-[#777783] transition hover:bg-[#25252C] hover:text-[#38BDF8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#007BA7]"><Download aria-hidden="true" size={15} /></button>
											<button type="button" aria-label={`More actions for ${invoice.id}`} className="inline-flex size-8 items-center justify-center rounded-md text-[#777783] transition hover:bg-[#25252C] hover:text-[#F5F5F7] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#007BA7]"><Ellipsis aria-hidden="true" size={17} /></button>
										</td>
									</tr>
								))}
								{filteredInvoices.length === 0 && <tr><td colSpan={7} className="px-5 py-14 text-center text-sm text-[#92929D]">{searchTerm || activeFilter !== "All invoices" ? "No invoices match your filters." : "No invoices found. No data available."}</td></tr>}
							</tbody>
						</table>
					</div>

					<div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#25252C] px-4 py-3.5 text-[11px] text-[#777783] sm:px-5">
						<span>Showing <span className="font-medium text-[#C4C4CC]">{filteredInvoices.length}</span> of <span className="font-medium text-[#C4C4CC]">{invoices.length}</span> invoices</span>
						<span className="inline-flex items-center gap-2"><FileText aria-hidden="true" size={13} className="text-[#007BA7]" />Invoice records · INR</span>
					</div>
				</section>
			</div>
		</MainLayout>
	);
}

export default Invoices;
