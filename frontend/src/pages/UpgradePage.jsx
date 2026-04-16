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

// Credits icon (exact same as in Profile page)
const CreditsIcon = ({ className, color = "currentColor" }) => (
  <svg viewBox="0 0 1024 1024" fill={color} className={className}>
    <path d="M 498.04 902.32 C487.03,900.01 475.94,891.85 469.24,881.12 C466.30,876.39 464.43,871.45 454.27,841.50 C449.60,827.75 442.50,806.83 438.48,795.00 C434.46,783.17 424.65,754.60 416.68,731.50 C408.71,708.40 399.39,681.40 395.98,671.50 C388.62,650.16 385.22,643.34 378.45,636.41 C370.67,628.43 369.90,628.12 300.00,604.00 C285.98,599.16 263.25,591.29 249.50,586.52 C235.75,581.74 212.35,573.65 197.50,568.54 C161.94,556.30 145.49,550.28 139.99,547.49 C127.63,541.24 116.17,529.21 111.93,518.06 C104.36,498.12 110.23,477.38 127.50,463.09 C139.35,453.28 138.70,453.53 288.34,404.03 C330.05,390.24 366.01,378.02 368.23,376.88 C374.55,373.66 381.40,366.60 384.85,359.76 C386.58,356.32 398.77,321.33 411.93,282.00 C448.35,173.17 459.60,140.54 463.46,132.51 C472.77,113.15 492.48,102.78 514.11,105.84 C532.90,108.49 546.88,120.13 553.76,138.82 C555.11,142.49 572.11,192.83 591.54,250.67 C610.97,308.52 627.63,357.34 628.57,359.17 C631.46,364.83 636.05,369.98 641.39,373.58 C646.67,377.15 663.73,382.97 789.00,424.00 C873.18,451.56 877.75,453.41 890.17,464.84 C907.43,480.74 911.43,504.29 900.21,524.00 C891.35,539.58 880.18,546.86 848.50,557.74 C841.35,560.19 819.30,567.74 799.50,574.52 C691.95,611.32 651.67,625.51 645.98,628.61 C639.57,632.10 632.84,638.77 629.14,645.31 C626.23,650.46 617.93,673.51 600.98,723.50 C589.01,758.79 554.96,857.43 551.01,868.23 C545.18,884.21 537.37,893.59 525.12,899.32 C519.44,901.99 517.22,902.46 509.50,902.63 C504.55,902.74 499.39,902.60 498.04,902.32 Z"/>
  </svg>
);

const UpgradePage = () => {
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState("monthly");
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
          <CreditsIcon className="pricing-credits-icon" color="#FFD700" />
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
            
            {/* AI Editing Tools as collapsible item in the list */}
            <li>
              <Check className="pricing-check-icon" />
              <Collapsible open={aiOpen} onOpenChange={setAiOpen}>
                <CollapsibleTrigger className="pricing-ai-trigger-inline">
                  <span>AI Editing tools</span>
                  <ChevronRight className={`pricing-ai-arrow-inline ${aiOpen ? 'rotate-90' : ''}`} />
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <ul className="pricing-ai-list-nested">
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
            </li>
          </ul>
        </div>
      </div>
    );
  };

  return (
    <div className="upgrade-page">
      {/* Header with close button (left) */}
      <header className="upgrade-header">
        <button className="upgrade-close-btn" onClick={() => navigate("/")}>
          <X className="w-5 h-5" />
        </button>
      </header>

      {/* Main Content */}
      <div className="upgrade-content">
        <h2 className="upgrade-title">Pick your plan</h2>
        <p className="upgrade-subtitle">Create more, better and faster</p>

        {/* Billing Tabs with animation */}
        <div className="upgrade-billing-tabs">
          <div 
            className="upgrade-billing-indicator"
            style={{
              width: 'calc(50% - 4px)',
              left: billingCycle === 'monthly' ? '4px' : '50%',
            }}
          />
          <button 
            className={`upgrade-billing-tab ${billingCycle === "monthly" ? "active" : ""}`}
            onClick={() => setBillingCycle("monthly")}
          >
            Monthly
          </button>
          <button 
            className={`upgrade-billing-tab ${billingCycle === "annually" ? "active" : ""}`}
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
