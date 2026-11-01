const GenerationModeToggle = ({ mode, onChange }) => (
  <div className="gen-mode-toggle" role="tablist" aria-label="Generation mode">
    <button
      type="button"
      role="tab"
      aria-selected={mode === "basic"}
      className={mode === "basic" ? "active" : ""}
      onClick={() => onChange("basic")}
      data-testid="mode-basic"
    >
      Basic
    </button>
    <button
      type="button"
      role="tab"
      aria-selected={mode === "enhanced"}
      className={mode === "enhanced" ? "active" : ""}
      onClick={() => onChange("enhanced")}
      data-testid="mode-enhanced"
    >
      Enhanced
    </button>
  </div>
);

export default GenerationModeToggle;
