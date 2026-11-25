import React from "react";
import { Clock, ArrowRight, ShieldCheck, Layers, Bot, FileText, CheckCircle2 } from "lucide-react";
import Button from "./ui/Button";
import Badge from "./ui/Badge";
import { Card, CardContent } from "./ui/Card";

export default function StubPage({
  milestone = "Milestone 4",
  title = "Module Under Development",
  agentName = "Executive Report Agent",
  description = "This module is scheduled for future delivery per the Project Scope Specification.",
  plannedFeatures = [],
  setPage
}) {
  return (
    <div className="fin-stub-page max-w-4xl mx-auto py-8 px-4 animate-fadeIn space-y-6">
      {/* Header Banner */}
      <div className="p-8 border border-subtle rounded-xl bg-card text-center space-y-4 shadow-lg">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-accent/10 border border-accent/30 text-accent mb-2">
          <Clock size={28} />
        </div>

        <div className="flex items-center justify-center gap-2">
          <span className="fin-badge fin-badge-warning text-xs font-mono font-semibold uppercase tracking-wider px-3 py-1">
            {milestone} — Under Development
          </span>
          <span className="fin-badge fin-badge-secondary text-xs font-mono px-2 py-1">
            Scheduled Scope
          </span>
        </div>

        <h1 className="text-2xl font-bold text-main tracking-tight">
          {title}
        </h1>

        <p className="text-muted text-sm max-w-xl mx-auto leading-relaxed">
          {description}
        </p>

        {/* Active Scope Badge */}
        <div className="pt-2">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-emerald-300 text-xs">
            <CheckCircle2 size={14} className="text-emerald-400" />
            <span>Currently Active &amp; Verified: <strong>Milestone 1</strong> (Document Intelligence) &amp; <strong>Milestone 2</strong> (Extraction &amp; Red Flags)</span>
          </div>
        </div>
      </div>

      {/* Planned Capabilities Grid */}
      {plannedFeatures && plannedFeatures.length > 0 && (
        <div className="p-6 border border-subtle rounded-xl bg-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-subtle">
            <h3 className="text-sm font-semibold text-main flex items-center gap-2">
              <Layers size={16} className="text-accent" />
              <span>Planned Capabilities for {agentName}</span>
            </h3>
            <span className="text-[11px] text-muted font-mono">Future Milestone Roadmap</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {plannedFeatures.map((feat, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-card-subtle border border-subtle space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-accent/20 text-accent text-[11px] font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <strong className="text-xs text-main">{feat.title}</strong>
                </div>
                <p className="text-[11px] text-muted leading-relaxed pl-7">
                  {feat.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Navigation to Implemented Modules */}
      <div className="p-6 border border-subtle rounded-xl bg-card space-y-4">
        <h4 className="text-xs font-semibold text-muted uppercase tracking-wider">
          Explore Implemented &amp; Live Modules:
        </h4>

        <div className="flex flex-wrap gap-3">
          {setPage && (
            <>
              <Button
                variant="primary"
                size="sm"
                icon={Bot}
                onClick={() => setPage("AI Research")}
              >
                Go to AI Research (Milestone 1)
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={Layers}
                onClick={() => setPage("Financial Analysis")}
              >
                Inspect Financial Analysis (Milestone 2)
              </Button>
              <Button
                variant="outline"
                size="sm"
                icon={FileText}
                onClick={() => setPage("Documents")}
              >
                View Document Library
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

