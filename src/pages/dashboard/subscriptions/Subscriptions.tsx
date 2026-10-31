import { useState } from "react";
import {
	ArrowDownUp,
	ArrowUpRight,
	CalendarClock,
	ChevronDown,
	CircleAlert,
	CreditCard,
	Ellipsis,
	Plus,
	Search,
	Users,
} from "lucide-react";
import MainLayout from "../../../component/layout/MainLayout";

type SubscriptionStatus = "Active" | "Trial" | "Past Due" | "Cancelled";
type StatusFilter = "All subscriptions" | SubscriptionStatus;

interface Subscription {
	customer: string;
	email: string;
	plan: string;
	startDate: string;
	nextBilling: string;
	mrr: number;
	status: SubscriptionStatus;
	initials: string;
}

const subscriptions: Subscription[] = [];

const statusFilters: StatusFilter[] = ["All subscriptions", "Active", "Trial", "Past Due", "Cancelled"];

const statusStyles: Record<SubscriptionStatus, string> = {
	Active: "border-[#22C55E]/20 bg-[#22C55E]/[0.08] text-[#4ADE80]",
	Trial: "border-[#007BA7]/25 bg-[#007BA7]/[0.09] text-[#38BDF8]",
	"Past Due": "border-[#F59E0B]/25 bg-[#F59E0B]/[0.08] text-[#FBBF24]",
	Cancelled: "border-[#92929D]/20 bg-[#92929D]/[0.07] text-[#B5B5BE]",
};

const avatarStyles = [
	"bg-[#007BA7]/15 text-[#38BDF8]",
	"bg-[#FF2E93]/10 text-[#FF80BC]",
	"bg-[#22C55E]/10 text-[#4ADE80]",
	"bg-[#F59E0B]/10 text-[#FBBF24]",
];

const summaries = [
	{ label: "Active Subscriptions", value: "—", icon: Users, tone: "blue" },
	{ label: "Monthly Recurring Revenue", value: "—", icon: CreditCard, tone: "pink" },
	{ label: "Past Due", value: "—", icon: CircleAlert, tone: "amber" },
] as const;

