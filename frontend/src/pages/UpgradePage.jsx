import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { X, ChevronDown, Check, ChevronRight } from "lucide-react";

// Credits icon (exact same as in Profile page)
const CreditsIcon = ({ className, color = "currentColor" }) => (
  <svg viewBox="0 0 1024 1024" fill={color} className={className}>
    <path d="M 498.04 902.32 C487.03,900.01 475.94,891.85 469.24,881.12 C466.30,876.39 464.43,871.45 454.27,841.50 C449.60,827.75 442.50,806.83 438.48,795.00 C434.46,783.17 424.65,754.60 416.68,731.50 C408.71,708.40 399.39,681.40 395.98,671.50 C388.62,650.16 385.22,643.34 378.45,636.41 C370.67,628.43 369.90,628.12 300.00,604.00 C285.98,599.16 263.25,591.29 249.50,586.52 C235.75,581.74 212.35,573.65 197.50,568.54 C161.94,556.30 145.49,550.28 139.99,547.49 C127.63,541.24 116.17,529.21 111.93,518.06 C104.36,498.12 110.23,477.38 127.50,463.09 C139.35,453.28 138.70,453.53 288.34,404.03 C330.05,390.24 366.01,378.02 368.23,376.88 C374.55,373.66 381.40,366.60 384.85,359.76 C386.58,356.32 398.77,321.33 411.93,282.00 C448.35,173.17 459.60,140.54 463.46,132.51 C472.77,113.15 492.48,102.78 514.11,105.84 C532.90,108.49 546.88,120.13 553.76,138.82 C555.11,142.49 572.11,192.83 591.54,250.67 C610.97,308.52 627.63,357.34 628.57,359.17 C631.46,364.83 636.05,369.98 641.39,373.58 C646.67,377.15 663.73,382.97 789.00,424.00 C873.18,451.56 877.75,453.41 890.17,464.84 C907.43,480.74 911.43,504.29 900.21,524.00 C891.35,539.58 880.18,546.86 848.50,557.74 C841.35,560.19 819.30,567.74 799.50,574.52 C691.95,611.32 651.67,625.51 645.98,628.61 C639.57,632.10 632.84,638.77 629.14,645.31 C626.23,650.46 617.93,673.51 600.98,723.50 C589.01,758.79 554.96,857.43 551.01,868.23 C545.18,884.21 537.37,893.59 525.12,899.32 C519.44,901.99 517.22,902.46 509.50,902.63 C504.55,902.74 499.39,902.60 498.04,902.32 Z"/>
  </svg>
);

