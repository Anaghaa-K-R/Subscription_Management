import {
	Activity,
	AlertTriangle,
	ArrowRight,
	BrainCircuit,
	CheckCircle2,
	CircleDollarSign,
	CreditCard,
	Gauge,
	Sparkles,
	TrendingUp,
	UsersRound,
} from "lucide-react";
import {
	Area,
	AreaChart,
	CartesianGrid,
	ReferenceLine,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import MainLayout from "../../component/layout/MainLayout";

interface ForecastPoint {
	month: string;
	actual?: number | null;
	forecast?: number | null;
}

const forecastData: ForecastPoint[] = [];

const keyMetrics = [
	{ label: "Revenue Growth", value: "—", note: "No data available", icon: TrendingUp, accent: "blue" },
	{ label: "Forecast Confidence", value: "—", note: "No data available", icon: Gauge, accent: "pink" },
	{ label: "At-Risk Revenue", value: "—", note: "No data available", icon: AlertTriangle, accent: "amber" },
	{ label: "Expansion Opportunity", value: "—", note: "No data available", icon: CircleDollarSign, accent: "green" },
] as const;

const insights = [
	{
		title: "Growth Opportunity",
		text: "No data available to identify customer retention patterns or growth opportunities.",
		icon: TrendingUp,
		accent: "blue",
		label: "Retention signal",
	},
	{
		title: "Revenue Risk",
		text: "No data available to assess failed payments or potential revenue leakage.",
		icon: AlertTriangle,
		accent: "pink",
		label: "Payment behavior",
	},
	{
		title: "Expansion Opportunity",
		text: "No data available to identify customer usage patterns or expansion opportunities.",
		icon: UsersRound,
		accent: "blue",
		label: "Usage signal",
	},
] as const;

const recommendations: {
	title: string;
	detail: string;
	priority: string;
	icon: typeof CreditCard;
	accent: "pink" | "blue" | "amber";
}[] = [];

function RevenueInsights() {
	return (
		<MainLayout>
			<div className="mx-auto min-h-screen w-full max-w-[1600px] px-5 py-7 text-[#F5F5F7] sm:px-8 sm:py-9 lg:px-11 lg:py-10">
				<header className="relative isolate mb-6 overflow-hidden border-b border-[#17171C] bg-[radial-gradient(ellipse_at_10%_35%,rgba(0,123,167,0.2),transparent_44%),radial-gradient(ellipse_at_80%_0%,rgba(255,46,147,0.13),transparent_42%)] pb-6 sm:mb-7 sm:pb-7">
					<div className="flex flex-wrap items-end justify-between gap-5">
						<div>
						<div className="mb-2.5 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#92929D]">
							<span className="h-px w-7 bg-[#FF2E93] shadow-[0_0_10px_2px_rgba(255,46,147,0.55)]" />
							Intelligence workspace
						</div>
						<h1 className="text-[30px] font-bold leading-tight text-[#F5F5F7] drop-shadow-[0_0_24px_rgba(0,123,167,0.28)] sm:text-[38px]">AI Revenue Intelligence</h1>
						<p className="mt-2 text-sm text-[#92929D]">AI-powered insights for recurring revenue growth</p>
						</div>
						<div className="inline-flex items-center gap-2 rounded-md border border-[#007BA7]/30 bg-[#0F1519]/90 px-3.5 py-2.5 shadow-[0_0_20px_rgba(0,123,167,0.11)]">
							<span className="relative flex size-2.5 items-center justify-center">
								<span className="absolute size-full rounded-full bg-[#FF2E93]/70 motion-safe:animate-ping motion-reduce:animate-none" />
								<span className="relative size-2 rounded-full bg-[#38BDF8] shadow-[0_0_10px_2px_rgba(0,123,167,0.8)]" />
							</span>
							<span className="text-[11px] font-semibold text-[#D9F5FF]">Awaiting data</span>
						</div>
					</div>
					<div className="mt-5 flex items-center gap-2 text-[11px] text-[#92929D]">
						<BrainCircuit aria-hidden="true" size={14} className="text-[#FF2E93] drop-shadow-[0_0_8px_rgba(255,46,147,0.7)]" />
						No data available to analyze subscription, invoice or payment patterns
					</div>
				</header>

				<section aria-label="Revenue prediction" className="relative mb-5 overflow-hidden rounded-lg border border-[#007BA7]/30 bg-[#17171C]/95 shadow-[0_18px_48px_rgba(0,0,0,0.3),0_0_34px_rgba(0,123,167,0.09)]">
					<div className="pointer-events-none absolute -right-20 -top-24 size-72 rounded-full bg-[#007BA7]/[0.07] blur-3xl" />
					<div className="relative flex flex-wrap items-start justify-between gap-5 border-b border-[#24242B] px-5 py-5 sm:px-6 sm:py-6">
						<div className="flex items-start gap-3">
							<div className="flex size-10 shrink-0 items-center justify-center rounded-md border border-[#007BA7]/35 bg-[#007BA7]/[0.10] text-[#38BDF8] shadow-[0_0_20px_rgba(0,123,167,0.2)]">
								<BrainCircuit aria-hidden="true" size={19} />
							</div>
							<div>
								<div className="flex flex-wrap items-center gap-2">
									<h2 className="text-base font-semibold text-[#F5F5F7]">Revenue prediction</h2>
									<span className="rounded-sm border border-[#FF2E93]/25 bg-[#FF2E93]/[0.08] px-2 py-0.5 text-[9px] font-semibold tracking-[0.1em] text-[#FF80BC]">AI FORECAST</span>
								</div>
								<p className="mt-1 text-[11px] text-[#92929D]">Historical performance and projected recurring revenue</p>
							</div>
						</div>
						<div className="grid w-full grid-cols-2 gap-3 sm:w-auto sm:grid-cols-4 sm:gap-5">
							<div><p className="text-[10px] text-[#92929D]">Current MRR</p><p className="mt-1 text-lg font-semibold text-[#F5F5F7]">—</p></div>
							<div><p className="text-[10px] text-[#92929D]">Predicted MRR</p><p className="mt-1 text-lg font-semibold text-[#FF80BC] drop-shadow-[0_0_10px_rgba(255,46,147,0.22)]">—</p></div>
							<div><p className="text-[10px] text-[#92929D]">Predicted Growth</p><p className="mt-1 inline-flex items-center gap-1 text-lg font-semibold text-[#4ADE80]">—</p></div>
							<div><p className="text-[10px] text-[#92929D]">Confidence</p><p className="mt-1 text-lg font-semibold text-[#38BDF8]">—</p></div>
						</div>
					</div>
					<div className="relative px-3 pb-4 pt-5 sm:px-6 sm:pb-5">
						<div className="mb-3 flex flex-wrap items-center justify-between gap-3 px-1">
							<div className="flex items-center gap-4 text-[10px] text-[#92929D]">
								<span className="inline-flex items-center gap-2"><span className="h-0.5 w-4 bg-[#159DCA] shadow-[0_0_7px_rgba(0,123,167,0.8)]" />Historical</span>
								<span className="inline-flex items-center gap-2"><span className="h-0.5 w-4 border-t border-dashed border-[#FF2E93]" />AI prediction</span>
							</div>
							<span className="text-[10px] text-[#777783]">MRR · INR (lakhs)</span>
						</div>
						<div className="relative h-[250px] w-full min-w-0 sm:h-[310px]">
							{forecastData.length === 0 && <div className="absolute inset-0 z-10 flex items-center justify-center text-xs text-[#92929D]">No revenue data available for forecasting.</div>}
							<ResponsiveContainer width="100%" height="100%">
								<AreaChart data={forecastData} margin={{ top: 10, right: 12, left: -14, bottom: 0 }}>
									<defs>
										<linearGradient id="actualRevenueFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#007BA7" stopOpacity={0.3} /><stop offset="95%" stopColor="#007BA7" stopOpacity={0.01} /></linearGradient>
										<linearGradient id="forecastRevenueFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#FF2E93" stopOpacity={0.17} /><stop offset="95%" stopColor="#FF2E93" stopOpacity={0.01} /></linearGradient>
										<filter id="aiChartGlow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
									</defs>
									<CartesianGrid stroke="#92929D" strokeOpacity={0.12} vertical={false} />
									<XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#92929D", fontSize: 11 }} dy={10} />
									<YAxis axisLine={false} tickLine={false} tick={{ fill: "#92929D", fontSize: 10 }} tickFormatter={(value: number) => `₹${value}L`} width={48} />
									<Tooltip
										formatter={(value, name) => [`₹${Number(value).toFixed(2)}L`, name === "actual" ? "Historical MRR" : "Predicted MRR"]}
										contentStyle={{ background: "#111115", border: "1px solid rgba(0,123,167,0.4)", borderRadius: 6, color: "#F5F5F7", boxShadow: "0 0 20px rgba(0,123,167,0.16)" }}
										labelStyle={{ color: "#92929D", marginBottom: 4 }}
										cursor={{ stroke: "#92929D", strokeOpacity: 0.25 }}
									/>
									{forecastData.length > 0 && <ReferenceLine stroke="#92929D" strokeOpacity={0.3} strokeDasharray="3 5" />}
									<Area type="monotone" dataKey="actual" stroke="#159DCA" strokeWidth={2.5} fill="url(#actualRevenueFill)" activeDot={{ r: 5, fill: "#F5F5F7", stroke: "#007BA7", strokeWidth: 3 }} style={{ filter: "url(#aiChartGlow)" }} isAnimationActive animationDuration={900} />
									<Area type="monotone" dataKey="forecast" stroke="#FF2E93" strokeWidth={2.5} strokeDasharray="7 5" fill="url(#forecastRevenueFill)" activeDot={{ r: 5, fill: "#F5F5F7", stroke: "#FF2E93", strokeWidth: 3 }} connectNulls style={{ filter: "url(#aiChartGlow)" }} isAnimationActive animationDuration={1100} />
								</AreaChart>
							</ResponsiveContainer>
						</div>
					</div>
				</section>

				<section aria-label="Key intelligence metrics" className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
					{keyMetrics.map(({ label, value, note, icon: Icon, accent }) => {
						const accentStyles = {
							blue: "border-[#007BA7]/20 hover:border-[#007BA7]/40 text-[#38BDF8] shadow-[0_0_18px_rgba(0,123,167,0.06)]",
							pink: "border-[#FF2E93]/20 hover:border-[#FF2E93]/40 text-[#FF80BC] shadow-[0_0_18px_rgba(255,46,147,0.05)]",
							amber: "border-[#F59E0B]/20 hover:border-[#F59E0B]/40 text-[#FBBF24] shadow-[0_0_18px_rgba(245,158,11,0.04)]",
							green: "border-[#22C55E]/20 hover:border-[#22C55E]/40 text-[#4ADE80] shadow-[0_0_18px_rgba(34,197,94,0.04)]",
						}[accent];
						return (
							<article key={label} className={`flex min-w-0 items-center justify-between gap-3 rounded-lg border bg-[#17171C]/90 px-4 py-4 transition duration-200 hover:-translate-y-0.5 ${accentStyles}`}>
								<div className="min-w-0"><p className="truncate text-[10px] font-medium text-[#92929D]">{label}</p><p className="mt-2 truncate text-xl font-semibold text-[#F5F5F7]">{value}</p><p className="mt-1 text-[9px] text-[#777783]">{note}</p></div>
								<div className="flex size-9 shrink-0 items-center justify-center rounded-md border border-current/20 bg-current/[0.08]"><Icon aria-hidden="true" size={16} /></div>
							</article>
						);
					})}
				</section>

				<section aria-label="AI generated insights" className="mb-5 grid grid-cols-1 gap-3.5 lg:grid-cols-3">
					{insights.map(({ title, text, icon: Icon, accent, label }) => {
						const accentStyles = {
							blue: "border-[#007BA7]/25 hover:border-[#007BA7]/45 shadow-[0_0_18px_rgba(0,123,167,0.06)]",
							pink: "border-[#FF2E93]/25 hover:border-[#FF2E93]/45 shadow-[0_0_20px_rgba(255,46,147,0.07)]",
						}[accent];
						const iconStyles = accent === "pink" ? "border-[#FF2E93]/30 bg-[#FF2E93]/[0.09] text-[#FF80BC] shadow-[0_0_15px_rgba(255,46,147,0.12)]" : "border-[#007BA7]/30 bg-[#007BA7]/[0.09] text-[#38BDF8] shadow-[0_0_15px_rgba(0,123,167,0.12)]";
						return (
							<article key={title} className={`group relative overflow-hidden rounded-lg border bg-[#17171C]/95 p-5 transition duration-200 hover:-translate-y-0.5 ${accentStyles}`}>
								<div className={`pointer-events-none absolute -right-12 -top-14 size-36 rounded-full blur-3xl ${accent === "pink" ? "bg-[#FF2E93]/[0.07]" : "bg-[#007BA7]/[0.07]"}`} />
								<div className="relative mb-4 flex items-center justify-between gap-3">
									<div className={`flex size-9 items-center justify-center rounded-md border ${iconStyles}`}><Icon aria-hidden="true" size={17} /></div>
									<span className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#777783]">{label}</span>
								</div>
								<h3 className="relative text-sm font-semibold text-[#F5F5F7]">{title}</h3>
								<p className="relative mt-2.5 text-[12px] leading-5 text-[#A7A7B1]">{text}</p>
							</article>
						);
					})}
				</section>

				<section aria-label="Recommended actions" className="overflow-hidden rounded-lg border border-[#202027] bg-[#17171C]/95 shadow-[0_12px_34px_rgba(0,0,0,0.22)]">
					<div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#25252C] px-5 py-4 sm:px-6">
						<div className="flex items-center gap-2.5"><div className="flex size-8 items-center justify-center rounded-md border border-[#FF2E93]/25 bg-[#FF2E93]/[0.07] text-[#FF80BC]"><Sparkles aria-hidden="true" size={15} /></div><div><h2 className="text-sm font-semibold text-[#F5F5F7]">Recommended Actions</h2><p className="mt-0.5 text-[10px] text-[#92929D]">Prioritized next steps from your AI analysis</p></div></div>
						<span className="rounded-sm border border-[#007BA7]/20 bg-[#007BA7]/[0.07] px-2 py-1 text-[9px] font-medium text-[#69C9EB]">Awaiting data</span>
					</div>
					<div className="divide-y divide-[#24242B]">
						{recommendations.map(({ title, detail, priority, icon: Icon, accent }, index) => {
							const priorityStyles = accent === "pink" ? "border-[#FF2E93]/25 bg-[#FF2E93]/[0.07] text-[#FF80BC]" : accent === "amber" ? "border-[#F59E0B]/25 bg-[#F59E0B]/[0.07] text-[#FBBF24]" : "border-[#007BA7]/25 bg-[#007BA7]/[0.07] text-[#69C9EB]";
							const iconStyles = accent === "pink" ? "text-[#FF80BC]" : accent === "amber" ? "text-[#FBBF24]" : "text-[#38BDF8]";
							return (
								<div key={title} className="group flex flex-wrap items-center gap-3 px-5 py-4 transition-colors hover:bg-white/[0.015] sm:px-6">
									<div className={`flex size-9 shrink-0 items-center justify-center rounded-md border border-[#292930] bg-[#101014] ${iconStyles}`}><Icon aria-hidden="true" size={16} /></div>
									<div className="min-w-[180px] flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="text-[12px] font-medium text-[#E8E8EC]">{title}</h3><span className={`rounded-sm border px-1.5 py-0.5 text-[9px] font-medium ${priorityStyles}`}>{priority}</span></div><p className="mt-1 text-[10px] text-[#858590]">{detail}</p></div>
									<span className="hidden text-[10px] tabular-nums text-[#62626C] sm:block">0{index + 1}</span>
									<button type="button" aria-label={`Review recommendation: ${title}`} className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#777783] transition hover:bg-[#007BA7]/10 hover:text-[#69C9EB] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#007BA7]"><ArrowRight aria-hidden="true" size={15} /></button>
								</div>
							);
						})}
						{recommendations.length === 0 && <p className="px-5 py-10 text-center text-xs text-[#92929D] sm:px-6">No recommendations available. Add revenue data to generate prioritized actions.</p>}
					</div>
					<div className="flex items-center gap-2 border-t border-[#25252C] px-5 py-3 text-[10px] text-[#777783] sm:px-6"><CheckCircle2 aria-hidden="true" size={13} className="text-[#22C55E]" />No analysis data available <span className="mx-1 text-[#36363E]">·</span><Activity aria-hidden="true" size={13} className="text-[#007BA7]" />Awaiting business data</div>
				</section>
			</div>
		</MainLayout>
	);
}

export default RevenueInsights;
