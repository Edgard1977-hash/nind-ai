const Logo = ({ className = "" }) => (
  <img
    src={`${process.env.PUBLIC_URL || ""}/logo.svg`}
    alt="nind"
    className={`nind-logo ${className}`.trim()}
  />
);

export default Logo;