const UpgradePage = () => {
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [proCredits, setProCredits] = useState(3000);
  const [proCreditsOpen, setProCreditsOpen] = useState(false);
  const [openFaqId, setOpenFaqId] = useState(null);

  const faqItems = [
    {
      id: 1,
      question: "How do credits work?",
      answer: "With a subscription, credits are issued once per month (for each billing period).\nAt the end of each period, any unused credits expire.\n\nAdditional top-up credits are not tied to the subscription and are valid for 1 year from the date of purchase."
    },
    {
      id: 2,
      question: "How many videos can I edit (create) with AI?",
      answer: "The number of videos depends on your available credits.\n\nOn average, 10 credits = 1 fully edited or created video.\nPlans include from 500 credits (~50 videos) to 9000 credits (~900 videos), and you can also purchase additional credits."
    },
    {
      id: 3,
      question: "Which subscription plan includes priority support?",
      answer: "All plans include priority support. We aim to provide fast and high-quality help to every user."
    },
    {
      id: 4,
      question: "What are custom templates and how do they work?",
      answer: "You can create your own custom templates for videos.\nThey help speed up and automate your workflow by letting you reuse the same setup instead of writing long prompts for similar videos.\nThis is especially useful for marketing and other repetitive content tasks."
    },
    {
      id: 5,
      question: "Can I change my subscription after purchase?",
      answer: "Yes. You can upgrade your plan at any time, and the change takes effect immediately. Any unused value difference is credited to your account.\n\nIf you downgrade, the change will take effect at the end of your current billing period, and your current plan stays active until then."
    }
  ];

  const plans = {
    starter: {
      name: "Starter",
      monthlyPrice: 20,
      annualPrice: 16,
      credits: 500,
      features: [
        "Full AI editor access",
        "AI cuts & captions",
        "AI script, speech & dubbing",
        "AI visuals & sound",
        "5 Custom templates",
        "Fast export (1080p, parallel 3 videos)"
      ]
    },
    pro: {
      name: "Creator",
      monthlyPrice: 69,
      annualPrice: 59,
      credits: proCredits,
      features: [
        "Everything in Starter, plus:",
        "Priority export (4K, parallel 8 videos)",
        "Unlimited custom templates",
        "Team workspace"
      ],
      hasCreditsDropdown: true
    }
  };

  const PricingCard = ({ plan, planKey }) => {
    const isMonthly = billingCycle === "monthly";
    const price = isMonthly ? plan.monthlyPrice : plan.annualPrice;

    return (
      <div className="pricing-card">
        <div className="pricing-card-top">
          <div className="pricing-card-header">
            <h3 className="pricing-card-name">{plan.name}</h3>
            <div className="pricing-card-price-row">
              <div className="pricing-price">€{price}</div>
              <span className="pricing-period">Per month</span>
            </div>
          </div>

          {/* Credits Box */}
          <div className="pricing-credits-box">
          <CreditsIcon className="pricing-credits-icon" color="#FFFFFF" />
          <span className="pricing-credits-text">{plan.credits} credits</span>
          
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
                  <button onClick={() => { setProCredits(3000); setProCreditsOpen(false); }}>
                    <CreditsIcon className="pricing-credits-icon" color="#FFFFFF" />
                    <span>3000 credits</span>
                  </button>
                  <button onClick={() => { setProCredits(6000); setProCreditsOpen(false); }}>
                    <CreditsIcon className="pricing-credits-icon" color="#FFFFFF" />
                    <span>6000 credits</span>
                  </button>
                  <button onClick={() => { setProCredits(9000); setProCreditsOpen(false); }}>
                    <CreditsIcon className="pricing-credits-icon" color="#FFFFFF" />
                    <span>9000 credits</span>
                  </button>
                </div>
              )}
            </div>
          )}
          </div>

          {/* Subscribe Button */}
          <button className="pricing-subscribe-btn">Upgrade</button>
        </div>

        <div className="pricing-card-bottom">
          {/* Features List with scrollable container */}
          <div className="pricing-features">
          <p className="pricing-features-title">Includes:</p>
          <div className="pricing-features-scroll">
            <ul className="pricing-features-list">
              {plan.features.map((feature, idx) => (
                <li key={idx} className={planKey === 'pro' && idx === 0 ? 'no-check' : ''}>
                  <Check className="pricing-check-icon" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>
          </div>
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
          <PricingCard plan={plans.pro} planKey="pro" />
        </div>

        {/* FAQ Section */}
        <div className="upgrade-faq-section">
          <h2 className="upgrade-faq-title">Frequently Asked Questions</h2>
          
          <div className="upgrade-faq-list">
            {faqItems.map((item) => (
              <div 
                key={item.id}
                className={`faq-item ${openFaqId === item.id ? 'open' : ''}`}
              >
                <button 
                  className="faq-question-btn"
                  onClick={() => setOpenFaqId(openFaqId === item.id ? null : item.id)}
                >
                  <span className="faq-question-text">{item.question}</span>
                  <ChevronRight className={`faq-arrow ${openFaqId === item.id ? 'open' : ''}`} />
                </button>
                
                <div className="faq-answer-wrapper">
                  <div className="faq-answer">
                    {item.answer.split('\n').map((line, idx) => (
                      <p key={idx}>{line}</p>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradePage;
