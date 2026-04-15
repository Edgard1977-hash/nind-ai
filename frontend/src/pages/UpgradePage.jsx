import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { X, ChevronDown, HelpCircle, Check, ChevronRight, Lock } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Star icon (same as in Profile page)
const StarIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
);

const LogoSvg = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="25 130 1360 420" className={className}>
    <g>
      <path d="M 97.00 546.37 C64.96,542.61 38.70,519.91 29.71,488.20 C27.57,480.64 27.52,479.13 27.23,405.59 C26.95,333.02 27.00,330.43 28.98,322.59 C36.12,294.22 57.79,272.03 85.13,265.08 C104.06,260.27 118.50,261.95 137.00,271.12 C146.08,275.62 148.73,277.56 156.64,285.46 C166.43,295.25 172.10,304.58 176.02,317.36 C179.55,328.87 180.00,338.89 179.99,404.97 C179.99,483.75 179.58,487.79 169.77,506.21 C164.02,517.01 149.05,531.58 137.45,537.68 C125.31,544.06 108.34,547.70 97.00,546.37 ZM 260.50 503.84 C242.54,500.46 231.50,494.62 218.44,481.56 C207.83,470.94 203.62,464.34 198.99,451.00 C195.93,442.19 195.16,423.24 195.07,354.47 C194.98,286.29 195.32,283.21 204.83,264.50 C208.58,257.11 211.10,253.81 218.95,246.00 C229.80,235.21 236.28,231.02 248.77,226.73 C255.78,224.32 259.72,223.63 268.78,223.24 C282.25,222.65 290.32,224.26 302.63,229.98 C320.14,238.12 332.34,250.33 339.87,267.27 C346.44,282.04 347.06,288.80 347.69,353.00 C348.44,430.46 347.23,445.08 338.57,462.50 C331.58,476.58 321.19,487.69 308.04,495.15 C293.79,503.24 275.30,506.62 260.50,503.84 ZM 1209.50 500.98 C1182.05,497.49 1154.42,481.64 1137.67,459.76 C1122.41,439.83 1113.49,419.15 1109.52,394.47 C1107.54,382.16 1107.51,350.71 1109.46,338.78 C1117.87,287.48 1152.09,246.54 1196.00,235.25 C1205.58,232.79 1208.16,232.55 1225.50,232.53 C1242.33,232.51 1245.47,232.78 1253.00,234.84 C1267.96,238.93 1284.16,248.64 1289.31,256.59 C1290.51,258.45 1291.84,259.98 1292.25,259.99 C1292.66,259.99 1293.00,233.03 1293.00,200.06 C1293.00,153.20 1293.27,139.94 1294.25,139.31 C1294.94,138.86 1313.89,138.37 1336.36,138.21 C1372.09,137.95 1377.52,138.11 1379.61,139.48 L 1382.00 141.05 L 1382.00 316.94 C1382.00,413.68 1381.73,493.55 1381.39,494.42 C1380.85,495.83 1376.13,496.00 1338.41,496.00 L 1296.04 496.00 L 1295.38 493.38 C1295.02,491.93 1294.97,486.49 1295.29,481.29 L 1295.85 471.82 L 1290.44 477.81 C1281.22,487.99 1266.13,496.25 1250.53,499.65 C1242.13,501.49 1219.28,502.23 1209.50,500.98 ZM 1257.84 425.55 C1272.94,421.54 1284.68,408.23 1290.63,388.40 C1293.37,379.26 1293.14,352.90 1290.24,343.81 C1283.13,321.53 1268.48,308.09 1249.38,306.31 C1238.34,305.28 1226.06,308.93 1217.25,315.87 C1205.18,325.38 1195.96,347.79 1196.01,367.50 C1196.06,387.92 1206.51,410.38 1220.42,419.94 C1230.00,426.54 1245.44,428.85 1257.84,425.55 ZM 412.61 494.42 C411.57,491.72 411.94,240.65 412.98,239.00 C413.80,237.71 419.62,237.50 455.38,237.50 C478.18,237.50 497.08,237.75 497.39,238.06 C497.70,238.37 498.08,243.54 498.23,249.56 L 498.50 260.50 L 506.50 252.45 C515.47,243.43 523.79,238.51 536.02,234.98 C545.40,232.27 569.68,231.16 580.99,232.93 C618.09,238.71 642.85,263.57 652.28,304.50 C654.28,313.19 654.37,316.68 654.72,404.76 L 655.08 496.02 L 611.29 495.76 L 567.50 495.50 L 566.99 416.50 C566.48,338.17 566.45,337.44 564.25,331.00 C561.17,321.98 555.79,315.16 549.00,311.68 C543.78,309.00 542.94,308.88 532.50,309.20 C522.57,309.52 521.04,309.82 516.77,312.36 C511.35,315.58 507.35,319.95 505.21,325.00 C501.17,334.55 501.07,336.69 501.04,417.75 L 501.00 496.00 L 457.11 496.00 C418.00,496.00 413.15,495.83 412.61,494.42 ZM 700.41 494.85 C699.30,493.07 699.46,240.13 700.56,239.08 C701.08,238.59 720.55,238.04 743.83,237.85 C784.79,237.51 786.21,237.56 787.58,239.44 C788.79,241.09 789.00,259.96 788.99,366.44 C788.98,435.22 788.70,492.51 788.37,493.75 L 787.77 496.00 L 744.44 496.00 C712.79,496.00 700.93,495.69 700.41,494.85 ZM 835.51 492.75 C834.59,487.65 835.40,239.27 836.33,238.33 C837.25,237.42 919.49,237.15 920.40,238.07 C920.71,238.38 921.09,243.55 921.23,249.57 L 921.50 260.50 L 929.50 252.39 C936.02,245.78 939.07,243.54 946.00,240.26 C960.84,233.25 964.90,232.49 987.00,232.56 C1005.32,232.62 1007.04,232.79 1015.45,235.36 C1043.32,243.90 1062.09,262.76 1071.54,291.72 C1077.68,310.54 1077.40,305.29 1077.75,404.76 L 1078.08 496.02 L 1034.29 495.76 L 990.50 495.50 L 990.00 416.00 L 989.50 336.50 L 987.18 330.76 C982.45,319.04 976.22,312.27 968.12,310.02 C963.36,308.69 950.98,308.72 945.69,310.07 C935.91,312.56 929.03,320.19 925.93,332.01 C924.10,338.98 924.00,343.51 924.00,417.68 L 924.00 496.00 L 880.05 496.00 L 836.09 496.00 L 835.51 492.75 ZM 700.25 216.34 C699.28,215.95 699.00,207.43 699.00,178.47 L 699.00 141.11 L 701.22 139.56 C703.15,138.21 708.97,138.00 744.57,138.00 C783.14,138.00 785.79,138.11 787.35,139.83 C788.82,141.46 789.00,145.64 789.00,178.72 C789.00,211.60 788.82,215.85 787.42,216.39 C785.53,217.12 702.05,217.06 700.25,216.34 Z" fill="currentColor"/>
    </g>
  </svg>
);

