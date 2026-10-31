import { useState } from "react";
import {
	ArrowDownUp,
	ChevronDown,
	Ellipsis,
	Filter,
	Plus,
	Search,
	UserRoundPlus,
} from "lucide-react";
import MainLayout from "../../../component/layout/MainLayout";

type CustomerStatus = "Active" | "Trial" | "At Risk";
type StatusFilter = "All customers" | CustomerStatus;

interface Customer {
	name: string;
	email: string;
	company: string;
	subscriptions: number;
	mrr: number;
	status: CustomerStatus;
	initials: string;
}

const customers: Customer[] = [];

const statusFilters: StatusFilter[] = ["All customers", "Active", "Trial", "At Risk"];

const statusStyles: Record<CustomerStatus, string> = {
	Active: "border-[#22C55E]/20 bg-[#22C55E]/[0.08] text-[#4ADE80]",
	Trial: "border-[#007BA7]/25 bg-[#007BA7]/[0.09] text-[#38BDF8]",
	"At Risk": "border-[#FF2E93]/25 bg-[#FF2E93]/[0.08] text-[#FF80BC]",
};

const avatarStyles = [
	"bg-[#007BA7]/15 text-[#38BDF8]",
	"bg-[#FF2E93]/10 text-[#FF80BC]",
	"bg-[#22C55E]/10 text-[#4ADE80]",
	"bg-[#F59E0B]/10 text-[#FBBF24]",
];

