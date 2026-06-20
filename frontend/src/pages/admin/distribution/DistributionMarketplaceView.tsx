import { ArrowRight, Building2, Search, Sparkles, Star, Store } from "lucide-react";
import type { FormEvent } from "react";

import { PanelTitle } from "../../../components/PanelTitle";
import { SegmentedFilter } from "../../../components/SegmentedFilter";
import { StatusBadge } from "../../../components/StatusBadge";
import { SummaryItem } from "../../../components/SummaryItem";

export type MarketplaceCard = {
  id: string;
  title: string;
  company: string;
  category: string;
  status: string;
  reward: string;
  rewardAmount: number;
  conversionRate: string;
  conversionScore: number;
  activeLabel: string;
  activeCount: number;
  trustRequirement: string;
  routeCount: number;
  joinedCount: number;
  tone: "violet" | "amber" | "green" | "rose" | "blue";
};

type DistributionMarketplaceViewProps = {
  activeDistributorCount: number;
  distributorsCount: number;
  featuredCampaign?: MarketplaceCard;
  marketplaceActiveCount: number;
  marketplaceCards: MarketplaceCard[];
  marketplaceCategories: string[];
  marketplaceFilter: string;
  marketplaceSearch: string;
  marketplaceSort: string;
  opportunitiesCount: number;
  publishedOpportunityCount: number;
  routedOfferCount: number;
  submittedTenant: string;
  tenantCode: string;
  onCampaignSelect: (opportunityId: string) => void;
  onMarketplaceFilterChange: (filter: string) => void;
  onMarketplaceSearchChange: (search: string) => void;
  onMarketplaceSortChange: (sort: string) => void;
  onSubmitTenant: (event: FormEvent<HTMLFormElement>) => void;
  onTenantCodeChange: (tenantCode: string) => void;
};

