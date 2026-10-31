import type { ReactNode } from "react";
import Sidebar from "./Sidebar";

interface MainLayoutProps {
	children: ReactNode;
}

function MainLayout({ children }: MainLayoutProps) {
	return (
		<div className="min-h-screen bg-[#0A0A0C]">
			<div className="hidden md:block">
				<Sidebar />
			</div>
			<main className="relative isolate min-h-screen min-w-0 bg-[#0A0A0C] bg-[radial-gradient(ellipse_at_82%_0%,rgba(0,123,167,0.12),transparent_38%),radial-gradient(ellipse_at_15%_72%,rgba(255,46,147,0.045),transparent_34%)] text-[#F5F5F7] md:ml-[250px]">
				{children}
			</main>
		</div>
	);
}

export default MainLayout;