function Subscriptions() {
	const [searchTerm, setSearchTerm] = useState("");
	const [activeFilter, setActiveFilter] = useState<StatusFilter>("All subscriptions");

	const filteredSubscriptions = subscriptions.filter((subscription) => {
		const matchesStatus = activeFilter === "All subscriptions" || subscription.status === activeFilter;
		const query = searchTerm.trim().toLowerCase();
		const matchesSearch = !query || [subscription.customer, subscription.email, subscription.plan].some((value) => value.toLowerCase().includes(query));
		return matchesStatus && matchesSearch;
	});

	return (
		<MainLayout>
			<div className="mx-auto min-h-screen w-full max-w-[1600px] px-5 py-7 text-[#F5F5F7] sm:px-8 sm:py-9 lg:px-11 lg:py-10">
				<header className="mb-7 flex flex-wrap items-end justify-between gap-5 border-b border-[#17171C] bg-[radial-gradient(ellipse_at_8%_30%,rgba(0,123,167,0.12),transparent_48%)] pb-6 sm:mb-8 sm:pb-7">
					<div>
						<div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#92929D]">
							<span className="h-px w-7 bg-[#007BA7] shadow-[0_0_10px_2px_rgba(0,123,167,0.6)]" />
							Recurring revenue
						</div>
						<h1 className="text-[32px] font-bold leading-tight text-[#F5F5F7] drop-shadow-[0_0_20px_rgba(0,123,167,0.18)] sm:text-[38px]">Subscriptions</h1>
						<p className="mt-2 text-sm text-[#92929D]">Track recurring subscriptions and revenue</p>
					</div>
					<button
						type="button"
						className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[#159DCA]/60 bg-[#007BA7] px-4 text-[13px] font-semibold text-white shadow-[0_0_20px_rgba(0,123,167,0.24),inset_0_1px_0_rgba(255,255,255,0.15)] transition hover:border-[#38BDF8] hover:bg-[#078AB8] hover:shadow-[0_0_26px_rgba(0,123,167,0.4)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#38BDF8] motion-reduce:transition-none"
					>
						<Plus aria-hidden="true" size={16} />
						Create Subscription
					</button>
				</header>

				<section aria-label="Subscription summary" className="mb-6 grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-3">
					{summaries.map(({ label, value, icon: Icon, tone }) => {
						const styles = {
							blue: "border-[#007BA7]/25 hover:border-[#007BA7]/50 text-[#38BDF8] shadow-[0_0_20px_rgba(0,123,167,0.08)]",
							pink: "border-[#FF2E93]/22 hover:border-[#FF2E93]/45 text-[#FF80BC] shadow-[0_0_20px_rgba(255,46,147,0.06)]",
							amber: "border-[#F59E0B]/20 hover:border-[#F59E0B]/40 text-[#FBBF24] shadow-[0_0_18px_rgba(245,158,11,0.05)]",
						}[tone];
						return (
							<article key={label} className={`group flex min-w-0 items-center justify-between gap-4 rounded-lg border bg-[#17171C]/95 px-5 py-4 transition duration-200 hover:-translate-y-0.5 ${styles}`}>
								<div className="min-w-0">
									<p className="text-[11px] font-medium text-[#92929D]">{label}</p>
									<p className="mt-2 text-[25px] font-semibold leading-none text-[#F5F5F7]">{value}</p>
								</div>
								<div className={`flex size-10 shrink-0 items-center justify-center rounded-md border border-current/20 bg-current/[0.08] transition group-hover:shadow-[0_0_16px_currentColor]`}>
									<Icon aria-hidden="true" size={18} strokeWidth={1.8} />
								</div>
							</article>
						);
					})}
				</section>

				<section aria-label="Subscription directory" className="overflow-hidden rounded-lg border border-[#202027] bg-[#17171C]/95 shadow-[0_14px_38px_rgba(0,0,0,0.25),0_0_24px_rgba(0,123,167,0.045)]">
					<div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#25252C] px-4 py-4 sm:px-5">
						<div>
							<h2 className="text-sm font-semibold text-[#F5F5F7]">Subscription directory</h2>
							<p className="mt-1 text-[11px] text-[#92929D]">Review plans, billing dates, and account status</p>
						</div>
						<div className="flex w-full flex-col gap-2.5 sm:w-auto sm:flex-row sm:items-center">
							<label className="relative block w-full sm:w-[250px]">
								<Search aria-hidden="true" size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#92929D]" />
								<input
									type="search"
									value={searchTerm}
									onChange={(event) => setSearchTerm(event.target.value)}
									placeholder="Search subscriptions..."
									aria-label="Search subscriptions"
									className="h-9 w-full rounded-md border border-[#2A2A32] bg-[#0F0F12] pl-9 pr-3 text-xs text-[#F5F5F7] outline-none placeholder:text-[#777783] transition focus:border-[#007BA7]/70 focus:shadow-[0_0_14px_rgba(0,123,167,0.12)]"
								/>
							</label>
							<label className="relative block">
								<span className="sr-only">Filter by subscription status</span>
								<select
									value={activeFilter}
									onChange={(event) => setActiveFilter(event.target.value as StatusFilter)}
									className="h-9 w-full appearance-none rounded-md border border-[#2A2A32] bg-[#111115] py-0 pl-3 pr-9 text-xs text-[#D8D8DE] outline-none transition hover:border-[#007BA7]/40 focus:border-[#007BA7]/70 sm:w-[170px]"
								>
									{statusFilters.map((filter) => <option key={filter} value={filter}>{filter}</option>)}
								</select>
								<ChevronDown aria-hidden="true" size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#92929D]" />
							</label>
						</div>
					</div>

					<div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#25252C] px-4 py-3 sm:px-5">
						<div className="flex items-center gap-2 text-[11px] text-[#92929D]"><CalendarClock aria-hidden="true" size={14} className="text-[#38BDF8]" /> Billing schedule</div>
						<button type="button" className="inline-flex items-center gap-1.5 text-[11px] text-[#92929D] transition hover:text-[#F5F5F7]"><ArrowDownUp aria-hidden="true" size={13} /> Sort</button>
					</div>

					<div className="overflow-x-auto">
						<table className="w-full min-w-[880px] border-collapse text-left">
							<thead className="bg-[#111115]/80">
								<tr className="border-b border-[#25252C] text-[10px] font-semibold uppercase tracking-[0.09em] text-[#777783]">
									<th scope="col" className="px-5 py-3.5">Customer</th>
									<th scope="col" className="px-4 py-3.5">Plan</th>
									<th scope="col" className="px-4 py-3.5">Start Date</th>
									<th scope="col" className="px-4 py-3.5">Next Billing</th>
									<th scope="col" className="px-4 py-3.5 text-right">MRR</th>
									<th scope="col" className="px-4 py-3.5">Status</th>
									<th scope="col" className="px-4 py-3.5"><span className="sr-only">Actions</span></th>
								</tr>
							</thead>
							<tbody className="divide-y divide-[#24242B]">
								{filteredSubscriptions.map((subscription, index) => (
									<tr key={`${subscription.email}-${subscription.plan}`} className="group transition-colors hover:bg-[#007BA7]/[0.055]">
										<td className="whitespace-nowrap px-5 py-3.5">
											<div className="flex items-center gap-3">
												<div className={`flex size-9 shrink-0 items-center justify-center rounded-md text-[10px] font-semibold ${avatarStyles[index % avatarStyles.length]}`}>{subscription.initials}</div>
												<div><p className="text-[13px] font-medium text-[#F5F5F7]">{subscription.customer}</p><p className="mt-0.5 text-[10px] text-[#777783]">{subscription.email}</p></div>
											</div>
										</td>
										<td className="whitespace-nowrap px-4 py-3.5"><span className="text-xs font-medium text-[#D8D8DE]">{subscription.plan}</span></td>
										<td className="whitespace-nowrap px-4 py-3.5 text-xs text-[#92929D]">{subscription.startDate}</td>
										<td className="whitespace-nowrap px-4 py-3.5 text-xs text-[#92929D]">{subscription.nextBilling}</td>
										<td className="whitespace-nowrap px-4 py-3.5 text-right text-xs font-medium tabular-nums text-[#F5F5F7]">₹{subscription.mrr.toLocaleString("en-IN")}</td>
										<td className="whitespace-nowrap px-4 py-3.5">
											<span className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 text-[10px] font-medium ${statusStyles[subscription.status]}`}>
												<span className={`size-1 rounded-full ${subscription.status === "Active" ? "bg-[#22C55E]" : subscription.status === "Trial" ? "bg-[#38BDF8]" : subscription.status === "Past Due" ? "bg-[#F59E0B]" : "bg-[#92929D]"}`} />
												{subscription.status}
											</span>
										</td>
										<td className="px-4 py-3.5 text-right">
											<button type="button" aria-label={`Actions for ${subscription.customer}`} className="inline-flex size-8 items-center justify-center rounded-md text-[#777783] transition hover:bg-[#25252C] hover:text-[#F5F5F7] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#007BA7]"><Ellipsis aria-hidden="true" size={17} /></button>
										</td>
									</tr>
								))}
								{filteredSubscriptions.length === 0 && <tr><td colSpan={7} className="px-5 py-14 text-center text-sm text-[#92929D]">{searchTerm || activeFilter !== "All subscriptions" ? "No subscriptions match your filters." : "No subscriptions found. No data available."}</td></tr>}
							</tbody>
						</table>
					</div>

					<div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#25252C] px-4 py-3.5 text-[11px] text-[#777783] sm:px-5">
						<span>Showing <span className="font-medium text-[#C4C4CC]">{filteredSubscriptions.length}</span> of <span className="font-medium text-[#C4C4CC]">{subscriptions.length}</span> subscriptions</span>
						<span className="inline-flex items-center gap-2"><ArrowUpRight aria-hidden="true" size={13} className="text-[#22C55E]" />Subscription records</span>
					</div>
				</section>
			</div>
		</MainLayout>
	);
}

export default Subscriptions;