export function DistributionMarketplaceView({
  activeDistributorCount,
  distributorsCount,
  featuredCampaign,
  marketplaceActiveCount,
  marketplaceCards,
  marketplaceCategories,
  marketplaceFilter,
  marketplaceSearch,
  marketplaceSort,
  opportunitiesCount,
  publishedOpportunityCount,
  routedOfferCount,
  submittedTenant,
  tenantCode,
  onCampaignSelect,
  onMarketplaceFilterChange,
  onMarketplaceSearchChange,
  onMarketplaceSortChange,
  onSubmitTenant,
  onTenantCodeChange,
}: DistributionMarketplaceViewProps) {
  return (
    <>
      <section className="earnings-command-header marketplace-topbar">
        <div className="earnings-breadcrumb">
          <span>Amplifi</span>
          <span>Marketplace</span>
          <strong>Distributor view</strong>
        </div>
        <div className="earnings-search">
          <Search size={16} />
          <input
            aria-label="Search campaigns and demand"
            placeholder="Search campaigns, companies, products..."
            value={marketplaceSearch}
            onChange={(event) => onMarketplaceSearchChange(event.target.value)}
          />
        </div>
        <div className="earnings-header-actions">
          <span className="earnings-rank-pill">
            <Building2 size={14} />
            {submittedTenant} - Network
          </span>
          <a className="button" href="/admin/distribution/operations">
            <Store size={16} />
            Operations
          </a>
        </div>
      </section>

      <section className="marketplace-hero">
        <div>
          <h1>Marketplace</h1>
          <p>Browse company-created demand, compare payouts and conversion signals, then choose the campaigns worth joining.</p>
        </div>
        <form className="marketplace-scope-form" onSubmit={onSubmitTenant}>
          <label htmlFor="distribution-tenant">Tenant</label>
          <input id="distribution-tenant" value={tenantCode} onChange={(event) => onTenantCodeChange(event.target.value)} />
          <button className="button" type="submit">
            Load
          </button>
        </form>
      </section>

      <section className="marketplace-feature-grid">
        <div className="marketplace-feature-card">
          <div className="marketplace-feature-kicker">
            <Sparkles size={15} />
            Featured demand
          </div>
          {featuredCampaign ? (
            <>
              <h2>{featuredCampaign.title}</h2>
              <p>
                {featuredCampaign.company} - {featuredCampaign.category} - {featuredCampaign.status}
              </p>
              <div className="marketplace-feature-metrics">
                <SummaryItem label="Payout" value={featuredCampaign.reward} />
                <SummaryItem label="Conversion" value={featuredCampaign.conversionRate} />
                <SummaryItem label="Active" value={featuredCampaign.activeLabel} />
              </div>
              <button className="button" type="button" onClick={() => onCampaignSelect(featuredCampaign.id)}>
                Select campaign
                <ArrowRight size={16} />
              </button>
            </>
          ) : (
            <div className="earnings-empty-card">No campaigns match the current filters.</div>
          )}
        </div>

        <div className="marketplace-insight-panel earnings-dark-panel">
          <div className="earnings-panel-head">
            <div>
              <PanelTitle
                help="Live marketplace posture based on distributor, opportunity, route, and wallet records."
                title="Marketplace pulse"
              />
              <div className="panel-subtitle">Demand, eligibility, and route readiness.</div>
            </div>
            <StatusBadge label={routedOfferCount ? "Routes waiting" : "Operational"} tone={routedOfferCount ? "info" : "success"} />
          </div>
          <div className="marketplace-pulse-grid">
            <SummaryItem label="Campaigns" value={opportunitiesCount} />
            <SummaryItem label="Published" value={publishedOpportunityCount} />
            <SummaryItem label="Active distributors" value={`${activeDistributorCount}/${distributorsCount}`} />
            <SummaryItem label="Active audience" value={marketplaceActiveCount || "-"} />
          </div>
        </div>
      </section>

      <section className="marketplace-browse-panel earnings-dark-panel">
        <div className="marketplace-browse-header">
          <div>
            <PanelTitle
              help="Distributor-facing view of company-created campaigns and demand currently loaded from marketplace opportunities."
              title="Campaigns and demand"
            />
            <div className="panel-subtitle">
              {marketplaceCards.length} visible - {opportunitiesCount} loaded from backend
            </div>
          </div>
          <div className="marketplace-filter-row">
            <SegmentedFilter
              ariaLabel="Marketplace filters"
              chipClassName="marketplace-chip"
              className="marketplace-filter-options"
              onChange={onMarketplaceFilterChange}
              options={marketplaceCategories.map((category) => ({
                label: category === "ALL" ? "All" : category,
                value: category,
              }))}
              value={marketplaceFilter}
            />
            <select
              className="marketplace-sort"
              aria-label="Sort campaigns"
              value={marketplaceSort}
              onChange={(event) => onMarketplaceSortChange(event.target.value)}
            >
              <option value="HIGHEST_PAYING">Highest paying</option>
              <option value="TRENDING">Trending</option>
              <option value="NEW">New</option>
            </select>
          </div>
        </div>

        <div className="marketplace-card-grid">
          {marketplaceCards.length ? (
            marketplaceCards.map((card) => (
              <MarketplaceCampaignCard card={card} key={card.id} onSelect={() => onCampaignSelect(card.id)} />
            ))
          ) : (
            <div className="earnings-empty-card">No company-created demand matches this view.</div>
          )}
        </div>
      </section>
    </>
  );
}

function MarketplaceCampaignCard({ card, onSelect }: { card: MarketplaceCard; onSelect: () => void }) {
  return (
    <article className={`marketplace-campaign-card ${card.tone}`}>
      <div className="marketplace-campaign-band">
        <div>
          <span>{card.company}</span>
          <h3>{card.title}</h3>
        </div>
        <StatusBadge label={card.category} tone="neutral" />
      </div>
      <div className="marketplace-campaign-body">
        <div className="marketplace-campaign-metrics">
          <div>
            <strong>{card.reward}</strong>
            <span>per activation</span>
          </div>
          <div>
            <strong>{card.conversionRate}</strong>
            <span>conversion</span>
          </div>
          <div>
            <strong>{card.activeLabel}</strong>
            <span>active</span>
          </div>
        </div>
        <div className="marketplace-campaign-foot">
          <span>
            <Star size={13} />
            {card.trustRequirement}
          </span>
          <span>
            {card.routeCount} routes - {card.joinedCount} joined
          </span>
        </div>
        <button className="button" type="button" onClick={onSelect}>
          Join
          <ArrowRight size={15} />
        </button>
      </div>
    </article>
  );
}