function Customers() {
	const [searchTerm, setSearchTerm] = useState("");
	const [activeFilter, setActiveFilter] = useState<StatusFilter>("All customers");

	const filteredCustomers = customers.filter((customer) => {
		const matchesStatus = activeFilter === "All customers" || customer.status === activeFilter;
		const query = searchTerm.trim().toLowerCase();
		const matchesSearch = !query || [customer.name, customer.email, customer.company].some((value) => value.toLowerCase().includes(query));
		return matchesStatus && matchesSearch;
	});

	return (
		<MainLayout>
			<div className="mx-auto min-h-screen w-full max-w-[1600px] px-5 py-7 text-[#F5F5F7] sm:px-8 sm:py-9 lg:px-11 lg:py-10">
				<header className="mb-7 flex flex-wrap items-end justify-between gap-5 border-b border-[#17171C] bg-[radial-gradient(ellipse_at_8%_30%,rgba(0,123,167,0.12),transparent_48%)] pb-6 sm:mb-8 sm:pb-7">
					<div>
						<div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#92929D]">
							<span className="h-px w-7 bg-[#007BA7] shadow-[0_0_10px_2px_rgba(0,123,167,0.6)]" />
							Relationship management
						</div>
						<h1 className="text-[32px] font-bold leading-tight text-[#F5F5F7] drop-shadow-[0_0_20px_rgba(0,123,167,0.18)] sm:text-[38px]">Customers</h1>
						<p className="mt-2 text-sm text-[#92929D]">Manage your customers and subscription relationships</p>
					</div>
					<button
						type="button"
						className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[#159DCA]/60 bg-[#007BA7] px-4 text-[13px] font-semibold text-white shadow-[0_0_20px_rgba(0,123,167,0.24),inset_0_1px_0_rgba(255,255,255,0.15)] transition hover:border-[#38BDF8] hover:bg-[#078AB8] hover:shadow-[0_0_26px_rgba(0,123,167,0.4)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#38BDF8] motion-reduce:transition-none"
					>
						<Plus aria-hidden="true" size={16} />
						Add Customer
					</button>
				</header>

				<section aria-label="Customer directory" className="overflow-hidden rounded-lg border border-[#202027] bg-[#17171C]/95 shadow-[0_14px_38px_rgba(0,0,0,0.25),0_0_24px_rgba(0,123,167,0.045)]">
					<div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#25252C] px-4 py-4 sm:px-5">
						<div>
							<h2 className="text-sm font-semibold text-[#F5F5F7]">Customer directory</h2>
							<p className="mt-1 text-[11px] text-[#92929D]">A clear view of your customer portfolio</p>
						</div>
						<div className="flex w-full flex-col gap-2.5 sm:w-auto sm:flex-row sm:items-center">
							<label className="relative block w-full sm:w-[250px]">
								<Search aria-hidden="true" size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#92929D]" />
								<input
									type="search"
									value={searchTerm}
									onChange={(event) => setSearchTerm(event.target.value)}
									placeholder="Search customers..."
									aria-label="Search customers"
									className="h-9 w-full rounded-md border border-[#2A2A32] bg-[#0F0F12] pl-9 pr-3 text-xs text-[#F5F5F7] outline-none placeholder:text-[#777783] transition focus:border-[#007BA7]/70 focus:shadow-[0_0_14px_rgba(0,123,167,0.12)]"
								/>
							</label>
							<button type="button" className="inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-md border border-[#2A2A32] bg-[#111115] px-3 text-xs font-medium text-[#B5B5BE] transition hover:border-[#007BA7]/40 hover:text-[#F5F5F7]">
								<Filter aria-hidden="true" size={14} />
								Filters
								<ChevronDown aria-hidden="true" size={13} className="text-[#92929D]" />
							</button>
						</div>
					</div>

					<div className="flex gap-1 overflow-x-auto border-b border-[#25252C] px-4 pt-2 sm:px-5">
						{statusFilters.map((filter) => {
							const count = filter === "All customers" ? customers.length : customers.filter((customer) => customer.status === filter).length;
							const isActive = activeFilter === filter;
							return (
								<button
									key={filter}
									type="button"
									onClick={() => setActiveFilter(filter)}
									aria-pressed={isActive}
									className={`relative inline-flex shrink-0 items-center gap-2 px-3 py-2.5 text-xs font-medium transition-colors ${isActive ? "text-[#F5F5F7] after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:bg-[#007BA7] after:shadow-[0_0_8px_rgba(0,123,167,0.8)]" : "text-[#92929D] hover:text-[#D8D8DE]"}`}
								>
									{filter}<span className={`text-[10px] tabular-nums ${isActive ? "text-[#38BDF8]" : "text-[#777783]"}`}>{count}</span>
								</button>
							);
						})}
						<button type="button" className="ml-auto hidden shrink-0 items-center gap-1.5 px-2 py-2.5 text-[11px] text-[#92929D] transition hover:text-[#F5F5F7] sm:inline-flex">
							<ArrowDownUp aria-hidden="true" size={13} /> Sort
						</button>
					</div>

					<div className="overflow-x-auto">
						<table className="w-full min-w-[900px] border-collapse text-left">
							<thead className="bg-[#111115]/80">
								<tr className="border-b border-[#25252C] text-[10px] font-semibold uppercase tracking-[0.09em] text-[#777783]">
									<th scope="col" className="px-5 py-3.5">Customer</th>
									<th scope="col" className="px-4 py-3.5">Email</th>
									<th scope="col" className="px-4 py-3.5">Company</th>
									<th scope="col" className="px-4 py-3.5 text-center">Active Subscriptions</th>
									<th scope="col" className="px-4 py-3.5 text-right">MRR</th>
									<th scope="col" className="px-4 py-3.5">Status</th>
									<th scope="col" className="px-4 py-3.5"><span className="sr-only">Actions</span></th>
								</tr>
							</thead>
							<tbody className="divide-y divide-[#24242B]">
								{filteredCustomers.map((customer, index) => (
									<tr key={customer.email} className="group transition-colors hover:bg-[#007BA7]/[0.055]">
										<td className="whitespace-nowrap px-5 py-3.5">
											<div className="flex items-center gap-3">
												<div className={`flex size-9 shrink-0 items-center justify-center rounded-md text-[10px] font-semibold ${avatarStyles[index % avatarStyles.length]}`}>{customer.initials}</div>
												<span className="text-[13px] font-medium text-[#F5F5F7]">{customer.name}</span>
											</div>
										</td>
										<td className="whitespace-nowrap px-4 py-3.5 text-xs text-[#92929D]">{customer.email}</td>
										<td className="whitespace-nowrap px-4 py-3.5 text-xs text-[#C4C4CC]">{customer.company}</td>
										<td className="px-4 py-3.5 text-center text-xs tabular-nums text-[#D8D8DE]">{customer.subscriptions}</td>
										<td className="whitespace-nowrap px-4 py-3.5 text-right text-xs font-medium tabular-nums text-[#F5F5F7]">₹{customer.mrr.toLocaleString("en-IN")}</td>
										<td className="whitespace-nowrap px-4 py-3.5">
											<span className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 text-[10px] font-medium ${statusStyles[customer.status]}`}>
												<span className={`size-1 rounded-full ${customer.status === "Active" ? "bg-[#22C55E]" : customer.status === "Trial" ? "bg-[#38BDF8]" : "bg-[#FF2E93]"}`} />
												{customer.status}
											</span>
										</td>
										<td className="px-4 py-3.5 text-right">
											<button type="button" aria-label={`Actions for ${customer.name}`} className="inline-flex size-8 items-center justify-center rounded-md text-[#777783] transition hover:bg-[#25252C] hover:text-[#F5F5F7] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#007BA7]">
												<Ellipsis aria-hidden="true" size={17} />
											</button>
										</td>
									</tr>
								))}
								{filteredCustomers.length === 0 && (
									<tr><td colSpan={7} className="px-5 py-14 text-center text-sm text-[#92929D]">{searchTerm || activeFilter !== "All customers" ? "No customers match your filters." : "No customers found. No data available."}</td></tr>
								)}
							</tbody>
						</table>
					</div>

					<div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#25252C] px-4 py-3.5 text-[11px] text-[#777783] sm:px-5">
						<span>Showing <span className="font-medium text-[#C4C4CC]">{filteredCustomers.length}</span> of <span className="font-medium text-[#C4C4CC]">{customers.length}</span> customers</span>
						<span className="inline-flex items-center gap-2"><UserRoundPlus aria-hidden="true" size={13} className="text-[#007BA7]" />Customer records</span>
					</div>
				</section>
			</div>
		</MainLayout>
	);
}

export default Customers;