const UpgradePage = () => {
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState("monthly"); // "monthly" or "annually"
  const [starterAiOpen, setStarterAiOpen] = useState(false);
  const [plusAiOpen, setPlusAiOpen] = useState(false);
  const [proAiOpen, setProAiOpen] = useState(false);
  const [proCredits, setProCredits] = useState(3000);
  const [proCreditsOpen, setProCreditsOpen] = useState(false);

  const aiTools = [
    { name: "AI Speech", locked: false },
    { name: "AI Sound design", locked: false },
    { name: "AI Translation", locked: true, tooltip: "Available in Plus and Pro" },
    { name: "AI Cut", locked: false },
    { name: "AI Script", locked: true, tooltip: "Available in Plus and Pro" },
    { name: "AI Color grading", locked: false },
    { name: "AI Subtitles", locked: false },
  ];

  const plans = {
    starter: {
      name: "Starter",
      monthlyPrice: 9,
      annualPrice: 7,
      credits: 200,
      features: [
        "Watermark removal",
        "5 Custom templates",
        "Parallel generation: up to 2 videos",
        "Standard generation"
      ],
      aiTools: aiTools
    },
    plus: {
      name: "Plus",
      monthlyPrice: 12,
      monthlyOriginal: 20,
      annualPrice: 12,
      credits: 500,
      features: [
        "Watermark removal",
        "30 Custom templates",
        "Parallel generation: up to 3 videos",
        "Fast generation"
      ],
      aiTools: aiTools.map(tool => ({ ...tool, locked: false }))
    },
    pro: {
      name: "Pro",
      monthlyPrice: 69,
      annualPrice: 59,
      credits: proCredits,
      features: [
        "Watermark removal",
        "Unlimited custom templates",
        "Parallel generation: up to 8 videos",
        "Ultra-fast generation"
      ],
      aiTools: aiTools.map(tool => ({ ...tool, locked: false })),
      hasCreditsDropdown: true
    }
  };

  const PricingCard = ({ plan, planKey }) => {
    const isMonthly = billingCycle === "monthly";
    const price = isMonthly ? plan.monthlyPrice : plan.annualPrice;
    const originalPrice = plan.monthlyOriginal;
    
    const aiOpen = planKey === "starter" ? starterAiOpen : 
                   planKey === "plus" ? plusAiOpen : proAiOpen;
    const setAiOpen = planKey === "starter" ? setStarterAiOpen : 
                      planKey === "plus" ? setPlusAiOpen : setProAiOpen;

    return (
      <div className="pricing-card">
        <div className="pricing-card-header">
          <h3 className="pricing-card-name">{plan.name}</h3>
          <div className="pricing-card-price-row">
            {originalPrice && isMonthly && (
              <span className="pricing-original-price">€{originalPrice}</span>
            )}
            <div className="pricing-price">€{price}</div>
            <span className="pricing-period">Per month</span>
          </div>
        </div>

        {/* Credits Box */}
        <div className="pricing-credits-box">
          <StarIcon className="pricing-star-icon" />
          <span className="pricing-credits-text">{plan.credits} credits</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="pricing-help-btn">
                  <HelpCircle className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Credits are used for video generation</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          {plan.hasCreditsDropdown && (
            <div className="pricing-credits-dropdown-wrapper">
              <button 
                className="pricing-credits-dropdown-btn"
                onClick={() => setProCreditsOpen(!proCreditsOpen)}
              >
                <ChevronDown className={`w-4 h-4 transition-transform ${proCreditsOpen ? 'rotate-180' : ''}`} />
              </button>
              {proCreditsOpen && (
                <div className="pricing-credits-dropdown-menu">
                  <button onClick={() => { setProCredits(3000); setProCreditsOpen(false); }}>3000</button>
                  <button onClick={() => { setProCredits(6000); setProCreditsOpen(false); }}>6000</button>
                  <button onClick={() => { setProCredits(9000); setProCreditsOpen(false); }}>9000</button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Subscribe Button */}
        <button className="pricing-subscribe-btn">Upgrade</button>

        {/* Features List */}
        <div className="pricing-features">
          <p className="pricing-features-title">Includes:</p>
          <ul className="pricing-features-list">
            {plan.features.map((feature, idx) => (
              <li key={idx}>
                <Check className="pricing-check-icon" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* AI Editing Tools Collapsible */}
        <Collapsible open={aiOpen} onOpenChange={setAiOpen}>
          <CollapsibleTrigger className="pricing-ai-trigger">
            <span>AI Editing tools</span>
            <ChevronRight className={`pricing-ai-arrow ${aiOpen ? 'rotate-90' : ''}`} />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <ul className="pricing-ai-list">
              {plan.aiTools.map((tool, idx) => (
                <li key={idx}>
                  <span>{idx + 1}. {tool.name}</span>
                  {tool.locked && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button className="pricing-lock-btn">
                            <Lock className="w-3 h-3" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{tool.tooltip}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </li>
              ))}
            </ul>
          </CollapsibleContent>
        </Collapsible>
      </div>
    );
  };

  return (
    <div className="upgrade-page">
      {/* Header with logo and close button */}
      <header className="upgrade-header">
        <div className="upgrade-header-logo" onClick={() => navigate("/")}>
          <LogoSvg className="upgrade-logo-svg" />
        </div>
        <button className="upgrade-close-btn" onClick={() => navigate("/")}>
          <X className="w-6 h-6" />
        </button>
      </header>

      {/* Main Content */}
      <div className="upgrade-content">
        <h1 className="upgrade-title">Pick your plan</h1>
        <p className="upgrade-subtitle">Create more, better and faster</p>

        {/* Billing Toggle */}
        <div className="upgrade-billing-toggle">
          <button 
            className={`upgrade-toggle-btn ${billingCycle === "monthly" ? "active" : ""}`}
            onClick={() => setBillingCycle("monthly")}
          >
            Monthly
          </button>
          <button 
            className={`upgrade-toggle-btn ${billingCycle === "annually" ? "active" : ""}`}
            onClick={() => setBillingCycle("annually")}
          >
            Annually
          </button>
        </div>

        {/* Pricing Cards */}
        <div className="upgrade-pricing-cards">
          <PricingCard plan={plans.starter} planKey="starter" />
          <PricingCard plan={plans.plus} planKey="plus" />
          <PricingCard plan={plans.pro} planKey="pro" />
        </div>
      </div>
    </div>
  );
};

export default UpgradePage;
