import React from "react";
import { BarChart3, Clock, TrendingUp, Users } from "lucide-react";
import { SummaryCard } from "./SummaryCard";

export function SummaryCards({ displayMetrics, searchQuery, loading }) {
    const isSearching = Boolean(searchQuery.trim());

    return (
        <section className="hn-cards" aria-label="Onboarding summary">
            <SummaryCard
                id="card-total-partners"
                icon={Users}
                label={isSearching ? "Matching Partners" : "Total Partners Onboarded"}
                value={displayMetrics?.totalPartners}
                accent="teal"
                loading={loading}
            />
            <SummaryCard
                id="card-min-days"
                icon={Clock}
                label="Minimum Onboarding Days"
                value={displayMetrics?.minDays}
                unit=" days"
                accent="blue"
                loading={loading}
            />
            <SummaryCard
                id="card-max-days"
                icon={TrendingUp}
                label="Maximum Onboarding Days"
                value={displayMetrics?.maxDays}
                unit=" days"
                accent="amber"
                loading={loading}
            />
            <SummaryCard
                id="card-avg-days"
                icon={BarChart3}
                label="Average Onboarding Days"
                value={displayMetrics?.avgDays}
                unit=" days"
                accent="slate"
                loading={loading}
            />
        </section>
    );
}
